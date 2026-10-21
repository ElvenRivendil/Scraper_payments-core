# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/config/SystemFundsConsolidationConfig.py */
from __future__ import annotations


class SystemFundsConsolidationConfig:
    CURRENCY_CODE = "SCR"
    SOURCE_WALLET_CODES: tuple[str, ...] = (
        "ITFP",
        "EWFP",
        "OCFP",
        "PCFP",
        "PTCP",
        "DPAP",
        "ILAP",
    )
    DESTINATION_WALLET_CODE = "SCAP"
    MINIMUM_TRANSFER_MINOR = 1
    IDEMPOTENCY_SCOPE = "system_funds_consolidation.hourly"
    IDEMPOTENCY_PREFIX = "sfc"
    DESCRIPTION_PREFIX = "Hourly system funds consolidation"
    SCHEDULE_MINUTE = 15
    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "system_funds_consolidation.log"

    @classmethod
    def validate(cls) -> None:
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")
        if not cls.SOURCE_WALLET_CODES:
            raise ValueError("At least one source wallet must be configured.")
        if any(not code for code in cls.SOURCE_WALLET_CODES):
            raise ValueError("Source wallet codes must not be empty.")
        if len(cls.SOURCE_WALLET_CODES) != len(set(cls.SOURCE_WALLET_CODES)):
            raise ValueError("Source wallet codes must be unique.")
        if not cls.DESTINATION_WALLET_CODE:
            raise ValueError("Destination wallet code must not be empty.")
        if cls.DESTINATION_WALLET_CODE in cls.SOURCE_WALLET_CODES:
            raise ValueError("Source and destination wallet codes must differ.")
        if cls.MINIMUM_TRANSFER_MINOR < 1:
            raise ValueError("Minimum transfer amount must be positive.")
        if not 0 <= cls.SCHEDULE_MINUTE <= 59:
            raise ValueError("Schedule minute must be between 0 and 59.")
