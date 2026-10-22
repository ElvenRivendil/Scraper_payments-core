# /* ../NauTrader_Helm/payments-core/backend/app/api/position_percent_value_execution_fees/application/services/RunPositionPercentValueExecutionFeeManualService.py */
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.PositionPercentValueExecutionFees.application.services.PositionPercentValueExecutionFeesService import (
    PositionPercentValueExecutionFeesService,
)


class RunPositionPercentValueExecutionFeeManualService:
    @classmethod
    def execute(
        cls,
        session: Session,
        user_id: UUID,
        event_id: str,
        mode: str,
        volume: Decimal,
    ) -> object:
        return PositionPercentValueExecutionFeesService.execute(
            session,
            user_id=user_id,
            event_id=event_id,
            mode=mode,
            volume=volume,
        )
