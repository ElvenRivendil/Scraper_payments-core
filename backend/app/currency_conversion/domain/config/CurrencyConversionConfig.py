# /* ../NauTrader_Helm/payments-core/backend/app/currency_conversion/domain/config/CurrencyConversionConfig.py */
from decimal import Decimal, ROUND_HALF_UP


class CurrencyConversionConfig:
    DEFAULT_RATE = Decimal("1")
    DEFAULT_SOURCE_CURRENCY = "USDT"
    DEFAULT_TARGET_CURRENCY = "SCR"
    DEFAULT_SOURCE_PRECISION = 8
    DEFAULT_TARGET_PRECISION = 8
    DEFAULT_ROUNDING = ROUND_HALF_UP
