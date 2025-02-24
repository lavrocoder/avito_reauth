import os
from pathlib import Path

from helpers import start_driver, get_profile

BASE_DIR = Path(__file__).resolve().parent

PROFILES_PATH = BASE_DIR / 'profiles'

PROFILES_PATH.mkdir(exist_ok=True)

BROWSER_PATH = BASE_DIR / 'browser'

BROWSER_PATH.mkdir(exist_ok=True)

BROWSER_FILE_PATH = BROWSER_PATH / 'chrome-win64' / 'chrome.exe'


def main():
    profile = get_profile(PROFILES_PATH)
    profile_path = os.path.join(profile, 'profile')
    cache_path = os.path.join(profile, 'cache')

    driver = start_driver(profile_path, cache_path, BROWSER_FILE_PATH)
    try:
        driver.maximize_window()
        driver.get('https://www.avito.ru')
        input("Enter to close: ")
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':
    main()
