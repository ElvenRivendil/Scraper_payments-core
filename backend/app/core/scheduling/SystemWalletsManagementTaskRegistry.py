# /* ../NauTrader_Helm/payments-core/backend/app/core/scheduling/SystemWalletsManagementTaskRegistry.py */
from typing import Any


class SystemWalletsManagementTaskRegistry:
    STATE_KEY_PREFIX = "payments_core:system_wallets_management:schedule"
    USER_FUNDS_TASK_ID = "user-funds-collection"
    SYSTEM_FUNDS_TASK_ID = "system-funds-consolidation"
    SYSTEM_FUNDS_DISTRIBUTION_TASK_ID = "system-funds-distribution"
    SYSTEM_WALLETS_AGGREGATION_TASK_ID = "system-wallets-aggregation"
    SYSTEM_WALLETS_DISTRIBUTION_TO_SYA_TASK_ID = "system-wallets-distribution-to-sya"
    TASK_DEFAULTS: dict[str, dict[str, Any]] = {
        USER_FUNDS_TASK_ID: {
            "schedule_name": "user-funds-collection-hourly-probe",
            "task_name": "payments_core.user_funds_collection_schedule_probe",
            "minute": 5,
        },
        SYSTEM_FUNDS_TASK_ID: {
            "schedule_name": "system-funds-consolidation-hourly",
            "task_name": "payments_core.system_funds_consolidation_hourly",
            "minute": 15,
        },
        SYSTEM_FUNDS_DISTRIBUTION_TASK_ID: {
            "schedule_name": "system-funds-distribution-hourly",
            "task_name": "payments_core.system_funds_distribution_hourly",
            "minute": 10,
            "enabled": True,
        },
        SYSTEM_WALLETS_AGGREGATION_TASK_ID: {
            "schedule_name": "system-wallets-aggregation-hourly",
            "task_name": "payments_core.system_wallets_aggregation_hourly",
            "minute": 0,
            "enabled": True,
        },
        SYSTEM_WALLETS_DISTRIBUTION_TO_SYA_TASK_ID: {
            "schedule_name": "system-wallets-distribution-to-sya-hourly",
            "task_name": "payments_core.system_wallets_distribution_to_sya_hourly",
            "minute": 20,
            "enabled": True,
        },
    }
