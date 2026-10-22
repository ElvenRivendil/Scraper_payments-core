# /* ../NauTrader_Helm/payments-core/backend/app/api/execution_fee_services/api/ExecutionFeeServiceRoutes.py */
from decimal import Decimal
from pathlib import Path
from typing import Callable
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api.execution_fee_services.application.services.ExecutionFeeServiceControlService import (
    ExecutionFeeServiceControlService,
)
from app.api.execution_fee_services.application.services.ExecutionFeeServiceLogService import (
    ExecutionFeeServiceLogService,
)
from app.api.execution_fee_services.domain.models.ExecutionFeeServiceRunRequest import (
    ExecutionFeeServiceRunRequest,
)
from app.api.execution_fee_services.domain.models.ExecutionFeeServiceStateResponse import (
    ExecutionFeeServiceStateResponse,
)
from app.core.auth import AuthenticatedUser, require_current_user
from app.core.authorization.SystemWalletAccessPolicy import SystemWalletAccessPolicy
from app.core.db import get_db
from app.core.execution_logging.ServiceExecutionLogger import ServiceExecutionLogger


class ExecutionFeeServiceRoutes:
    def __init__(
        self,
        *,
        service_name: str,
        config: type,
        executor: Callable[[Session, UUID, str, str, Decimal], object],
        input_field: str = "volume_usdt",
    ) -> None:
        self.service_name = service_name
        self.config = config
        self.executor = executor
        self.input_field = input_field
        self.policy = SystemWalletAccessPolicy()
        self.control_service = ExecutionFeeServiceControlService(
            service_name=service_name,
            log_directory=config.LOG_DIRECTORY,
        )
        self.log_service = ExecutionFeeServiceLogService(
            service_name=service_name,
            config=config,
        )
        self.router = APIRouter(
            prefix=f"/admin/{service_name}",
            tags=[f"admin-{service_name}"],
        )
        self.router.add_api_route(
            "/state",
            self.get_state,
            methods=["GET"],
            response_model=ExecutionFeeServiceStateResponse,
        )
        self.router.add_api_route(
            "/enable",
            self.enable_service,
            methods=["POST"],
            response_model=ExecutionFeeServiceStateResponse,
        )
        self.router.add_api_route(
            "/disable",
            self.disable_service,
            methods=["POST"],
            response_model=ExecutionFeeServiceStateResponse,
        )
        self.router.add_api_route("/run", self.run_test, methods=["POST"])
        self.router.add_api_route("/logs", self.get_logs, methods=["GET"])
        self.router.add_api_route("/logs", self.clear_logs, methods=["DELETE"])

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
        payload: ExecutionFeeServiceRunRequest,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        if not self.control_service.is_enabled():
            raise HTTPException(
                status_code=409,
                detail=f"{self.service_name} service is disabled",
            )

        input_value = getattr(payload, self.input_field, None)
        if input_value is None:
            raise HTTPException(status_code=422, detail=f"{self.input_field} is required")

        event_id = f"manual-{self.service_name}-{uuid4()}"
        log_file = Path(self.config.LOG_DIRECTORY) / self.config.LOG_FILENAME
        try:
            with ServiceExecutionLogger(
                service_name=f"{self.service_name}_manual_request",
                log_file=log_file,
            ) as execution_logger:
                execution_logger.record_event(
                    f"Manual request mode={payload.mode} "
                    f"{self.input_field}={input_value} "
                    f"caller_user_id={current_user.id} event_id={event_id}"
                )
                result = self.executor(
                    session,
                    current_user.id,
                    event_id,
                    payload.mode,
                    input_value,
                )
                execution_logger.set_status("completed")
        except Exception as exc:
            raise HTTPException(
                status_code=409,
                detail=f"{self.service_name} manual run failed: {exc}",
            ) from exc

        return {
            "status": "completed",
            "service_name": self.service_name,
            "mode": payload.mode,
            self.input_field: str(input_value),
            "event_id": event_id,
            "result": jsonable_encoder(result),
        }

    def get_logs(
        self,
        limit: int = Query(default=200, ge=1, le=2000),
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        return self.log_service.get_logs(limit)

    def clear_logs(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, object]:
        self.policy.require_access(current_user)
        return self.log_service.clear_logs()
