```shell
docker-compose up -d --build
```

```shell 
celery -A tasks worker --loglevel=info --pool=solo
```

# Server Commands

```shell
redis-server
```

```shell
uvicorn api:app --host 0.0.0.0 --port 8000
```

```shell
celery -A tasks flower
```

```shell
ceelery -A tasks worker --loglevel=info --pool=solo
```