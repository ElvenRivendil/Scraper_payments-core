# /* ../NauTrader_Helm/payments-core/backend/app/features/transfers/domain/models/TransferResult.py */
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class TransferResult(BaseModel):
    mode: str
    amount_minor: int
    fee_minor: int
    fee_percentage: Decimal
    currency_code: str
    execution_at: datetime
    discounts_status: str
    transfers: list[dict[str, Any]]
