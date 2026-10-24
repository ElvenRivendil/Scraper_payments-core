# /* ../NauTrader_Helm/payments-core/backend/app/currency_conversion/application/services/CurrencyConversionService.py */
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.currency_conversion.domain.config.CurrencyConversionConfig import (
    CurrencyConversionConfig as Config,
)
from app.currency_conversion.domain.models.CurrencyConversionResult import (
    CurrencyConversionResult,
)


class CurrencyConversionService:
    @classmethod
    def convert(
        cls,
        amount: Decimal | str | int,
        *,
        source_currency: str = Config.DEFAULT_SOURCE_CURRENCY,
        target_currency: str = Config.DEFAULT_TARGET_CURRENCY,
        rate: Decimal = Config.DEFAULT_RATE,
        source_precision: int = Config.DEFAULT_SOURCE_PRECISION,
        target_precision: int = Config.DEFAULT_TARGET_PRECISION,
        rounding: str = ROUND_HALF_UP,
    ) -> CurrencyConversionResult:
        return cls._convert(
            amount,
            source_currency=source_currency,
            target_currency=target_currency,
            rate=rate,
            source_precision=source_precision,
            target_precision=target_precision,
            rounding=rounding,
            inverse=False,
        )

    @classmethod
    def convert_back(
        cls,
        amount: Decimal | str | int,
        *,
        source_currency: str = Config.DEFAULT_SOURCE_CURRENCY,
        target_currency: str = Config.DEFAULT_TARGET_CURRENCY,
        rate: Decimal = Config.DEFAULT_RATE,
        source_precision: int = Config.DEFAULT_SOURCE_PRECISION,
        target_precision: int = Config.DEFAULT_TARGET_PRECISION,
        rounding: str = ROUND_HALF_UP,
    ) -> CurrencyConversionResult:
        return cls._convert(
            amount,
            source_currency=target_currency,
            target_currency=source_currency,
            rate=rate,
            source_precision=target_precision,
            target_precision=source_precision,
            rounding=rounding,
            inverse=True,
        )

    @classmethod
    def _convert(
        cls,
        amount: Decimal | str | int,
        *,
        source_currency: str,
        target_currency: str,
        rate: Decimal,
        source_precision: int,
        target_precision: int,
        rounding: str,
        inverse: bool,
    ) -> CurrencyConversionResult:
        if isinstance(amount, bool) or isinstance(amount, float):
            raise TypeError("Amount must be Decimal, str, or int; float is not supported.")
        if isinstance(rate, bool) or isinstance(rate, float):
            raise TypeError("Conversion rate must be Decimal, str, or int; float is not supported.")
        try:
            input_amount = Decimal(amount)
            conversion_rate = Decimal(rate)
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid conversion amount or rate.") from exc
        if not input_amount.is_finite() or input_amount < 0:
            raise ValueError("Conversion amount must be finite and non-negative.")
        if not conversion_rate.is_finite() or conversion_rate <= 0:
            raise ValueError("Conversion rate must be finite and greater than zero.")
        if not isinstance(source_currency, str) or not source_currency.strip():
            raise ValueError("Source currency must not be empty.")
        if not isinstance(target_currency, str) or not target_currency.strip():
            raise ValueError("Target currency must not be empty.")
        if source_currency == target_currency:
            raise ValueError("Source and target currencies must differ.")
        for precision in (source_precision, target_precision):
            if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
                raise ValueError("Currency precision must be a non-negative integer.")
        if not isinstance(rounding, str):
            raise TypeError("Rounding mode must be a decimal rounding constant.")

        output_amount = (
            input_amount / conversion_rate
            if inverse
            else input_amount * conversion_rate
        )
        quantum = Decimal("1").scaleb(-target_precision)
        try:
            output_amount = output_amount.quantize(quantum, rounding=rounding)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Currency conversion could not be rounded to target precision.") from exc

        return CurrencyConversionResult(
            input_amount=input_amount,
            input_currency=source_currency,
            output_amount=output_amount,
            output_currency=target_currency,
            rate=conversion_rate,
            inverse=inverse,
        )
