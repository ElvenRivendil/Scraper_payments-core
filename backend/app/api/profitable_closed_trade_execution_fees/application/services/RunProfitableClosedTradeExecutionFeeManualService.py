# /* ../NauTrader_Helm/payments-core/backend/app/api/profitable_closed_trade_execution_fees/application/services/RunProfitableClosedTradeExecutionFeeManualService.py */
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.ProfitableClosedTradeExecutionFees.application.services.ProfitableClosedTradeExecutionFeesService import (
    ProfitableClosedTradeExecutionFeesService,
)


class RunProfitableClosedTradeExecutionFeeManualService:
    @classmethod
    def execute(
        cls,
        session: Session,
        user_id: UUID,
        event_id: str,
        mode: str,
        profit_usdt: Decimal,
        conversion_rate: Decimal = Decimal("1"),
    ) -> object:
        return ProfitableClosedTradeExecutionFeesService.execute(
            session,
            user_id=user_id,
            event_id=event_id,
            mode=mode,
            profit_usdt=profit_usdt,
            conversion_rate=conversion_rate,
        )
