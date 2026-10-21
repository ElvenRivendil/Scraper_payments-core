# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/domain/models/OrderPositionExecutionFeesStateResponse.py */
from pydantic import BaseModel


class OrderPositionExecutionFeesStateResponse(BaseModel):
    service_name: str
    enabled: bool
