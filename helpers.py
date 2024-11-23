import pysftp
from loguru import logger
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


def send_files_via_sftp(ip: str, username: str, private_key_path: str, files: list[list[str]]) -> list[bool]:
    """
    Отправляет файлы на сервер по sftp.
    :param ip: IP адрес сервера, куда отправить файлы.
    :param username: Имя пользователя на сервере через которого нужно зайти.
    :param private_key_path: Путь к приватному ключу.
    :param files: Список, в котором каждый элемент - это список из 2-х полных путей:
                    1 - локальный путь к файлу;
                    2 - путь к файлу на сервере.
    :return: Список результатов отправки для каждого файла
    """
    results = []
    with pysftp.Connection(ip, username=username, private_key=private_key_path) as sftp:
        logger.debug(f'Connected to SFTP server: {ip}')
        for file in files:
            logger.debug(f'Sending file: {file}')
            try:
                sftp.put(file[0], file[1])
                logger.debug(f'File sent: {file[0]}')
                results.append(True)
            except Exception as e:
                logger.error(f'Failed to send file: {file[0]}')
                logger.opt(exception=True).error(e)
                results.append(False)
    logger.debug(f'{results=}')
    return results