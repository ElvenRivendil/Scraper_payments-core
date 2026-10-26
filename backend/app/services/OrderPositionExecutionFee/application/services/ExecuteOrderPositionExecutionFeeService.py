# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/ExecuteOrderPositionExecutionFeeService.py */

import logging
from pathlib import Path
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.execution_logging.ServiceExecutionLogger import ServiceExecutionLogger
from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount
from app.services.OrderPositionExecutionFee.application.services.OrderPositionExecutionFeeService import (
    OrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.application.services.ResolveExecutionFeeTariffService import (
    ResolveExecutionFeeTariffService,
)
from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig as Config,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeResult import (
    ExecutionFeeResult,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)

logger = logging.getLogger(__name__)


class ExecuteOrderPositionExecutionFeeService:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
        event_id: str,
        mode: Literal["paper", "live", "mock", "backtests"],
        tariff_type: Literal["orders", "positions"],
        scenario: ExecutionFeeScenario,
    ) -> ExecutionFeeResult:
        execution = ServiceExecutionLogger(
            service_name="order_position_execution_fee",
            log_file=Path(Config.LOG_DIRECTORY) / Config.LOG_FILENAME,
            console_logger=logger,
        )
        with execution:
            execution.record_event(
                f"user_id={user_id} event_id={event_id} mode={mode} "
                f"tariff_type={tariff_type} phase=tariff_resolution"
            )
            try:
                tariff = ResolveExecutionFeeTariffService.resolve(
                    user_id=user_id,
                    mode=mode,
                    tariff_type=tariff_type,
                    diagnostic_logger=execution.record_event,
                )
            except Exception as error:
                execution.record_error(
                    "Execution fee tariff could not be resolved",
                    exception=error,
                )
                execution.set_status("tariff_resolution_error")
                raise

            execution.record_event(
                f"tariff_enabled={tariff.enabled} amount_minor={tariff.amount_minor}"
            )
            if not tariff.enabled:
                result = ExecutionFeeResult(
                    status="tariff_disabled",
                    amount_minor=tariff.amount_minor,
                    created=False,
                )
                execution.record_event("result_status=tariff_disabled transfer=skipped")
                execution.set_status(result.status)
                return result

            try:
                result = OrderPositionExecutionFeeService.execute(
                    session,
                    user_id=user_id,
                    event_id=event_id,
                    tariff_amount=ScripeAmount.from_minor_units(tariff.amount_minor),
                    scenario=scenario,
                )
            except Exception as error:
                execution.record_error(
                    "Execution fee processing failed",
                    exception=error,
                )
                execution.set_status("execution_error")
                raise

            execution.record_event(
                f"result_status={result.status} amount_minor={result.amount_minor} "
                f"created={result.created}"
            )
            execution.set_status(result.status)
            return result
