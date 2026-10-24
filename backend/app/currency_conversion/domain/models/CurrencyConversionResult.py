# /* ../NauTrader_Helm/payments-core/backend/app/currency_conversion/domain/models/CurrencyConversionResult.py */
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CurrencyConversionResult:
    input_amount: Decimal
    input_currency: str
    output_amount: Decimal
    output_currency: str
    rate: Decimal
    inverse: bool
