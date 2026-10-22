# /* ../NauTrader_Helm/payments-core/backend/app/services/ProfitableClosedTradeExecutionFees/application/operations/ResolveProfitableClosedTradeFeeWalletsOperation.py */
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account
from app.models.enums import AccountType
from app.services.ProfitableClosedTradeExecutionFees.domain.config.ProfitableClosedTradeExecutionFeesConfig import (
    ProfitableClosedTradeExecutionFeesConfig as Config,
)


class ResolveProfitableClosedTradeFeeWalletsOperation:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        user_id: UUID,
    ) -> tuple[Account, Account]:
        Config.validate()
        accounts = session.execute(
            select(Account).where(
                Account.owner_id == user_id,
                Account.wallet_code.in_(
                    (Config.SOURCE_WALLET_CODE, Config.TARGET_WALLET_CODE)
                ),
                Account.currency_code == Config.CURRENCY_CODE,
                Account.is_system.is_(False),
                Account.is_demo.is_(False),
            )
        ).scalars().all()
        accounts_by_code = {account.wallet_code: account for account in accounts}
        source = accounts_by_code.get(Config.SOURCE_WALLET_CODE)
        destination = accounts_by_code.get(Config.TARGET_WALLET_CODE)

        if source is None or destination is None:
            raise LookupError("Required user fee wallets were not found.")
        if source.type != AccountType.USER or destination.type != AccountType.USER:
            raise ValueError("Both fee wallets must be user accounts.")
        if source.id == destination.id:
            raise ValueError("Fee source and destination wallets must differ.")

        return source, destination
