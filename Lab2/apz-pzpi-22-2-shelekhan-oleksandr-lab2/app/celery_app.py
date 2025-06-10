# app/celery_app.py
from celery import Celery
import os
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND
)

default_config = 'app.celeryconfig'

celery_app.config_from_object(default_config)

celery_app.conf.update(task_track_started=True, task_serializer="json")

# celery_app.autodiscover_tasks(['app.email_utils'])