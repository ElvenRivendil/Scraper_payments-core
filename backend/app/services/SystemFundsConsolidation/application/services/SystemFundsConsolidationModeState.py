# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/services/SystemFundsConsolidationModeState.py */
from redis import Redis

from app.core.config import get_settings
from app.services.SystemFundsConsolidation.domain.value_objects.SystemFundsConsolidationMode import (
    SystemFundsConsolidationMode,
)


class SystemFundsConsolidationModeState:
    KEY = "payments_core:system_funds_consolidation:execution_mode"
    DEFAULT_MODE = SystemFundsConsolidationMode.MANY_TO_ONE

    def __init__(self) -> None:
        self.redis = Redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )

    def get_mode(self) -> SystemFundsConsolidationMode:
        stored_mode = self.redis.get(self.KEY)
        if stored_mode is None:
            return self.DEFAULT_MODE
        return SystemFundsConsolidationMode.parse(stored_mode)

    def update_mode(
        self,
        mode: str | SystemFundsConsolidationMode,
    ) -> SystemFundsConsolidationMode:
        selected_mode = SystemFundsConsolidationMode.parse(mode)
        self.redis.set(self.KEY, selected_mode.value)
        return selected_mode
