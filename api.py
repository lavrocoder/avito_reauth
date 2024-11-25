import json
import os

from fastapi import FastAPI, Request, HTTPException

from celery import Celery

from config import COOKIES_PATH

COOKIES_PATH.mkdir(exist_ok=True)

app = FastAPI()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)

# Настройка Celery
celery = Celery(
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0'
)

# ALLOWED_IPS = {"127.0.0.1", "192.168.0.1"}  # Разрешённые IP-адреса
#
#
# @app.middleware("http")
# async def check_ip_middleware(request: Request, call_next):
#     client_ip = request.client.host
#     if client_ip not in ALLOWED_IPS:
#         raise HTTPException(status_code=403, detail="Access forbidden: Your IP is not allowed")
#     response = await call_next(request)
#     return response


@app.post("/update-cookies/all")
def update_cookies():
    task = celery.send_task('tasks.update_all_cookies')
    return {"task_id": task.id, "status": "ok"}


@app.post("/update-cookies/{profile_id}")
def update_cookies(profile_id: str):
    task = celery.send_task('tasks.update_cookies', args=[profile_id])
    return {"task_id": task.id, "status": "ok"}


@app.post("/send-cookies/{profile_id}")
def send_cookies(profile_id: str, data: dict):
    profile_path = COOKIES_PATH / f"{profile_id}.json"
    with open(profile_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data['data'], indent=4, ensure_ascii=False))
    return {"status": "ok"}
