import json
import os
import shutil
import time

import requests
from celery import Celery
from bs4 import BeautifulSoup
from loguru import logger

from config import PROFILES_PATH, TEMP_PATH, SSH_PATH, ALIASES_PATH, SERVERS_PATH
from helpers import start_driver, send_files_via_sftp
from start_session import BROWSER_FILE_PATH

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)

# Настройка Celery
celery = Celery(
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0'
)


@celery.task(name='tasks.update_cookies')
def update_cookies(profile_id):
    if not os.path.exists(PROFILES_PATH / profile_id):
        raise Exception(f'Profile {profile_id} does not exist')
    profile_path = os.path.join(PROFILES_PATH, profile_id, 'profile')
    cache_path = os.path.join(PROFILES_PATH, profile_id, 'cache')

    driver = start_driver(profile_path, cache_path, BROWSER_FILE_PATH)
    try:
        driver.maximize_window()
        n = 5
        for i in range(n):
            try:
                driver.get('https://www.avito.ru/analytics')
            except Exception as e:
                if n - 1 == i:
                    raise e
                logger.opt(exception=True).warning(e)
                time.sleep(10)
            else:
                break
        cookies = driver.get_cookies()
        current_url = driver.current_url
        if 'https://www.avito.ru/analytics' in current_url:
            status = "ok"
            html_code = driver.page_source
            soup = BeautifulSoup(html_code, "html.parser")
            element = soup.find("h2", class_="firewall-title")
            if element:
                status = "ip ban"
        else:
            status = "not authorized"
        return {"status": status, "cookies": cookies}
    finally:
        driver.close()
        driver.quit()


