import json
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = Path(__file__).resolve().parent

PROFILES_PATH = BASE_DIR / 'profiles'


def load_cookies(path: str) -> list[dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def get_profile(path: Path) -> str:
    dirs = os.listdir(path)
    dirs_txt = "\n".join(dirs)
    print(f"Выбери профиль или создайте новый: \n{dirs_txt}")
    select_dir = input(">>> ")
    if select_dir not in dirs:
        os.mkdir(os.path.join(path, select_dir))
    return os.path.join(path, select_dir)


def main():
    profile = get_profile(PROFILES_PATH)
    profile_path = os.path.join(profile, 'profile')
    cache_path = os.path.join(profile, 'cache')

    options = Options()
    options.add_argument(f"user-data-dir={profile_path}")
    options.add_argument("disk-cache-size=104857600")
    options.add_argument("media-cache-size=104857600")
    options.add_argument(f"--disk-cache-dir={cache_path}")
    options.add_argument("--disk-cache-size=104857600")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.maximize_window()
        driver.get('https://www.avito.ru/analytics')
        sessid = driver.get_cookie("sessid")
        print(f"{sessid=}")
        ft = driver.get_cookie("ft")
        print(f"{ft=}")
        auth = driver.get_cookie("auth")
        print(f"{auth=}")
        input("Enter to close: ")
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':
    main()
