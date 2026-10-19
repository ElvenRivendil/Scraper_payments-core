# /* ../NauTrader_Helm/payments-core/backend/app/api/helm/application/services/HelmTariffService.py */
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.api.helm.domain.models.HelmTariffResponse import HelmTariffResponse
from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient


class HelmTariffService:
    def __init__(self, client: HelmApiClient) -> None:
        self.client = client

    def get_user_tariffs(self, authorization: str) -> HelmTariffResponse:
        payload = self.client.get_user_tariffs(authorization)
        try:
            return HelmTariffResponse.model_validate(payload)
        except ValidationError:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=502,
                detail="Invalid tariff response from Helm",
            ) from None

    def get_user_tariff_entity(
        self,
        authorization: str,
        entity_key: str,
    ) -> dict[str, Any]:
        return self.client.get_user_tariff_entity(authorization, entity_key)
