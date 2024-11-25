import json
import os
import shutil

from celery import Celery

from config import PROFILES_PATH, TEMP_PATH, SSH_PATH, ALIASES_PATH, SERVERS_PATH
from helpers import start_driver, send_files_via_sftp

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)

# Настройка Celery
celery = Celery(
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0'
)


@celery.task(name='tasks.update_cookies')
def update_cookies(profile_id):
    status = False
    if not os.path.exists(PROFILES_PATH / profile_id):
        raise Exception(f'Profile {profile_id} does not exist')
    profile_path = os.path.join(PROFILES_PATH, profile_id, 'profile')
    cache_path = os.path.join(PROFILES_PATH, profile_id, 'cache')

    driver = start_driver(profile_path, cache_path)
    try:
        driver.maximize_window()
        driver.get('https://www.avito.ru/analytics')
        cookies = driver.get_cookies()
        current_url = driver.current_url
        if 'https://www.avito.ru/analytics' in current_url:
            status = True
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
    for profile in profiles:
        data = update_cookies(profile)
        cookies = data['cookies']
        statuses.append(data['status'])
        with open(TEMP_PATH / f'{profile}.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(cookies, ensure_ascii=False, indent=4))

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

    result = f"{statuses.count(True)}/{len(statuses)}"
    if statuses.count(True) < len(statuses):
        errors = []
        for i, status in enumerate(statuses):
            if not status:
                errors.append(profiles[i])
        errors = ", ".join(errors)
        result = f'{result} (errors: {errors})'

    return result
