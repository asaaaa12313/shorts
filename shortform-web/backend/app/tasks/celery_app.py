from celery import Celery
from app.core.config import REDIS_URL

celery_app = Celery(
    "shortform",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.video_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    worker_concurrency=2,
    task_time_limit=600,  # 10분 타임아웃
)
