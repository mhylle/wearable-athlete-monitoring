"""Celery application factory."""

from celery import Celery

from app.config import settings
from app.tasks.schedule import get_beat_schedule

celery_app = Celery(
    "wearable",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule=get_beat_schedule(),
)

# Auto-discover tasks from app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])
