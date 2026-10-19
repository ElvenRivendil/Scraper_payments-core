# /* ../NauTrader_Helm/payments-core/backend/app/api/helm/domain/models/HelmTariffResponse.py */
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HelmTariffResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: UUID
    profile_exists: bool
    profile: dict[str, Any]
    tariffs: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
