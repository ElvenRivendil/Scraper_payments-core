# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemWalletsManagementTaskUpdateRequest.py */
from pydantic import BaseModel, ConfigDict, Field


class SystemWalletsManagementTaskUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool | None = None
    schedule_minute_utc: int | None = Field(default=None, ge=0, le=59)
