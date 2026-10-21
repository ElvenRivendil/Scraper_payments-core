# /* ../NauTrader_Helm/payments-core/backend/app/workers/SystemWalletsManagementScheduler.py */
from __future__ import annotations

import logging
from typing import Any

from celery.beat import Scheduler
from celery.schedules import crontab
from redis import Redis

from app.core.config import get_settings
from app.core.scheduling.SystemWalletsManagementTaskRegistry import (
    SystemWalletsManagementTaskRegistry,
)

logger = logging.getLogger(__name__)


class SystemWalletsManagementScheduler(Scheduler):
    TASK_DEFAULTS = SystemWalletsManagementTaskRegistry.TASK_DEFAULTS
    STATE_KEY_PREFIX = SystemWalletsManagementTaskRegistry.STATE_KEY_PREFIX

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.state_redis = Redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )
        super().__init__(*args, **kwargs)

    def setup_schedule(self) -> None:
        super().setup_schedule()
        self._refresh_managed_entries()

    def tick(self, *args: Any, **kwargs: Any) -> float:
        self._refresh_managed_entries()
        return super().tick(*args, **kwargs)

    def _refresh_managed_entries(self) -> None:
        for task_id, defaults in SystemWalletsManagementTaskRegistry.TASK_DEFAULTS.items():
            try:
                state = self.state_redis.hgetall(
                    f"{SystemWalletsManagementTaskRegistry.STATE_KEY_PREFIX}:{task_id}"
                )
                enabled = state.get(
                    "enabled", str(defaults.get("enabled", True)).lower()
                ).lower() == "true"
                minute = int(state.get("schedule_minute_utc", defaults["minute"]))
                if not 0 <= minute <= 59:
                    raise ValueError(f"Invalid schedule minute for {task_id}")
            except Exception:
                logger.exception(
                    "Unable to refresh scheduled task state for %s",
                    task_id,
                )
                continue

            schedule_name = defaults["schedule_name"]
            current_entry = self.schedule.get(schedule_name)

            if not enabled:
                if current_entry is not None:
                    self.schedule.pop(schedule_name, None)
                    logger.info("Disabled scheduled task %s", task_id)
                continue

            current_minute = None
            if current_entry is not None:
                current_minute = getattr(
                    current_entry.schedule,
                    "_orig_minute",
                    None,
                )
                if str(current_minute) == str(minute):
                    continue

            self.schedule[schedule_name] = self.Entry(
                name=schedule_name,
                task=defaults["task_name"],
                schedule=crontab(minute=minute),
                args=(),
                kwargs={},
                options={},
                last_run_at=self.app.now(),
                total_run_count=(
                    current_entry.total_run_count
                    if current_entry is not None
                    else 0
                ),
                app=self.app,
            )
            logger.info(
                "Updated scheduled task %s to minute %02d UTC",
                task_id,
                minute,
            )
