# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/PrepareOrderPositionExecutionFeeService.py */
from decimal import Decimal
from typing import Literal
from uuid import UUID

from app.services.OrderPositionExecutionFee.application.services.ExecutionFeePreparationStore import (
    ExecutionFeePreparationStore,
)
from app.services.OrderPositionExecutionFee.application.services.ResolveExecutionFeeTariffService import (
    ResolveExecutionFeeTariffService,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeePreparation import (
    ExecutionFeePreparation,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeResult import (
    ExecutionFeeResult,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)


class PrepareOrderPositionExecutionFeeService:
    @classmethod
    def prepare(
        cls,
        *,
        user_id: UUID,
        event_id: str,
        mode: Literal["paper", "live", "mock", "backtests"],
        fee_type: Literal["order", "position_opening", "position_closing"],
        tariff_type: Literal["orders", "positions"],
        scenario: ExecutionFeeScenario,
        volume_usdt: Decimal = Decimal("0"),
        is_protective_order: bool = False,
    ) -> ExecutionFeeResult:
        if not event_id.strip():
            raise ValueError("Execution event ID must not be empty.")
        if volume_usdt < 0:
            raise ValueError("Execution volume must not be negative.")
        if is_protective_order and fee_type != "order":
            raise ValueError("Protective order flag is only valid for order fees.")

        if is_protective_order:
            preparation = ExecutionFeePreparation(
                user_id=user_id,
                event_id=event_id.strip(),
                mode=mode,
                fee_type=fee_type,
                tariff_type=tariff_type,
                volume_usdt=volume_usdt,
                amount_minor=0,
                tariff_enabled=True,
                is_protective_order=True,
                scenario=scenario,
            )
            ExecutionFeePreparationStore.put(preparation)
            return ExecutionFeeResult(
                status="protective_order_no_fee",
                amount_minor=0,
                created=False,
            )

        tariff = ResolveExecutionFeeTariffService.resolve(
            user_id=user_id,
            mode=mode,
            tariff_type=tariff_type,
        )
        amount_minor = tariff.amount_minor if tariff.enabled else 0
        preparation = ExecutionFeePreparation(
            user_id=user_id,
            event_id=event_id.strip(),
            mode=mode,
            fee_type=fee_type,
            tariff_type=tariff_type,
            volume_usdt=volume_usdt,
            amount_minor=amount_minor,
            tariff_enabled=tariff.enabled,
            is_protective_order=False,
            scenario=scenario,
        )
        ExecutionFeePreparationStore.put(preparation)
        return ExecutionFeeResult(
            status="prepared" if tariff.enabled else "tariff_disabled",
            amount_minor=amount_minor,
            created=False,
        )
