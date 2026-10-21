# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/OrderPositionExecutionFeeService.py */

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas import TransferCreate
from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount
from app.services.transfers import TransferConflictError, create_transfer
from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig as Config,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeResult import (
    ExecutionFeeResult,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)
from app.services.OrderPositionExecutionFee.application.operations.ResolveUserFeeWalletsOperation import (
    ResolveUserFeeWalletsOperation,
)


class OrderPositionExecutionFeeService:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
        event_id: str,
        tariff_amount: Decimal,
        scenario: ExecutionFeeScenario,
    ) -> ExecutionFeeResult:
        Config.validate()
        scenario.validate()
        if not event_id.strip():
            raise ValueError("Execution event ID must not be empty.")
        if not isinstance(tariff_amount, Decimal):
            raise TypeError("Tariff amount must be Decimal.")
        amount_minor = ScripeAmount.to_minor_units(tariff_amount)
        if amount_minor < 0:
            raise ValueError("Execution fee must not be negative.")
        if amount_minor == 0:
            return ExecutionFeeResult(
                status="no_fee",
                amount_minor=0,
                created=False,
            )

        source, destination = ResolveUserFeeWalletsOperation.execute(
            session,
            user_id=user_id,
            destination_wallet_code=scenario.destination_wallet_code,
        )
        idempotency_key = (
            f"{scenario.idempotency_prefix}:{user_id}:{event_id.strip()}"
        )
        transfer = TransferCreate(
            from_account_id=source.id,
            to_account_id=destination.id,
            currency_code=Config.CURRENCY_CODE,
            amount_minor=amount_minor,
            description=(
                f"{scenario.description_prefix} "
                f"{event_id.strip()}"
            ),
        )
        request_payload = {
            "user_id": str(user_id),
            "event_id": event_id.strip(),
            "tariff_key": scenario.tariff_key,
            "amount_minor": amount_minor,
            "from_wallet_code": source.wallet_code,
            "to_wallet_code": destination.wallet_code,
        }
        try:
            result = create_transfer(
                session,
                idempotency_key=idempotency_key,
                transfer=transfer,
                owner_id=user_id,
                scope=scenario.idempotency_scope,
                request_payload=request_payload,
            )
        except TransferConflictError as error:
            if error.code != "INSUFFICIENT_FUNDS":
                raise
            should_continue = scenario.insufficient_funds_policy.handle(error)
            if not should_continue:
                return ExecutionFeeResult(
                    status="skipped_insufficient_funds",
                    amount_minor=amount_minor,
                    created=False,
                )
            raise

        return ExecutionFeeResult(
            status="charged" if result.created else "already_processed",
            amount_minor=amount_minor,
            created=result.created,
            transaction=result.payload,
        )
