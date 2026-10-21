# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/application/services/SystemFundsDistributionSharesState.py */
from redis import Redis

from app.core.config import get_settings


class SystemFundsDistributionSharesState:
    KEY = "payments_core:system_funds_distribution:shares"
    DEFAULT_SHARES = {
        "SPAP": 25,
        "WRAP": 75,
    }
    WALLET_CODES = ("SPAP", "WRAP")

    def __init__(self) -> None:
        self.redis = Redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )

    @classmethod
    def validate_shares(cls, shares: dict[str, int]) -> dict[str, int]:
        if set(shares) != set(cls.WALLET_CODES):
            raise ValueError("Shares must define SPAP and WRAP.")
        if any(
            type(value) is not int or not 0 <= value <= 100
            for value in shares.values()
        ):
            raise ValueError("Each share must be an integer between 0 and 100.")
        if sum(shares.values()) != 100:
            raise ValueError("Distribution shares must sum to 100.")
        return {code: shares[code] for code in cls.WALLET_CODES}

    def get_shares(self) -> dict[str, int]:
        stored = self.redis.hgetall(self.KEY)
        if not stored:
            return dict(self.DEFAULT_SHARES)
        try:
            shares = {
                code: int(stored[code])
                for code in self.WALLET_CODES
            }
        except (KeyError, TypeError, ValueError):
            raise ValueError("Stored distribution shares are invalid.") from None
        return self.validate_shares(shares)

    def update_shares(
        self,
        spap_percentage: int,
        wrap_percentage: int,
    ) -> dict[str, int]:
        shares = self.validate_shares({
            "SPAP": spap_percentage,
            "WRAP": wrap_percentage,
        })
        self.redis.hset(self.KEY, mapping={
            code: str(shares[code])
            for code in self.WALLET_CODES
        })
        return shares
