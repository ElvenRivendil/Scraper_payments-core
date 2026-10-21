# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/operations/ResolveUserFeeWalletsOperation.py */

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account
from app.models.enums import AccountType
from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig as Config,
)


class ResolveUserFeeWalletsOperation:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
        destination_wallet_code: str,
    ) -> tuple[Account, Account]:
        wallet_codes = (
            Config.SYSTEM_SOURCE_WALLET_CODE,
            destination_wallet_code,
        )
        accounts = session.execute(
            select(Account).where(
                Account.owner_id == user_id,
                Account.wallet_code.in_(wallet_codes),
                Account.currency_code == Config.CURRENCY_CODE,
                Account.is_system.is_(False),
                Account.is_demo.is_(False),
            )
        ).scalars().all()
        accounts_by_code = {account.wallet_code: account for account in accounts}
        missing_codes = set(wallet_codes) - set(accounts_by_code)
        if missing_codes:
            raise ValueError(
                f"Required user fee wallets are missing: {', '.join(sorted(missing_codes))}."
            )
        source = accounts_by_code[Config.SYSTEM_SOURCE_WALLET_CODE]
        destination = accounts_by_code[destination_wallet_code]
        if source.type != AccountType.USER or destination.type != AccountType.USER:
            raise ValueError("Execution fee wallets must have USER account type.")
        if source.id == destination.id:
            raise ValueError("Execution fee source and destination wallets must differ.")
        return source, destination
