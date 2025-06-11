from celery import Celery
import os
from app.core.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "worker", broker=settings.BROKER_URL, backend=settings.RESULT_BACKEND
)

default_config = "app.celeryconfig"

celery_app.config_from_object(default_config)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    enable_utc=True,
    timezone="UTC",
)


# # Add periodic task schedule
# celery_app.conf.beat_schedule = {
#     "check-temperature-every-3-minutes": {
#         "task": "check_temperature_task",
#         "schedule": crontab(minute="*/3"),  # Run every 3 minutes
#     },
# }
