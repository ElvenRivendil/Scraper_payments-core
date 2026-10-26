# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/models/ExecutionFeePreparation.py */
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID

from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)


@dataclass(frozen=True, slots=True)
class ExecutionFeePreparation:
    user_id: UUID
    event_id: str
    mode: Literal["paper", "live", "mock", "backtests"]
    fee_type: Literal["order", "position_opening", "position_closing"]
    tariff_type: Literal["orders", "positions"]
    volume_usdt: Decimal
    amount_minor: int
    tariff_enabled: bool
    is_protective_order: bool
    scenario: ExecutionFeeScenario
