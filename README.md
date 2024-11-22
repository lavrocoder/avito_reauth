```shell
docker-compose up -d --build
```

```shell 
celery -A tasks worker --loglevel=info --pool=solo
```