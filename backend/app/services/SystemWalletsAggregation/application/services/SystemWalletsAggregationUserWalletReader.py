# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsAggregation/application/services/SystemWalletsAggregationUserWalletReader.py */

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountType
from app.services.SystemWalletsAggregation.domain.config.SystemWalletsAggregationConfig import (
    SystemWalletsAggregationConfig,
)
from app.services.balances import account_balances_minor


class SystemWalletsAggregationUserWalletReader:
    @classmethod
    def read_snapshot(
        cls,
        session: Session,
        user_ids: list[UUID],
        *,
        wallet_code: str,
    ) -> dict[UUID, tuple[int, int, int]]:
        SystemWalletsAggregationConfig.validate()
        source_code, _destination_code = (
            SystemWalletsAggregationConfig.get_wallet_pair(wallet_code)
        )
        unique_user_ids = tuple(sorted(set(user_ids)))
        if not unique_user_ids:
            return {}

        with session.begin():
            accounts = session.scalars(
                select(Account)
                .where(
                    Account.owner_id.in_(unique_user_ids),
                    Account.wallet_code == source_code,
                )
                .order_by(Account.owner_id, Account.id)
                .with_for_update()
            ).all()

            snapshot: dict[UUID, tuple[int, int, int]] = {}
            for account in accounts:
                if account.owner_id is None:
                    raise ValueError(
                        f"User wallet {source_code} has no owner."
                    )
                if account.owner_id not in unique_user_ids:
                    raise ValueError(
                        f"User wallet {source_code} has an unexpected owner."
                    )
                if (
                    account.wallet_code != source_code
                    or account.currency_code
                    != SystemWalletsAggregationConfig.CURRENCY_CODE
                    or account.is_system
                    or account.type != AccountType.USER
                ):
                    raise ValueError(
                        f"User wallet validation failed: {source_code}."
                    )
                if account.owner_id in snapshot:
                    raise ValueError(
                        f"Duplicate user wallet: {source_code}."
                    )
                snapshot[account.owner_id] = account_balances_minor(
                    session,
                    account.id,
                )

        return snapshot
