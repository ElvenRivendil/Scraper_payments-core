# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsDistributionToSya/domain/config/SystemWalletsDistributionToSyaConfig.py */

class SystemWalletsDistributionToSyaConfig:
    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "system_wallets_distribution_to_sya.log"
    CURRENCY_CODE = "SCR"

    USER_SOURCE_WALLET_CODE = "ER"
    SYSTEM_TOTAL_WALLET_CODE = "ERP"
    SYSTEM_DISTRIBUTION_WALLET_CODE = "SPAP"
    USER_DESTINATION_WALLET_CODE = "SYA"

    @classmethod
    def validate(cls) -> None:
        wallet_codes = (
            cls.USER_SOURCE_WALLET_CODE,
            cls.SYSTEM_TOTAL_WALLET_CODE,
            cls.SYSTEM_DISTRIBUTION_WALLET_CODE,
            cls.USER_DESTINATION_WALLET_CODE,
        )
        if any(not code for code in wallet_codes):
            raise ValueError("Wallet codes must not be empty.")
        if len(wallet_codes) != len(set(wallet_codes)):
            raise ValueError("Wallet codes must be unique.")
        if not cls.CURRENCY_CODE:
            raise ValueError("Currency code must not be empty.")
