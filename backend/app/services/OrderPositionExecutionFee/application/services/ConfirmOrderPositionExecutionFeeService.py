# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/ConfirmOrderPositionExecutionFeeService.py */
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.ExecutionFee.application.services.ExecutionFeeConfirmationService import (
    ExecutionFeeConfirmationService,
)
from app.services.OrderPositionExecutionFee.application.services.ExecutionFeePreparationStore import (
    ExecutionFeePreparationStore,
)
from app.services.OrderPositionExecutionFee.application.services.OrderPositionExecutionFeeService import (
    OrderPositionExecutionFeeService,
)
from app.services.OrderPositionExecutionFee.application.services.ResolveExecutionFeeTariffService import (
    ResolveExecutionFeeTariffService,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeResult import (
    ExecutionFeeResult,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)
from app.services.OrderPositionExecutionFee.domain.scenarios.OrderPositionExecutionFeeScenarios import (
    OrderPositionExecutionFeeScenarios,
)
from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount


class ConfirmOrderPositionExecutionFeeService:
    @classmethod
    def confirm(
        cls,
        session: Session,
        *,
        user_id: UUID,
        event_id: str,
        mode: Literal["paper", "live", "mock", "backtests"],
        fee_type: Literal["order", "position_opening", "position_closing"],
        is_protective_order: bool = False,
    ) -> ExecutionFeeResult:
        normalized_event_id = event_id.strip()
        if not normalized_event_id:
            raise ValueError("Execution event ID must not be empty.")
        if is_protective_order and fee_type != "order":
            raise ValueError("Protective order flag is only valid for order fees.")

        preparation = ExecutionFeePreparationStore.get(
            user_id=user_id,
            event_id=normalized_event_id,
            mode=mode,
            fee_type=fee_type,
        )
        if preparation is not None:
            scenario = preparation.scenario
            tariff_type = preparation.tariff_type
            prepared_amount_minor = preparation.amount_minor
            prepared_tariff_enabled = preparation.tariff_enabled
            effective_protective_order = preparation.is_protective_order
        else:
            scenario, tariff_type = cls._resolve_scenario(fee_type)
            prepared_amount_minor = None
            prepared_tariff_enabled = None
            effective_protective_order = is_protective_order

        idempotency_key = (
            f"{scenario.idempotency_prefix}:{user_id}:{normalized_event_id}"
        )

        def resolve_tariff() -> tuple[bool, int]:
            tariff = ResolveExecutionFeeTariffService.resolve(
                user_id=user_id,
                mode=mode,
                tariff_type=tariff_type,
            )
            return tariff.enabled, tariff.amount_minor

        def execute_fee(amount_minor: int) -> ExecutionFeeResult:
            return OrderPositionExecutionFeeService.execute(
                session,
                user_id=user_id,
                event_id=normalized_event_id,
                tariff_amount=ScripeAmount.from_minor_units(amount_minor),
                scenario=scenario,
            )

        result = ExecutionFeeConfirmationService.confirm(
            session,
            idempotency_key=idempotency_key,
            idempotency_scope=scenario.idempotency_scope,
            execute_fee=execute_fee,
            resolve_tariff=resolve_tariff,
            prepared_amount_minor=prepared_amount_minor,
            prepared_tariff_enabled=prepared_tariff_enabled,
            is_protective_order=effective_protective_order,
        )

        if result.status in {
            "charged",
            "already_processed",
            "no_fee",
            "tariff_disabled",
            "protective_order_no_fee",
            "skipped_insufficient_funds",
        }:
            ExecutionFeePreparationStore.remove(
                user_id=user_id,
                event_id=normalized_event_id,
                mode=mode,
                fee_type=fee_type,
            )
        return result

    @staticmethod
    def _resolve_scenario(
        fee_type: Literal["order", "position_opening", "position_closing"],
    ) -> tuple[ExecutionFeeScenario, Literal["orders", "positions"]]:
        if fee_type == "order":
            return OrderPositionExecutionFeeScenarios.order(), "orders"
        if fee_type == "position_opening":
            return OrderPositionExecutionFeeScenarios.position_opening(), "positions"
        if fee_type == "position_closing":
            return OrderPositionExecutionFeeScenarios.position_closing(), "positions"
        raise ValueError("Unsupported execution fee type.")
