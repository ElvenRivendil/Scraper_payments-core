# /* ../NauTrader_Helm/payments-core/backend/app/services/PositionPercentValueExecutionFees/application/services/PositionPercentValueExecutionFeesService.py */

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas import TransferCreate
from app.services.transfers import create_transfer
from app.services.ParameterizedExecutionFee.application.services.ParameterizedExecutionFeeService import (
    ParameterizedExecutionFeeService,
)
from app.services.PositionPercentValueExecutionFees.application.operations.ResolvePositionPercentValueFeeWalletsOperation import (
    ResolvePositionPercentValueFeeWalletsOperation,
)
from app.services.PositionPercentValueExecutionFees.domain.config.PositionPercentValueExecutionFeesConfig import (
    PositionPercentValueExecutionFeesConfig as Config,
)
from app.services.PositionPercentValueExecutionFees.domain.models.PositionPercentValueExecutionFeeResult import (
    PositionPercentValueExecutionFeeResult,
)


class PositionPercentValueExecutionFeesService:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
        event_id: str,
        mode: str,
        volume: Decimal,
    ) -> PositionPercentValueExecutionFeeResult:
        Config.validate()
        normalized_event_id = event_id.strip()
        if not normalized_event_id:
            raise ValueError("Execution event ID must not be empty.")

        calculation = ParameterizedExecutionFeeService.calculate(
            user_id=user_id,
            mode=mode,
            volume=volume,
            tariff_entity_key=Config.TARIFF_ENTITY_KEY,
        )
        amount_minor = calculation.amount_minor
        if amount_minor == 0:
            return PositionPercentValueExecutionFeeResult(
                status="no_fee",
                amount_minor=0,
                created=False,
                band_key=calculation.band_key,
                percent=calculation.percent,
            )

        source, destination = ResolvePositionPercentValueFeeWalletsOperation.execute(
            session,
            user_id=user_id,
        )
        idempotency_key = (
            f"{Config.IDEMPOTENCY_PREFIX}:{user_id}:{normalized_event_id}"
        )
        transfer = TransferCreate(
            from_account_id=source.id,
            to_account_id=destination.id,
            currency_code=Config.CURRENCY_CODE,
            amount_minor=amount_minor,
            description=f"{Config.DESCRIPTION_PREFIX} {normalized_event_id}",
        )
        result = create_transfer(
            session,
            idempotency_key=idempotency_key,
            transfer=transfer,
            owner_id=user_id,
            scope=Config.IDEMPOTENCY_SCOPE,
            request_payload={
                "user_id": str(user_id),
                "event_id": normalized_event_id,
                "mode": mode,
                "band_key": calculation.band_key,
                "percent": calculation.percent,
                "volume": str(volume),
                "amount_minor": amount_minor,
                "from_wallet_code": source.wallet_code,
                "to_wallet_code": destination.wallet_code,
            },
        )
        return PositionPercentValueExecutionFeeResult(
            status="charged" if result.created else "already_processed",
            amount_minor=amount_minor,
            created=result.created,
            band_key=calculation.band_key,
            percent=calculation.percent,
            transaction=result.payload,
        )
