# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/application/services/SystemWalletsManagementConfigService.py */
from app.api.system_wallets_management.domain.models.SystemWalletsManagementConfigResponse import (
    SystemWalletsManagementConfigResponse,
    SystemWalletsManagementTaskConfig,
)
from app.services.SystemFundsConsolidation.domain.config.ManyToOneConfig import (
    ManyToOneConfig,
)
from app.services.SystemFundsConsolidation.domain.config.SystemFundsDistributionConfig import (
    SystemFundsDistributionConfig,
)
from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import (
    UserFundsCollectionConfig,
)
from app.services.SystemWalletsAggregation.domain.config.SystemWalletsAggregationConfig import (
    SystemWalletsAggregationConfig,
)
from app.api.system_wallets_management.application.services.SystemWalletsManagementScheduleState import (
    SystemWalletsManagementScheduleState,
)
from app.api.system_wallets_management.application.services.SystemFundsDistributionSharesState import (
    SystemFundsDistributionSharesState,
)
from app.core.scheduling.SystemWalletsManagementTaskRegistry import (
    SystemWalletsManagementTaskRegistry,
)


class SystemWalletsManagementConfigService:
    USER_FUNDS_TASK_ID = SystemWalletsManagementTaskRegistry.USER_FUNDS_TASK_ID
    SYSTEM_FUNDS_TASK_ID = SystemWalletsManagementTaskRegistry.SYSTEM_FUNDS_TASK_ID
    SYSTEM_FUNDS_DISTRIBUTION_TASK_ID = SystemWalletsManagementTaskRegistry.SYSTEM_FUNDS_DISTRIBUTION_TASK_ID
    SYSTEM_WALLETS_AGGREGATION_TASK_ID = SystemWalletsManagementTaskRegistry.SYSTEM_WALLETS_AGGREGATION_TASK_ID

    def __init__(self) -> None:
        self.schedule_state = SystemWalletsManagementScheduleState()
        self.distribution_shares_state = SystemFundsDistributionSharesState()

    def get_config(self) -> SystemWalletsManagementConfigResponse:
        return SystemWalletsManagementConfigResponse(
            tasks=[
                self._user_funds_config(),
                self._system_funds_config(),
                self._system_funds_distribution_config(),
                self._system_wallets_aggregation_config(),
            ]
        )

    @staticmethod
    def _schedule_description(enabled: bool, minute: int) -> str:
        if not enabled:
            return "Disabled"
        return f"Hourly at minute {minute:02d} UTC"

    def _user_funds_config(self) -> SystemWalletsManagementTaskConfig:
        state = self.schedule_state.get_state(self.USER_FUNDS_TASK_ID)
        enabled = bool(state["enabled"])
        minute = int(state["schedule_minute_utc"])
        pairs = UserFundsCollectionConfig.get_wallet_pairs()
        return SystemWalletsManagementTaskConfig(
            task_id=self.USER_FUNDS_TASK_ID,
            task_name="User Funds Collection",
            description=(
                "Collects funds from each active user's configured wallet "
                "into the corresponding system wallet."
            ),
            operation="One-to-one user funds collection",
            schedule=self._schedule_description(enabled, minute),
            schedule_minute_utc=minute,
            enabled=enabled,
            currency_code=UserFundsCollectionConfig.CURRENCY_CODE,
            source_wallet_codes=[source for source, _ in pairs],
            destination_wallet_codes=[destination for _, destination in pairs],
            fee_status="not_configured",
            fee=None,
        )

    def _system_funds_distribution_config(self) -> SystemWalletsManagementTaskConfig:
        config = SystemFundsDistributionConfig
        shares = self.distribution_shares_state.get_shares()
        state = self.schedule_state.get_state(self.SYSTEM_FUNDS_DISTRIBUTION_TASK_ID)
        enabled = bool(state["enabled"])
        minute = int(state["schedule_minute_utc"])
        return SystemWalletsManagementTaskConfig(
            task_id=self.SYSTEM_FUNDS_DISTRIBUTION_TASK_ID,
            task_name="System Funds Distribution",
            description=(
                "Distributes available SCR balance from SCAP to SPAP and WRAP "
                "using configured proportional shares."
            ),
            operation="One-to-many system funds distribution",
            schedule=self._schedule_description(enabled, minute),
            schedule_minute_utc=minute,
            enabled=enabled,
            currency_code=config.CURRENCY_CODE,
            source_wallet_codes=[config.SOURCE_WALLET_CODE],
            destination_wallet_codes=list(config.DESTINATION_WALLET_CODES),
            destination_shares=[
                {"wallet_code": code, "percentage": shares[code]}
                for code in config.DESTINATION_WALLET_CODES
            ],
            fee_status="not_configured",
            fee=None,
        )

    def _system_wallets_aggregation_config(self) -> SystemWalletsManagementTaskConfig:
        config = SystemWalletsAggregationConfig
        state = self.schedule_state.get_state(self.SYSTEM_WALLETS_AGGREGATION_TASK_ID)
        enabled = bool(state["enabled"])
        minute = int(state["schedule_minute_utc"])
        pairs = config.get_wallet_pairs()
        return SystemWalletsManagementTaskConfig(
            task_id=self.SYSTEM_WALLETS_AGGREGATION_TASK_ID,
            task_name="System Wallets Aggregation",
            description=(
                "Aggregates available SCR balances from each configured "
                "system wallet into its corresponding paired wallet."
            ),
            operation="System wallets aggregation",
            schedule=self._schedule_description(enabled, minute),
            schedule_minute_utc=minute,
            enabled=enabled,
            currency_code=config.CURRENCY_CODE,
            source_wallet_codes=[source for source, _ in pairs],
            destination_wallet_codes=[destination for _, destination in pairs],
            fee_status="not_configured",
            fee=None,
        )

    def _system_funds_config(self) -> SystemWalletsManagementTaskConfig:
        config = ManyToOneConfig
        state = self.schedule_state.get_state(self.SYSTEM_FUNDS_TASK_ID)
        enabled = bool(state["enabled"])
        minute = int(state["schedule_minute_utc"])
        return SystemWalletsManagementTaskConfig(
            task_id=self.SYSTEM_FUNDS_TASK_ID,
            task_name="System Funds Consolidation",
            description=(
                "Transfers available balances from configured source system "
                "wallets into the destination system wallet."
            ),
            operation="Many-to-one system funds consolidation",
            schedule=self._schedule_description(enabled, minute),
            schedule_minute_utc=minute,
            enabled=enabled,
            currency_code=config.CURRENCY_CODE,
            source_wallet_codes=list(config.SOURCE_WALLET_CODES),
            destination_wallet_codes=[config.DESTINATION_WALLET_CODE],
            fee_status="not_configured",
            fee=None,
        )