@celery.task(name='tasks.update_all_cookies')
def update_all_cookies():
    statuses = []
    # Загружаем алиасы профилей
    with open(ALIASES_PATH, 'r', encoding='utf-8') as f:
        aliases = json.loads(f.read())

    # Загружаем доступы к серверам
    with open(SERVERS_PATH, 'r', encoding='utf-8') as f:
        servers = json.loads(f.read())

    # Удаляем старую папку
    if TEMP_PATH.exists() and TEMP_PATH.is_dir():
        shutil.rmtree(TEMP_PATH)
    # Создаём новую папку
    TEMP_PATH.mkdir()

    # Получаем все cookies
    profiles = os.listdir(PROFILES_PATH)
    updated_cookies = []
    for profile in profiles:
        data = update_cookies(profile)
        cookies = data['cookies']
        statuses.append(data['status'])
        with open(TEMP_PATH / f'{profile}.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(cookies, ensure_ascii=False, indent=4))
        if data['status'] == 'ok':
            updated_cookies.append(f'{profile}.json')

    # Обновляем cookies на серверах
    # Центральный сервер
    for server in servers:
        if server.get('type') != 'central':
            continue
        files = []
        for file in os.listdir(TEMP_PATH):
            alias = aliases.get(file, file)
            files.append(
                [
                    str(TEMP_PATH / file),
                    f'/home/www/code/avito_analytics/accounts/{alias}'
                ]
            )
        files.append(
            [
                str(TEMP_PATH / '7.json'),
                '/home/www/code/avito_analytics/cookies/cookie.json'
            ]
        )
        send_files_via_sftp(server['ip'], server['user'], str(SSH_PATH / server['ssh_key']), files)

    # Потоки
    for server in servers:
        if server.get('type') != 'flow':
            continue

        files = []
        for file in os.listdir(TEMP_PATH):
            alias = aliases.get(file, file)
            files.append(
                [
                    str(TEMP_PATH / file),
                    f'/home/www/code/avito_analytics_flows/avito_analytics_flow1/accounts/{alias}'
                ]
            )
            files.append(
                [
                    str(TEMP_PATH / file),
                    f'/home/www/code/avito_analytics_flows/avito_analytics_flow2/accounts/{alias}'
                ]
            )
            files.append(
                [
                    str(TEMP_PATH / file),
                    f'/home/www/code/avito_analytics_flows/avito_analytics_flow3/accounts/{alias}'
                ]
            )
        files.append(
            [
                str(TEMP_PATH / '7.json'),
                '/home/www/code/avito_analytics_flows/avito_analytics_flow1/cookies/cookie.json'
            ]
        )
        files.append(
            [
                str(TEMP_PATH / '7.json'),
                '/home/www/code/avito_analytics_flows/avito_analytics_flow2/cookies/cookie.json'
            ]
        )
        files.append(
            [
                str(TEMP_PATH / '7.json'),
                '/home/www/code/avito_analytics_flows/avito_analytics_flow3/cookies/cookie.json'
            ]
        )

        send_files_via_sftp(server['ip'], server['user'], str(SSH_PATH / server['ssh_key']), files)

    for file in updated_cookies:
        alias = aliases.get(file, file)
        try:
            requests.post("https://analytics.qqrooza.ru/api/cookies-updated/", params={"file_name": alias})
        except Exception as e:
            logger.opt(exception=True).error(e)

    result = f"{statuses.count('ok')}/{len(statuses)}"
    if statuses.count('ok') < len(statuses):
        errors = []
        for i, status in enumerate(statuses):
            if status != 'ok':
                errors.append(f"{profiles[i]}: {status}")
        errors = ", ".join(errors)
        result = f'{result} (errors: {errors})'

    return result


@celery.task(name='tasks.update_cookies_with_update_file')
def update_cookies_with_update_file(file_name: str):
    # Загружаем алиасы профилей
    with open(ALIASES_PATH, 'r', encoding='utf-8') as f:
        aliases = json.loads(f.read())

    aliases = {value: key for key, value in aliases.items()}
    file: str = aliases.get(file_name)
    if file is None:
        raise Exception(f'File {file_name} not found')

    # Загружаем доступы к серверам
    with open(SERVERS_PATH, 'r', encoding='utf-8') as f:
        servers = json.loads(f.read())

    # Удаляем старую папку
    if TEMP_PATH.exists() and TEMP_PATH.is_dir():
        shutil.rmtree(TEMP_PATH)
    # Создаём новую папку
    TEMP_PATH.mkdir()

    profile_id = file.split('.')[0]
    data = update_cookies(profile_id)

    cookies = data['cookies']
    status = data['status']
    if status != 'ok':
        if status == 'not authorized':
            # :TODO: Отправить уведомление, что не удалось войти в аккаунт
            raise Exception("Authorization error")
        if status == 'ip ban':
            # :TODO: Отправить уведомление, что Ip адрес заблокирован
            raise Exception("IP ban")

    with open(TEMP_PATH / f'{profile_id}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(cookies, ensure_ascii=False, indent=4))

    for server in servers:
        if server.get('type') != 'central':
            continue
        files = [
            [
                str(TEMP_PATH / f'{profile_id}.json'),
                f'/home/www/code/avito_analytics/accounts/{file_name}'
            ]
        ]

        send_files_via_sftp(server['ip'], server['user'], str(SSH_PATH / server['ssh_key']), files)

    for server in servers:
        if server.get('type') != 'flow':
            continue
        files = [
            [
                str(TEMP_PATH / f'{profile_id}.json'),
                f'/home/www/code/avito_analytics_flows/avito_analytics_flow1/accounts/{file_name}'
            ],
            [
                str(TEMP_PATH / f'{profile_id}.json'),
                f'/home/www/code/avito_analytics_flows/avito_analytics_flow2/accounts/{file_name}'
            ],
            [
                str(TEMP_PATH / f'{profile_id}.json'),
                f'/home/www/code/avito_analytics_flows/avito_analytics_flow3/accounts/{file_name}'
            ]
        ]

        send_files_via_sftp(server['ip'], server['user'], str(SSH_PATH / server['ssh_key']), files)

    requests.post("https://analytics.qqrooza.ru/api/cookies-updated/", params={"file_name": file_name})

    return status
