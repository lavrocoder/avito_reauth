import json
import os
from pathlib import Path

from helpers import start_driver

BASE_DIR = Path(__file__).resolve().parent

PROFILES_PATH = BASE_DIR / 'profiles'

PROFILES_PATH.mkdir(exist_ok=True)


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

    driver = start_driver(profile_path, cache_path)
    try:
        driver.maximize_window()
        driver.get('https://www.avito.ru')
        input("Enter to close: ")
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':
    main()
