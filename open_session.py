import os

from helpers import start_driver, get_profile
from start_session import PROFILES_PATH, BROWSER_FILE_PATH


def main():
    profile = get_profile(PROFILES_PATH)
    profile_path = os.path.join(profile, 'profile')
    cache_path = os.path.join(profile, 'cache')

    driver = start_driver(profile_path, cache_path, BROWSER_FILE_PATH)
    try:
        input("Enter to close: ")
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':
    main()