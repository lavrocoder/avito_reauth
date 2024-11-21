from fastapi import FastAPI

# from celery import Celery

app = FastAPI()


# Настройка Celery
# celery = Celery(
#     broker='redis://localhost:6379/0',
#     backend='redis://localhost:6379/0'
# )

@app.post("/update-cookies/")
def update_cookies(task_data: dict):
    # task = celery.send_task('tasks.update_cookies', args=[task_data])
    return {"status": "Task submitted"}
