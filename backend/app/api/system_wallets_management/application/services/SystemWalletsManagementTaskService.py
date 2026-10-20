# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/application/services/SystemWalletsManagementTaskService.py */
from __future__ import annotations

from typing import Any

from app.api.system_wallets_management.application.services.SystemWalletsManagementScheduleState import (
    SystemWalletsManagementScheduleState,
)
from app.core.scheduling.SystemWalletsManagementTaskRegistry import (
    SystemWalletsManagementTaskRegistry,
)
from app.workers.celery_app import celery_app


class SystemWalletsManagementTaskService:
    def __init__(self) -> None:
        self.schedule_state = SystemWalletsManagementScheduleState()

    @staticmethod
    def _get_defaults(task_id: str) -> dict[str, Any]:
        defaults = SystemWalletsManagementTaskRegistry.TASK_DEFAULTS.get(task_id)
        if defaults is None:
            raise KeyError(task_id)
        return defaults

    def get_state(self, task_id: str) -> dict[str, Any]:
        defaults = self._get_defaults(task_id)
        return {
            "task_id": task_id,
            "task_name": defaults["task_name"],
            **self.schedule_state.get_state(task_id),
        }

    def update_state(
        self,
        task_id: str,
        *,
        enabled: bool | None,
        schedule_minute_utc: int | None,
    ) -> dict[str, Any]:
        self._get_defaults(task_id)
        if enabled is None and schedule_minute_utc is None:
            raise ValueError("At least one task setting must be provided")
        self.schedule_state.update_state(
            task_id,
            enabled=enabled,
            schedule_minute_utc=schedule_minute_utc,
        )
        return self.get_state(task_id)

    def queue_task(self, task_id: str) -> dict[str, Any]:
        defaults = self._get_defaults(task_id)
        state = self.get_state(task_id)
        result = celery_app.send_task(defaults["task_name"])
        return {
            **state,
            "status": "queued",
            "message": "Task was queued for execution",
            "celery_task_id": result.id,
        }
