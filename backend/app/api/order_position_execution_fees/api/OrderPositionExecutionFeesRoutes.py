# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/api/OrderPositionExecutionFeesRoutes.py */
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.order_position_execution_fees.application.services.OrderPositionExecutionFeesControlService import (
    OrderPositionExecutionFeesControlService,
)
from app.api.order_position_execution_fees.domain.models.OrderPositionExecutionFeesRunRequest import (
    OrderPositionExecutionFeesRunRequest,
)
from app.api.order_position_execution_fees.domain.models.OrderPositionExecutionFeesStateResponse import (
    OrderPositionExecutionFeesStateResponse,
)
from app.core.auth import AuthenticatedUser, require_current_user
from app.core.authorization.SystemWalletAccessPolicy import SystemWalletAccessPolicy
from app.core.db import get_db
from app.core.execution_logging.ServiceExecutionLogger import ServiceExecutionLogger
from app.services.OrderPositionExecutionFee.application.services.ExecuteOrderPositionExecutionFeeService import (
    ExecuteOrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig,
)
from app.services.OrderPositionExecutionFee.domain.scenarios.OrderPositionExecutionFeeScenarios import (
    OrderPositionExecutionFeeScenarios,
)


class OrderPositionExecutionFeesRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/admin/order-position-execution-fees",
            tags=["admin-order-position-execution-fees"],
        )
        self.policy = SystemWalletAccessPolicy()
        self.control_service = OrderPositionExecutionFeesControlService()
        self.router.add_api_route(
            "/state",
            self.get_state,
            methods=["GET"],
            response_model=OrderPositionExecutionFeesStateResponse,
        )
        self.router.add_api_route(
            "/enable",
            self.enable_service,
            methods=["POST"],
            response_model=OrderPositionExecutionFeesStateResponse,
        )
        self.router.add_api_route(
            "/disable",
            self.disable_service,
            methods=["POST"],
            response_model=OrderPositionExecutionFeesStateResponse,
        )
        self.router.add_api_route(
            "/run/{tariff_type}",
            self.run_test,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/logs",
            self.get_logs,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/logs",
            self.clear_logs,
            methods=["DELETE"],
        )

    def get_state(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        return self.control_service.get_state()

    def enable_service(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        return self.control_service.set_enabled(True)

    def disable_service(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        return self.control_service.set_enabled(False)

    def run_test(
        self,
        tariff_type: Literal["orders", "positions"],
        payload: OrderPositionExecutionFeesRunRequest,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        if not self.control_service.is_enabled():
            raise HTTPException(
                status_code=409,
                detail="Order and position execution fees service is disabled",
            )

        config = OrderPositionExecutionFeeConfig
        log_file = Path(config.LOG_DIRECTORY) / config.LOG_FILENAME
        event_id = f"manual-{tariff_type}-{uuid4()}"

        with ServiceExecutionLogger(
            service_name="order_position_execution_fee_manual_request",
            log_file=log_file,
        ) as execution_logger:
            execution_logger.record_event(
                "Manual test request: "
                f"tariff_type={tariff_type}, "
                f"mode={payload.mode}, "
                f"volume_usdt={payload.volume_usdt}, "
                f"caller_user_id={current_user.id}, "
                f"event_id={event_id}"
            )

        scenario = (
            OrderPositionExecutionFeeScenarios.order()
            if tariff_type == "orders"
            else OrderPositionExecutionFeeScenarios.position_opening()
        )

        try:
            result = ExecuteOrderPositionExecutionFeeService.execute(
                session,
                user_id=current_user.id,
                event_id=event_id,
                mode=payload.mode,
                tariff_type=tariff_type,
                scenario=scenario,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=409,
                detail=f"Execution fee test failed: {exc}",
            ) from exc

        return {
            "status": "completed",
            "tariff_type": tariff_type,
            "mode": payload.mode,
            "volume_usdt": str(payload.volume_usdt),
            "fee_currency": config.CURRENCY_CODE,
            "event_id": event_id,
            "result": jsonable_encoder(result),
        }

    def get_logs(
        self,
        limit: int = Query(default=200, ge=1, le=2000),
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        config = OrderPositionExecutionFeeConfig
        log_file = Path(config.LOG_DIRECTORY) / config.LOG_FILENAME
        if not log_file.exists():
            return {"service_name": "order-position-execution-fees", "lines": []}
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            raise HTTPException(status_code=500, detail="Unable to read service log") from exc
        return {
            "service_name": "order-position-execution-fees",
            "lines": lines[-limit:],
        }

    def clear_logs(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        config = OrderPositionExecutionFeeConfig
        log_file = Path(config.LOG_DIRECTORY) / config.LOG_FILENAME
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text("", encoding="utf-8")
        except OSError as exc:
            raise HTTPException(status_code=500, detail="Unable to clear service log") from exc
        return {"service_name": "order-position-execution-fees", "cleared": True}
