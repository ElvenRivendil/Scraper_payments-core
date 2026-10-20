# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/services/SystemFundsConsolidationWalletValidator.py */
from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountType
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)
from app.services.SystemFundsConsolidation.domain.errors.SystemFundsConsolidationWalletValidationError import (
    SystemFundsConsolidationWalletValidationError,
)


class SystemFundsConsolidationWalletValidator:
    @staticmethod
    def lock_required_wallets(
        session: Session,
        wallet_codes: Iterable[str],
        *,
        currency_code: str,
    ) -> dict[str, Account]:
        required_codes = tuple(wallet_codes)
        if not required_codes:
            raise SystemFundsConsolidationWalletValidationError(
                "At least one system wallet is required."
            )
        if any(not code for code in required_codes):
            raise SystemFundsConsolidationWalletValidationError(
                "System wallet codes must not be empty."
            )
        if len(required_codes) != len(set(required_codes)):
            raise SystemFundsConsolidationWalletValidationError(
                "System wallet codes must be unique."
            )

        statement = (
            select(Account)
            .where(
                Account.owner_id == SystemWalletProvisioningService.SYSTEM_OWNER_ID,
                Account.wallet_code.in_(required_codes),
            )
            .order_by(Account.wallet_code, Account.id)
            .with_for_update()
        )
        accounts = session.scalars(statement).all()
        accounts_by_code: dict[str, Account] = {}
        for account in accounts:
            if account.wallet_code in accounts_by_code:
                raise SystemFundsConsolidationWalletValidationError(
                    f"Duplicate system wallet: {account.wallet_code}."
                )
            accounts_by_code[account.wallet_code] = account

        missing_codes = sorted(set(required_codes) - set(accounts_by_code))
        if missing_codes:
            raise SystemFundsConsolidationWalletValidationError(
                f"Required system wallets are missing: {', '.join(missing_codes)}."
            )

        for code, account in accounts_by_code.items():
            if not account.is_system:
                raise SystemFundsConsolidationWalletValidationError(
                    f"Wallet {code} is not marked as a system wallet."
                )
            if account.type != AccountType.USER:
                raise SystemFundsConsolidationWalletValidationError(
                    f"System wallet {code} must have type USER."
                )
            if account.currency_code != currency_code:
                raise SystemFundsConsolidationWalletValidationError(
                    f"System wallet {code} has currency {account.currency_code}; "
                    f"expected {currency_code}."
                )

        return accounts_by_code
