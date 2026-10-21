# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemWalletsManagementConfigResponse.py */
from typing import Literal

from pydantic import BaseModel, Field


class SystemWalletsManagementTaskConfig(BaseModel):
    task_id: str
    task_name: str
    description: str
    operation: str
    schedule: str
    schedule_minute_utc: int
    enabled: bool
    currency_code: str
    source_wallet_codes: list[str]
    destination_wallet_codes: list[str]
    fee_status: Literal["not_configured"]
    fee: None = None


class SystemWalletsManagementConfigResponse(BaseModel):
    tasks: list[SystemWalletsManagementTaskConfig] = Field(default_factory=list)
