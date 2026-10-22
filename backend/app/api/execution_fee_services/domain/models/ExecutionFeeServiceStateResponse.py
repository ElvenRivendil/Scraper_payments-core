# /* ../NauTrader_Helm/payments-core/backend/app/api/execution_fee_services/domain/models/ExecutionFeeServiceStateResponse.py */
from pydantic import BaseModel


class ExecutionFeeServiceStateResponse(BaseModel):
    service_name: str
    enabled: bool
