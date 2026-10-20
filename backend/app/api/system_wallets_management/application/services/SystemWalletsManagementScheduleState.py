# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/application/services/SystemWalletsManagementScheduleState.py */
from redis import Redis

from app.core.config import get_settings
from app.core.scheduling.SystemWalletsManagementTaskRegistry import (
    SystemWalletsManagementTaskRegistry,
)


class SystemWalletsManagementScheduleState:
    KEY_PREFIX = SystemWalletsManagementTaskRegistry.STATE_KEY_PREFIX
    TASK_DEFAULTS = SystemWalletsManagementTaskRegistry.TASK_DEFAULTS

    def __init__(self) -> None:
        self.redis = Redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )

    def get_state(self, task_id: str) -> dict[str, bool | int]:
        defaults = self.TASK_DEFAULTS[task_id]
        stored = self.redis.hgetall(f"{self.KEY_PREFIX}:{task_id}")
        return {
            "enabled": stored.get("enabled", "true").lower() == "true",
            "schedule_minute_utc": int(
                stored.get("schedule_minute_utc", defaults["minute"])
            ),
        }

    def update_state(
        self,
        task_id: str,
        *,
        enabled: bool | None = None,
        schedule_minute_utc: int | None = None,
    ) -> dict[str, bool | int]:
        current = self.get_state(task_id)
        if enabled is not None:
            current["enabled"] = enabled
        if schedule_minute_utc is not None:
            current["schedule_minute_utc"] = schedule_minute_utc
        self.redis.hset(
            f"{self.KEY_PREFIX}:{task_id}",
            mapping={
                "enabled": str(current["enabled"]).lower(),
                "schedule_minute_utc": str(current["schedule_minute_utc"]),
            },
        )
        return current
