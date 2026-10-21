# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsDistributionToSya/application/services/SystemWalletsDistributionToSyaSnapshotReader.py */

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Account, AccountType
from app.services.balances import account_balances_minor
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)
from app.services.SystemWalletsDistributionToSya.domain.config.SystemWalletsDistributionToSyaConfig import (
    SystemWalletsDistributionToSyaConfig,
)


class SystemWalletsDistributionToSyaSnapshotReader:
    @classmethod
    def read_snapshot(
        cls,
        session: Session,
        user_ids: list[UUID],
    ) -> dict[str, Any]:
        config = SystemWalletsDistributionToSyaConfig
        config.validate()
        unique_user_ids = tuple(sorted(set(user_ids)))
        system_owner_id = SystemWalletProvisioningService.SYSTEM_OWNER_ID
        system_codes = (
            config.SYSTEM_TOTAL_WALLET_CODE,
            config.SYSTEM_DISTRIBUTION_WALLET_CODE,
        )
        user_wallet_condition = and_(
            Account.owner_id.in_(unique_user_ids),
            Account.wallet_code == config.USER_SOURCE_WALLET_CODE,
        )
        system_wallet_condition = and_(
            Account.owner_id == system_owner_id,
            Account.wallet_code.in_(system_codes),
        )
        with session.begin():
            accounts = session.scalars(
                select(Account)
                .where(or_(user_wallet_condition, system_wallet_condition))
                .order_by(Account.owner_id, Account.wallet_code, Account.id)
                .with_for_update()
            ).all()
            user_accounts: dict[UUID, Account] = {}
            system_accounts: dict[str, Account] = {}
            for account in accounts:
                if account.currency_code != config.CURRENCY_CODE:
                    raise ValueError(
                        f"Wallet {account.wallet_code} has unexpected currency."
                    )
                if account.type != AccountType.USER:
                    raise ValueError(
                        f"Wallet {account.wallet_code} must have type USER."
                    )
                if account.owner_id == system_owner_id:
                    if not account.is_system:
                        raise ValueError(
                            f"System wallet {account.wallet_code} is not marked as system."
                        )
                    if account.wallet_code in system_accounts:
                        raise ValueError(
                            f"Duplicate system wallet: {account.wallet_code}."
                        )
                    system_accounts[account.wallet_code] = account
                    continue
                if account.is_system or account.owner_id not in unique_user_ids:
                    raise ValueError(
                        f"User wallet {account.wallet_code} has invalid ownership."
                    )
                if account.owner_id in user_accounts:
                    raise ValueError(
                        f"Duplicate user wallet {account.wallet_code}."
                    )
                user_accounts[account.owner_id] = account
            missing_users = set(unique_user_ids) - set(user_accounts)
            if missing_users:
                raise ValueError(
                    f"Active users are missing ER wallets: {len(missing_users)}."
                )
            missing_system_wallets = set(system_codes) - set(system_accounts)
            if missing_system_wallets:
                raise ValueError(
                    "Required system wallets are missing: "
                    + ", ".join(sorted(missing_system_wallets))
                    + "."
                )
            user_balances = {
                owner_id: account_balances_minor(session, account.id)
                for owner_id, account in user_accounts.items()
            }
            system_balances = {
                wallet_code: account_balances_minor(session, account.id)
                for wallet_code, account in system_accounts.items()
            }
        return {
            "user_er_balances_minor": user_balances,
            "system_balances_minor": system_balances,
        }
