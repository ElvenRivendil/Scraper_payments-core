# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsAggregation/domain/config/SystemWalletsAggregationConfig.py */

class SystemWalletsAggregationConfig:
    CURRENCY_CODE = "SCR"
    WALLET_PAIRS: tuple[tuple[str, str], ...] = (
        ("ER", "ERP"),
        ("IS", "ISP"),
        ("PM", "PMP"),
        ("BD", "BDP"),
        ("SYA", "SYAP"),
    )
    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "system_wallets_aggregation.log"

    @classmethod
    def get_wallet_pairs(cls) -> tuple[tuple[str, str], ...]:
        return cls.WALLET_PAIRS

    @classmethod
    def get_wallet_pair(cls, user_wallet_code: str) -> tuple[str, str]:
        for source_code, destination_code in cls.WALLET_PAIRS:
            if source_code == user_wallet_code:
                return source_code, destination_code
        raise ValueError(
            f"Unsupported aggregation source wallet: {user_wallet_code}."
        )

    @classmethod
    def validate(cls) -> None:
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")
        if not cls.WALLET_PAIRS:
            raise ValueError("At least one wallet pair must be configured.")

        source_codes = []
        destination_codes = []
        for source_code, destination_code in cls.WALLET_PAIRS:
            if not source_code or not destination_code:
                raise ValueError("Wallet codes must not be empty.")
            if source_code == destination_code:
                raise ValueError("Source and destination wallet codes must differ.")
            source_codes.append(source_code)
            destination_codes.append(destination_code)

        if len(source_codes) != len(set(source_codes)):
            raise ValueError("Source wallet codes must be unique.")
        if len(destination_codes) != len(set(destination_codes)):
            raise ValueError("Destination wallet codes must be unique.")
