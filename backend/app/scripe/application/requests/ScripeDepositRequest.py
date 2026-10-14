# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/requests/ScripeDepositRequest.py */
from pydantic import BaseModel, Field


class ScripeDepositRequest(BaseModel):
    amount_minor: int = Field(gt=0)
