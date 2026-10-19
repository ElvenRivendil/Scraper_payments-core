# /* ../NauTrader_Helm/payments-core/backend/app/services/UserFundsCollection/application/services/UserFundsCollectionService.py */
from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountType
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)
from app.schemas import TransferCreate
from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import (
    UserFundsCollectionConfig,
)
from app.services.balances import account_balances_minor
from app.services.transfers import create_transfer

logger = logging.getLogger(__name__)


class UserFundsCollectionService:
    IDEMPOTENCY_SCOPE = "user_funds_collection.hourly"
    DESCRIPTION_PREFIX = "Hourly user funds collection"

    @classmethod
    def collect_for_user(
        cls,
        session: Session,
        user_id: UUID,
        *,
        collection_hour: datetime,
        minimum_transfer_minor: int = 1,
    ) -> dict[str, int]:
        if collection_hour.tzinfo is None:
            raise ValueError("collection_hour must be timezone-aware.")
        if minimum_transfer_minor < 1:
            raise ValueError("minimum_transfer_minor must be positive.")

        UserFundsCollectionConfig.validate()
        system_owner_id = SystemWalletProvisioningService.SYSTEM_OWNER_ID
        pairs = UserFundsCollectionConfig.get_wallet_pairs()
        expected_codes = {
            code
            for pair in pairs
            for code in pair
        }

        with session.begin():
            accounts = session.execute(
                select(Account)
                .where(
                    (
                        (Account.owner_id == user_id)
                        & Account.wallet_code.in_(
                            [user_code for user_code, _ in pairs]
                        )
                    )
                    | (
                        (Account.owner_id == system_owner_id)
                        & Account.wallet_code.in_(
                            [system_code for _, system_code in pairs]
                        )
                    )
                )
                .order_by(Account.wallet_code, Account.id)
                .with_for_update()
            ).scalars().all()

            accounts_by_key = {
                (account.owner_id, account.wallet_code): account
                for account in accounts
            }

            expected_accounts = {
                (user_id, user_code): (
                    user_code,
                    False,
                )
                for user_code, _ in pairs
            }
            expected_accounts.update(
                {
                    (system_owner_id, system_code): (
                        system_code,
                        True,
                    )
                    for _, system_code in pairs
                }
            )

            if len(accounts_by_key) != len(expected_accounts):
                raise ValueError(
                    f"User {user_id} has missing or duplicate collection accounts."
                )

            for key, (wallet_code, is_system) in expected_accounts.items():
                account = accounts_by_key.get(key)
                if account is None:
                    raise ValueError(
                        f"Required collection account is missing: {wallet_code}."
                    )
                if (
                    account.wallet_code != wallet_code
                    or account.currency_code != UserFundsCollectionConfig.CURRENCY_CODE
                    or account.is_system is not is_system
                    or account.type != AccountType.USER
                ):
                    raise ValueError(
                        f"Collection account validation failed: {wallet_code}."
                    )

            prelocked_accounts = {
                account.id: account
                for account in accounts
            }
            transferred: dict[str, int] = {}
            hour_key = collection_hour.astimezone(UTC).strftime("%Y%m%dT%H")

            for user_code, system_code in pairs:
                source = accounts_by_key[(user_id, user_code)]
                destination = accounts_by_key[(system_owner_id, system_code)]
                _posted, _held, available = account_balances_minor(
                    session,
                    source.id,
                )

                if available < minimum_transfer_minor:
                    continue

                idempotency_key = (
                    f"ufc:{user_id}:{user_code}:{system_code}:{hour_key}"
                )
                result = create_transfer(
                    session,
                    idempotency_key=idempotency_key,
                    transfer=TransferCreate(
                        from_account_id=source.id,
                        to_account_id=destination.id,
                        amount_minor=available,
                        currency_code=UserFundsCollectionConfig.CURRENCY_CODE,
                        description=(
                            f"{cls.DESCRIPTION_PREFIX} "
                            f"{user_code}->{system_code} {hour_key}"
                        ),
                    ),
                    owner_id=user_id,
                    scope=cls.IDEMPOTENCY_SCOPE,
                    request_payload={
                        "user_id": str(user_id),
                        "source_wallet": user_code,
                        "destination_wallet": system_code,
                        "amount_minor": available,
                        "currency_code": UserFundsCollectionConfig.CURRENCY_CODE,
                        "collection_hour": hour_key,
                    },
                    commit=False,
                    prelocked_accounts=prelocked_accounts,
                )
                if result.created:
                    transferred[user_code] = available

        logger.info(
            "User funds collection completed: user_id=%s hour=%s wallets_transferred=%s",
            user_id,
            collection_hour.astimezone(UTC).strftime("%Y%m%dT%H"),
            len(transferred),
        )
        return transferred
