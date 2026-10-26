# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/api/InternalOrderPositionExecutionFeesRoutes.py */
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.order_position_execution_fees.domain.models.InternalOrderPositionExecutionFeeRequest import (
    InternalOrderPositionExecutionFeeRequest,
)
from app.api.profitable_closed_trade_execution_fees.api.InternalProfitableClosedTradeExecutionFeesRoutes import (
    require_internal_secret,
)
from app.core.db import get_db
from app.services.OrderPositionExecutionFee.application.services.ExecuteOrderPositionExecutionFeeService import (
    ExecuteOrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.application.services.PrepareOrderPositionExecutionFeeService import (
    PrepareOrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.application.services.ConfirmOrderPositionExecutionFeeService import (
    ConfirmOrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.domain.scenarios.OrderPositionExecutionFeeScenarios import (
    OrderPositionExecutionFeeScenarios,
)


class InternalOrderPositionExecutionFeesRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/internal/order-position-execution-fees",
            tags=["internal-order-position-execution-fees"],
            dependencies=[Depends(require_internal_secret)],
        )
        self.router.add_api_route(
            "/run",
            self.run,
            methods=["POST"],
            name="run_internal_order_position_execution_fee",
        )
        self.router.add_api_route(
            "/prepare",
            self.prepare,
            methods=["POST"],
            name="prepare_internal_order_position_execution_fee",
        )
        self.router.add_api_route(
            "/confirm",
            self.confirm,
            methods=["POST"],
            name="confirm_internal_order_position_execution_fee",
        )

    @staticmethod
    def prepare(
        payload: InternalOrderPositionExecutionFeeRequest,
    ) -> dict[str, object]:
        if payload.fee_type == "order":
            tariff_type = "orders"
            scenario = OrderPositionExecutionFeeScenarios.order()
        elif payload.fee_type == "position_opening":
            tariff_type = "positions"
            scenario = OrderPositionExecutionFeeScenarios.position_opening()
        elif payload.fee_type == "position_closing":
            tariff_type = "positions"
            scenario = OrderPositionExecutionFeeScenarios.position_closing()
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported execution fee type",
            )

        try:
            result = PrepareOrderPositionExecutionFeeService.prepare(
                user_id=payload.user_id,
                event_id=payload.event_id,
                mode=payload.mode,
                fee_type=payload.fee_type,
                tariff_type=tariff_type,
                scenario=scenario,
                volume_usdt=payload.volume_usdt,
                is_protective_order=payload.is_protective_order,
            )
        except (ValueError, LookupError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Execution fee prepare failed: user_id=%s event_id=%s mode=%s fee_type=%s tariff_type=%s",
                payload.user_id,
                payload.event_id,
                payload.mode,
                payload.fee_type,
                tariff_type,
            )
            raise

        return {
            "status": result.status,
            "created": result.created,
            "amount_minor": result.amount_minor,
            "event_id": payload.event_id,
            "fee_type": payload.fee_type,
            "volume_usdt": str(payload.volume_usdt),
        }

    @staticmethod
    def confirm(
        payload: InternalOrderPositionExecutionFeeRequest,
        session: Session = Depends(get_db),
    ) -> dict[str, object]:
        try:
            result = ConfirmOrderPositionExecutionFeeService.confirm(
                session,
                user_id=payload.user_id,
                event_id=payload.event_id,
                mode=payload.mode,
                fee_type=payload.fee_type,
                is_protective_order=payload.is_protective_order,
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
            "event_id": payload.event_id,
            "fee_type": payload.fee_type,
            "volume_usdt": str(payload.volume_usdt),
        }

    @staticmethod
    def run(
        payload: InternalOrderPositionExecutionFeeRequest,
        session: Session = Depends(get_db),
    ) -> dict[str, object]:
        if payload.fee_type == "order":
            tariff_type = "orders"
            scenario = OrderPositionExecutionFeeScenarios.order()
        elif payload.fee_type == "position_opening":
            tariff_type = "positions"
            scenario = OrderPositionExecutionFeeScenarios.position_opening()
        elif payload.fee_type == "position_closing":
            tariff_type = "positions"
            scenario = OrderPositionExecutionFeeScenarios.position_closing()
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported execution fee type",
            )

        try:
            result = ExecuteOrderPositionExecutionFeeService.execute(
                session,
                user_id=payload.user_id,
                event_id=payload.event_id,
                mode=payload.mode,
                tariff_type=tariff_type,
                scenario=scenario,
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
            "event_id": payload.event_id,
            "fee_type": payload.fee_type,
            "volume_usdt": str(payload.volume_usdt),
        }
