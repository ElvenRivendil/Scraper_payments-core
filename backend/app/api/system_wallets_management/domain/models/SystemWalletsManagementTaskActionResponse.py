# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemWalletsManagementTaskActionResponse.py */
from typing import Literal

from pydantic import BaseModel


class SystemWalletsManagementTaskActionResponse(BaseModel):
    task_id: str
    status: Literal["updated", "queued"]
    enabled: bool
    schedule_minute_utc: int
    message: str
    celery_task_id: str | None = None
