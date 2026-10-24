# /* ../NauTrader_Helm/payments-core/backend/app/api/profitable_closed_trade_execution_fees/api/InternalProfitableClosedTradeExecutionFeesRoutes.py */
import secrets
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.services.ProfitableClosedTradeExecutionFees.application.services.ProfitableClosedTradeExecutionFeesService import (
    ProfitableClosedTradeExecutionFeesService,
)


class InternalProfitableClosedTradeExecutionFeeRequest(BaseModel):
    user_id: UUID
    event_id: str = Field(min_length=1, max_length=256)
    mode: Literal["paper", "live", "mock", "backtests"]
    profit_usdt: Decimal = Field(ge=0, max_digits=18, decimal_places=6)
    conversion_rate: Decimal = Field(default=Decimal("1"), gt=0, max_digits=18, decimal_places=8)


def require_internal_secret(
    supplied_secret: Annotated[
        str | None,
        Header(alias="X-Helm-Internal-Secret"),
    ] = None,
) -> None:
    expected_secret = get_settings().helm_internal_api_secret
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API secret is not configured",
        )
    if not supplied_secret or not secrets.compare_digest(
        supplied_secret,
        expected_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal credentials",
        )


class InternalProfitableClosedTradeExecutionFeesRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/internal/profitable-closed-trade-execution-fees",
            tags=["internal-profitable-closed-trade-execution-fees"],
            dependencies=[Depends(require_internal_secret)],
        )
        self.router.add_api_route(
            "/run",
            self.run,
            methods=["POST"],
            name="run_internal_profitable_closed_trade_execution_fee",
        )

    @staticmethod
    def run(
        payload: InternalProfitableClosedTradeExecutionFeeRequest,
        session: Session = Depends(get_db),
    ) -> dict[str, object]:
        try:
            result = ProfitableClosedTradeExecutionFeesService.execute(
                session,
                user_id=payload.user_id,
                event_id=payload.event_id,
                mode=payload.mode,
                profit_usdt=payload.profit_usdt,
                conversion_rate=payload.conversion_rate,
            )
            session.commit()
        except (ValueError, LookupError) as exc:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        except Exception:
            session.rollback()
            raise

        return {
            "status": result.status,
            "created": result.created,
            "amount_minor": result.amount_minor,
            "band_key": result.band_key,
            "percent": str(result.percent),
            "event_id": payload.event_id,
            "profit_usdt": str(payload.profit_usdt),
            "conversion_rate": str(payload.conversion_rate),
        }
