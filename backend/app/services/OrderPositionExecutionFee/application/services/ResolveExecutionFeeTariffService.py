# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/ResolveExecutionFeeTariffService.py */
from typing import Literal
from uuid import UUID

from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.core.config import get_settings
from app.services.OrderPositionExecutionFee.application.operations.ResolveExecutionFeeTariffOperation import (
    ResolveExecutionFeeTariffOperation,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeTariff import (
    ExecutionFeeTariff,
)


class ResolveExecutionFeeTariffService:
    @classmethod
    def resolve(
        cls,
        *,
        user_id: UUID,
        mode: Literal["paper", "live", "mock", "backtests"],
        tariff_type: Literal["orders", "positions"],
    ) -> ExecutionFeeTariff:
        settings = get_settings()
        client = HelmApiClient(base_url=settings.helm_auth_base_url)
        return ResolveExecutionFeeTariffOperation.execute(
            client,
            user_id=user_id,
            mode=mode,
            tariff_type=tariff_type,
            internal_secret=settings.helm_internal_api_secret,
        )
