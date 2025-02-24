import os
import shutil

from helpers import start_driver, get_profile
from start_session import PROFILES_PATH


def remove_extensions(profile_path):
    # Попытка удалить расширения из стандартного пути (для профиля по умолчанию)
    ext_path = os.path.join(profile_path, "Default", "Extensions")
    if os.path.exists(ext_path):
        shutil.rmtree(ext_path)
        print("Папка с расширениями удалена:", ext_path)
    else:
        # Если такой папки нет, пробуем искать ее в корне профиля
        ext_path = os.path.join(profile_path, "Extensions")
        if os.path.exists(ext_path):
            shutil.rmtree(ext_path)
            print("Папка с расширениями удалена:", ext_path)
        else:
            print("Папка с расширениями не найдена")


def main():
    # Получаем путь к профилю и кэшу (определите get_profile и PROFILES_PATH согласно вашему коду)
    profile = get_profile(PROFILES_PATH)
    profile_path = os.path.join(profile, 'profile')
    cache_path = os.path.join(profile, 'cache')

    # Удаляем расширения из старого профиля
    remove_extensions(profile_path)

    driver = start_driver(profile_path, cache_path)
    try:
        try:
            driver.maximize_window()
        except Exception as e:
            print("Не удалось максимизировать окно")
            print(e)
        driver.get('https://www.avito.ru')
        input("Enter to close: ")
    finally:
        try:
            driver.close()
        except Exception as e:
            print('При закрытии окна произошла ошибка')
            print(e)
        driver.quit()


if __name__ == '__main__':
    main()
