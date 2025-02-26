import json
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

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

static_folder = "cookies"
profiles_folder = "profiles"
app.mount("/cookies", StaticFiles(directory="cookies"), name="cookies")
app.mount("/profiles", StaticFiles(directory="profiles"), name="profiles")


@app.get("/cookies")
async def list_cookies():
    try:
        # Получаем список файлов в папке
        files = os.listdir(static_folder)
        # Фильтруем только файлы (исключаем папки)
        files = [f for f in files if os.path.isfile(os.path.join(static_folder, f))]
        return JSONResponse(content={"files": files})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/working_cookies")
async def working_cookies():
    try:
        data = []
        dirs = [d for d in os.listdir(profiles_folder) if os.path.isdir(os.path.join(profiles_folder, d))]
        for folder in dirs:
            cookies_path = os.path.join(profiles_folder, folder, 'cookies.json')
            if os.path.exists(cookies_path):
                with open(cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                data.append({folder: cookies})
        return JSONResponse(content={"cookies": data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/update-cookies/all")
def update_cookies():
    task = celery.send_task('tasks.update_all_cookies')
    return {"task_id": task.id, "status": "ok"}


@app.post("/update-cookies/{profile_id}")
def update_cookies(profile_id: str):
    task = celery.send_task('tasks.update_cookies', args=[profile_id])
    return {"task_id": task.id, "status": "ok"}


@app.post("/update-cookies-by-file-name/{file_name}")
def update_cookies(file_name: str):
    task = celery.send_task('tasks.update_cookies_with_update_file', args=[file_name])
    return {"task_id": task.id, "status": "ok"}


@app.post("/send-cookies/{profile_id}")
def send_cookies(profile_id: str, data: dict):
    profile_path = COOKIES_PATH / f"{profile_id}.json"
    with open(profile_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data['data'], indent=4, ensure_ascii=False))
    return {"status": "ok"}
