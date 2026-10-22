# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/application/services/ResolveExecutionFeeBandsService.py */

from uuid import UUID

from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.core.config import get_settings
from app.services.ParameterizedExecutionFee.application.operations.ResolveExecutionFeeBandsOperation import (
    ResolveExecutionFeeBandsOperation,
)
from app.services.ParameterizedExecutionFee.domain.models.ExecutionFeeBand import (
    ExecutionFeeBand,
)


class ResolveExecutionFeeBandsService:
    @classmethod
    def resolve(
        cls,
        *,
        user_id: UUID,
        mode: str,
        tariff_entity_key: str,
        percentage_key: str = "profit_percent",
    ) -> tuple[ExecutionFeeBand, ...]:
        settings = get_settings()
        client = HelmApiClient(base_url=settings.helm_auth_base_url)
        return ResolveExecutionFeeBandsOperation.execute(
            client,
            user_id=user_id,
            mode=mode,
            internal_secret=settings.helm_internal_api_secret,
            tariff_entity_key=tariff_entity_key,
            percentage_key=percentage_key,
        )
