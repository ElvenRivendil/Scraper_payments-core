# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/config/OrderPositionExecutionFeeConfig.py */

class OrderPositionExecutionFeeConfig:
    CURRENCY_CODE = "SCR"
    TARIFF_ENTITY_KEY = "orders_positions_tariffs"
    ORDER_TARIFF_KEY = "orders"
    POSITION_TARIFF_KEY = "positions"

    # User-owned wallet configuration
    WALLET_OWNER_STRATEGY = "user_id"
    SYSTEM_SOURCE_WALLET_CODE = "IS"
    ORDER_FEE_WALLET_CODE = "OCF"
    POSITION_FEE_WALLET_CODE = "PCF"

    ORDER_WALLET_PAIR = (
        SYSTEM_SOURCE_WALLET_CODE,
        ORDER_FEE_WALLET_CODE,
    )
    POSITION_WALLET_PAIR = (
        SYSTEM_SOURCE_WALLET_CODE,
        POSITION_FEE_WALLET_CODE,
    )

    ORDER_IDEMPOTENCY_SCOPE = "order_execution_fee"
    POSITION_IDEMPOTENCY_SCOPE = "position_execution_fee"
    ORDER_IDEMPOTENCY_PREFIX = "order-execution-fee"
    POSITION_IDEMPOTENCY_PREFIX = "position-execution-fee"

    ORDER_DESCRIPTION_PREFIX = "Order execution fee"
    POSITION_DESCRIPTION_PREFIX = "Position opening fee"

    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "order_position_execution_fee.log"

    @classmethod
    def validate(cls) -> None:
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")

        if not cls.TARIFF_ENTITY_KEY:
            raise ValueError("Tariff entity key must not be empty.")

        tariff_keys = (
            cls.ORDER_TARIFF_KEY,
            cls.POSITION_TARIFF_KEY,
        )
        if any(not key for key in tariff_keys):
            raise ValueError("Tariff keys must not be empty.")
        if len(tariff_keys) != len(set(tariff_keys)):
            raise ValueError("Tariff keys must be unique.")

        wallet_codes = (
            cls.SYSTEM_SOURCE_WALLET_CODE,
            cls.ORDER_FEE_WALLET_CODE,
            cls.POSITION_FEE_WALLET_CODE,
        )
        if any(not code for code in wallet_codes):
            raise ValueError("Wallet codes must not be empty.")
        if len(wallet_codes) != len(set(wallet_codes)):
            raise ValueError("Wallet codes must be unique.")

        idempotency_values = (
            cls.ORDER_IDEMPOTENCY_SCOPE,
            cls.POSITION_IDEMPOTENCY_SCOPE,
            cls.ORDER_IDEMPOTENCY_PREFIX,
            cls.POSITION_IDEMPOTENCY_PREFIX,
        )
        if any(not value for value in idempotency_values):
            raise ValueError("Idempotency values must not be empty.")

        if not cls.LOG_DIRECTORY or not cls.LOG_FILENAME:
            raise ValueError("Log path settings must not be empty.")
