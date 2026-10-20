# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemWalletsManagementTaskStateResponse.py */
from pydantic import BaseModel


class SystemWalletsManagementTaskStateResponse(BaseModel):
    task_id: str
    task_name: str
    enabled: bool
    schedule_minute_utc: int
