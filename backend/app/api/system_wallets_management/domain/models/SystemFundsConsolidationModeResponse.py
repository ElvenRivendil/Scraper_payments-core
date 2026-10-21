# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemFundsConsolidationModeResponse.py */
from pydantic import BaseModel
from app.services.SystemFundsConsolidation.domain.value_objects.SystemFundsConsolidationMode import (
    SystemFundsConsolidationMode,
)


class SystemFundsConsolidationModeResponse(BaseModel):
    mode: SystemFundsConsolidationMode
    available_modes: list[SystemFundsConsolidationMode]
