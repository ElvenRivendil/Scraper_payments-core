# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/domain/config/ParameterizedExecutionFeeConfig.py */


class ParameterizedExecutionFeeConfig:
    CURRENCY_CODE = "SCR"

    # Tariff resolution is configured after the existing tariff contract is inspected.
    TARIFF_ENTITY_KEY = None
    TARIFF_KEY = None
    TARIFF_RESOLVER_STRATEGY = None

    # Concrete services must define wallet ownership and wallet codes.
    WALLET_OWNER_STRATEGY = "user_id"
    SOURCE_WALLET_CODE = None
    TARGET_WALLET_CODE = None

    IDEMPOTENCY_SCOPE = None
    IDEMPOTENCY_PREFIX = None
    DESCRIPTION_PREFIX = None

    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "parameterized_execution_fee.log"

    @classmethod
    def validate(cls) -> None:
        if not isinstance(cls.TARIFF_ENTITY_KEY, str) or not cls.TARIFF_ENTITY_KEY.strip():
            raise ValueError("Tariff entity key must not be empty.")
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")

        if not cls.WALLET_OWNER_STRATEGY:
            raise ValueError("Wallet owner strategy must not be empty.")

        wallet_codes = (
            cls.SOURCE_WALLET_CODE,
            cls.TARGET_WALLET_CODE,
        )
        if any(not code for code in wallet_codes):
            raise ValueError("Source and target wallet codes must not be empty.")
        if len(wallet_codes) != len(set(wallet_codes)):
            raise ValueError("Source and target wallet codes must be different.")

        idempotency_values = (
            cls.IDEMPOTENCY_SCOPE,
            cls.IDEMPOTENCY_PREFIX,
        )
        if any(not value for value in idempotency_values):
            raise ValueError("Idempotency settings must not be empty.")

        if not cls.DESCRIPTION_PREFIX:
            raise ValueError("Description prefix must not be empty.")

        if not cls.LOG_DIRECTORY or not cls.LOG_FILENAME:
            raise ValueError("Log path settings must not be empty.")
