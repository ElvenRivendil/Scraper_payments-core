# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/config/SystemFundsDistributionConfig.py */
from app.services.SystemFundsConsolidation.domain.strategies.one_to_many.ProportionalDistributionStrategy import (
    ProportionalDistributionStrategy,
)


class SystemFundsDistributionConfig:
    EXECUTION_TYPE = "SYSTEM_FUNDS_DISTRIBUTION"
    CURRENCY_CODE = "SCR"
    SOURCE_WALLET_CODE = "SCAP"
    DESTINATION_WALLET_CODES: tuple[str, ...] = ("SPAP", "WRAP")
    DISTRIBUTION_STRATEGY = ProportionalDistributionStrategy
    DESTINATION_WEIGHTS: dict[str, int] = {
        "SPAP": 25,
        "WRAP": 75,
    }
    DESTINATION_PRIORITIES: dict[str, int] = {
        "SPAP": 0,
        "WRAP": 1,
    }
    DESTINATION_MAX_AMOUNTS_MINOR: dict[str, int] = {}
    MINIMUM_TRANSFER_MINOR = 1
    IDEMPOTENCY_SCOPE = "system_funds_distribution.hourly"
    IDEMPOTENCY_PREFIX = "sfd"
    DESCRIPTION_PREFIX = "Hourly system funds distribution"
    SCHEDULE_MINUTE = 10
    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "system_funds_distribution.log"

    @classmethod
    def validate(cls) -> None:
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")
        if not cls.SOURCE_WALLET_CODE:
            raise ValueError("Source wallet code must not be empty.")
        if not cls.DESTINATION_WALLET_CODES:
            raise ValueError("At least one destination wallet is required.")
        if cls.SOURCE_WALLET_CODE in cls.DESTINATION_WALLET_CODES:
            raise ValueError("Source and destination wallets must differ.")
        if len(cls.DESTINATION_WALLET_CODES) != len(set(cls.DESTINATION_WALLET_CODES)):
            raise ValueError("Destination wallet codes must be unique.")
        if set(cls.DESTINATION_WEIGHTS) != set(cls.DESTINATION_WALLET_CODES):
            raise ValueError("Distribution weights must match destination wallets.")
        if any(
            type(weight) is not int or not 0 <= weight <= 100
            for weight in cls.DESTINATION_WEIGHTS.values()
        ):
            raise ValueError("Distribution weights must be integers between 0 and 100.")
        if sum(cls.DESTINATION_WEIGHTS.values()) != 100:
            raise ValueError("Distribution weights must sum to 100.")
        if set(cls.DESTINATION_PRIORITIES) != set(cls.DESTINATION_WALLET_CODES):
            raise ValueError("Distribution priorities must match destination wallets.")
        if any(amount < 1 for amount in cls.DESTINATION_MAX_AMOUNTS_MINOR.values()):
            raise ValueError("Destination maximum amounts must be positive.")
        if not 0 <= cls.SCHEDULE_MINUTE <= 59:
            raise ValueError("Schedule minute must be between 0 and 59.")
