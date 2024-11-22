import os

from celery import Celery

from config import PROFILES_PATH
from helpers import start_driver

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

    driver = start_driver(profile_path, cache_path)
    try:
        driver.maximize_window()
        driver.get('https://www.avito.ru/analytics')
        cookies = driver.get_cookies()
        return cookies
    finally:
        driver.close()
        driver.quit()
