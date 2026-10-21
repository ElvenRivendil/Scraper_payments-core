# /* ../NauTrader_Helm/payments-core/backend/app/workers/celery_app.py */
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "payments_core",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    enable_utc=True,
    timezone="UTC",
    beat_scheduler="app.workers.SystemWalletsManagementScheduler:SystemWalletsManagementScheduler",
    beat_schedule={
        "user-funds-collection-hourly-probe": {
            "task": "payments_core.user_funds_collection_schedule_probe",
            "schedule": crontab(minute=5),
        },
        "system-funds-consolidation-hourly": {
            "task": "payments_core.system_funds_consolidation_hourly",
            "schedule": crontab(minute=15),
        },
    },
)
