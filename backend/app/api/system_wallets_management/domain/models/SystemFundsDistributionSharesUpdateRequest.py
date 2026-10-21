# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/domain/models/SystemFundsDistributionSharesUpdateRequest.py */
from pydantic import BaseModel, ConfigDict, Field, StrictInt


class SystemFundsDistributionSharesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spap_percentage: StrictInt = Field(ge=0, le=100)
    wrap_percentage: StrictInt = Field(ge=0, le=100)
