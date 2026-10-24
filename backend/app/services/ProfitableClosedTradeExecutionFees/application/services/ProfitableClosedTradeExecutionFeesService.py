# /* ../NauTrader_Helm/payments-core/backend/app/services/ProfitableClosedTradeExecutionFees/application/services/ProfitableClosedTradeExecutionFeesService.py */
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas import TransferCreate
from app.currency_conversion.application.services.CurrencyConversionService import (
    CurrencyConversionService,
)
from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount
from app.services.transfers import create_transfer
from app.services.ParameterizedExecutionFee.application.services.ParameterizedExecutionFeeService import (
    ParameterizedExecutionFeeService,
)
from app.services.ProfitableClosedTradeExecutionFees.application.operations.ResolveProfitableClosedTradeFeeWalletsOperation import (
    ResolveProfitableClosedTradeFeeWalletsOperation,
)
from app.services.ProfitableClosedTradeExecutionFees.domain.config.ProfitableClosedTradeExecutionFeesConfig import (
    ProfitableClosedTradeExecutionFeesConfig as Config,
)
from app.services.ProfitableClosedTradeExecutionFees.domain.models.ProfitableClosedTradeExecutionFeeResult import (
    ProfitableClosedTradeExecutionFeeResult,
)


class ProfitableClosedTradeExecutionFeesService:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
        event_id: str,
        mode: str,
        profit_usdt: Decimal,
        conversion_rate: Decimal | None = None,
    ) -> ProfitableClosedTradeExecutionFeeResult:
        Config.validate()
        normalized_event_id = event_id.strip()
        if not normalized_event_id:
            raise ValueError("Execution event ID must not be empty.")
        if not profit_usdt.is_finite() or profit_usdt < 0:
            raise ValueError("Profit must be a finite non-negative amount.")
        if profit_usdt == 0:
            return ProfitableClosedTradeExecutionFeeResult(
                status="no_fee",
                amount_minor=0,
                created=False,
                band_key="",
                percent=Decimal("0"),
            )

        calculation = ParameterizedExecutionFeeService.calculate(
            user_id=user_id,
            mode=mode,
            volume=profit_usdt,
            tariff_entity_key=Config.TARIFF_ENTITY_KEY,
            percentage_key=Config.TARIFF_KEY,
        )
        effective_rate = Config.CONVERSION_RATE if conversion_rate is None else conversion_rate
        conversion = CurrencyConversionService.convert(
            calculation.amount,
            source_currency=Config.PROFIT_CURRENCY_CODE,
            target_currency=Config.CURRENCY_CODE,
            rate=effective_rate,
            source_precision=Config.USDT_PRECISION,
            target_precision=Config.SCR_PRECISION,
            rounding=Config.CONVERSION_ROUNDING,
        )
        amount_minor = ScripeAmount.to_minor_units(conversion.output_amount)
        if amount_minor == 0:
            return ProfitableClosedTradeExecutionFeeResult(
                status="no_fee",
                amount_minor=0,
                created=False,
                band_key=calculation.band_key,
                percent=calculation.percent,
            )

        source, destination = ResolveProfitableClosedTradeFeeWalletsOperation.execute(
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
                "profit_usdt": str(profit_usdt),
                "band_key": calculation.band_key,
                "percent": str(calculation.percent),
                "fee_usdt": str(calculation.amount),
                "conversion_rate": str(effective_rate),
                "fee_scr": str(conversion.output_amount),
                "amount_minor": amount_minor,
                "from_wallet_code": source.wallet_code,
                "to_wallet_code": destination.wallet_code,
            },
        )
        return ProfitableClosedTradeExecutionFeeResult(
            status="charged" if result.created else "already_processed",
            amount_minor=amount_minor,
            created=result.created,
            band_key=calculation.band_key,
            percent=calculation.percent,
            transaction=result.payload,
        )
