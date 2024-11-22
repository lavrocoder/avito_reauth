from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def start_driver(profile_path, cache_path):
    options = Options()
    options.add_argument(f"user-data-dir={profile_path}")
    options.add_argument("disk-cache-size=104857600")
    options.add_argument("media-cache-size=104857600")
    options.add_argument(f"--disk-cache-dir={cache_path}")
    options.add_argument("--disk-cache-size=104857600")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument("--disable-webgl")  # Отключить WebGL
    options.add_argument("--log-level=3")  # Уровень логирования (0=ALL, 1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR, 5=FATAL)
    options.add_argument("--ignore-certificate-errors")  # Игнорировать ошибки SSL
    options.add_argument("--disable-logging")  # Отключить логи
    # Отключение лишних логов
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-blink-features"])

    driver = webdriver.Chrome(options=options)
    return driver
