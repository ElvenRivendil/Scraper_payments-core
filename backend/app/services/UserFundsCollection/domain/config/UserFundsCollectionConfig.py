# /* ../NauTrader_Helm/payments-core/backend/app/services/UserFundsCollection/domain/config/UserFundsCollectionConfig.py */

class UserFundsCollectionConfig:
    CURRENCY_CODE = "SCR"

    # Fixed direction: user wallet -> system wallet.
    WALLET_PAIRS: tuple[tuple[str, str], ...] = (
        ("ITF", "ITFP"),
        ("EWF", "EWFP"),
        ("OCF", "OCFP"),
        ("PCF", "PCFP"),
        ("PTC", "PTCP"),
        ("DPA", "DPAP"),
        ("ILA", "ILAP"),
    )

    @classmethod
    def get_wallet_pairs(cls) -> tuple[tuple[str, str], ...]:
        return cls.WALLET_PAIRS

    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "user_funds_collection.log"

    @classmethod
    def validate(cls) -> None:
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")

        if not cls.WALLET_PAIRS:
            raise ValueError("At least one wallet pair must be configured.")

        user_codes = []
        system_codes = []

        for user_code, system_code in cls.WALLET_PAIRS:
            if not user_code or not system_code:
                raise ValueError("Wallet codes must not be empty.")

            if user_code == system_code:
                raise ValueError("User and system wallet codes must differ.")

            user_codes.append(user_code)
            system_codes.append(system_code)

        if len(user_codes) != len(set(user_codes)):
            raise ValueError("User wallet codes must be unique.")

        if len(system_codes) != len(set(system_codes)):
            raise ValueError("System wallet codes must be unique.")
