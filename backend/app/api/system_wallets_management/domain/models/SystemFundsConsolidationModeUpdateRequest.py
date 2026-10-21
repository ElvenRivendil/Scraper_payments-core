# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemFundsConsolidationModeUpdateRequest.py */
from pydantic import BaseModel, ConfigDict
from app.services.SystemFundsConsolidation.domain.value_objects.SystemFundsConsolidationMode import (
    SystemFundsConsolidationMode,
)


class SystemFundsConsolidationModeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: SystemFundsConsolidationMode
