# /* ../NauTrader_Helm/payments-core/tests/services/UserFundsCollection/application/services/integration/user_funds_collection_atomicity_integration.py */
from datetime import UTC, datetime
from uuid import UUID
from unittest.mock import patch
import importlib

import pytest
from sqlalchemy import select

from app.models import (
    Account,
    LedgerEntry,
    LedgerEntryDirection,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from app.scripe.application.services.ScripeCurrencyRegistrationService import (
    ScripeCurrencyRegistrationService,
)
from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)
from app.services.UserFundsCollection.application.services.UserFundsCollectionService import (
    UserFundsCollectionService,
)
from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import (
    UserFundsCollectionConfig,
)
from app.services.balances import account_balances_minor

collection_module = importlib.import_module(
    "app.services.UserFundsCollection.application.services.UserFundsCollectionService"
)


class TestUserFundsCollectionAtomicityIntegration:
    @staticmethod
    def _prepare_accounts(app, user_id: UUID) -> dict[str, Account]:
        with app.state.session_factory() as session:
            ScripeCurrencyRegistrationService.register(session)

        with app.state.session_factory() as session:
            SystemWalletProvisioningService().provision(session)

        with app.state.session_factory() as session:
            ScripeWalletProvisioningService.provision(session, user_id)
            accounts = session.execute(
                select(Account).where(
                    Account.owner_id.in_(
                        [user_id, SystemWalletProvisioningService.SYSTEM_OWNER_ID]
                    )
                )
            ).scalars().all()
            return {
                f"{account.owner_id}:{account.wallet_code}": account
                for account in accounts
            }

    @staticmethod
    def _credit_user_wallet(
        app,
        *,
        user_id: UUID,
        account_id: UUID,
        wallet_code: str,
        amount_minor: int,
    ) -> None:
        with app.state.session_factory() as session:
            transaction = Transaction(
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.POSTED,
                currency_code="SCR",
                idempotency_key=f"ufc-test-credit:{user_id}:{wallet_code}",
                description="User funds collection test fixture",
            )
            session.add(transaction)
            session.flush()
            session.add(
                LedgerEntry(
                    tx_id=transaction.id,
                    account_id=account_id,
                    currency_code="SCR",
                    direction=LedgerEntryDirection.CREDIT,
                    amount=amount_minor,
                )
            )
            session.commit()

    def test_collects_available_balances_and_is_idempotent(self, app) -> None:
        user_id = UUID(int=91001)
        accounts = self._prepare_accounts(app, user_id)
        collection_hour = datetime(2026, 10, 19, 12, tzinfo=UTC)
        pairs = UserFundsCollectionConfig.get_wallet_pairs()

        for user_code, _ in pairs:
            account = accounts[f"{user_id}:{user_code}"]
            self._credit_user_wallet(
                app,
                user_id=user_id,
                account_id=account.id,
                wallet_code=user_code,
                amount_minor=1000,
            )

        with app.state.session_factory() as session:
            first_result = UserFundsCollectionService.collect_for_user(
                session, user_id, collection_hour=collection_hour
            )

        assert first_result == {user_code: 1000 for user_code, _ in pairs}

        with app.state.session_factory() as session:
            second_result = UserFundsCollectionService.collect_for_user(
                session, user_id, collection_hour=collection_hour
            )

        assert second_result == {}

        with app.state.session_factory() as session:
            transactions = session.execute(
                select(Transaction).where(
                    Transaction.idempotency_key.like(f"ufc:{user_id}:%")
                )
            ).scalars().all()
            assert len(transactions) == 7

            source_ids = [
                accounts[f"{user_id}:{user_code}"].id
                for user_code, _ in pairs
            ]
            debit_entries = session.execute(
                select(LedgerEntry).where(
                    LedgerEntry.direction == LedgerEntryDirection.DEBIT,
                    LedgerEntry.account_id.in_(source_ids),
                    LedgerEntry.tx_id.in_(
                        [transaction.id for transaction in transactions]
                    ),
                )
            ).scalars().all()
            assert len(debit_entries) == 7

    def test_rolls_back_entire_user_package_when_a_transfer_fails(self, app) -> None:
        user_id = UUID(int=91002)
        accounts = self._prepare_accounts(app, user_id)
        collection_hour = datetime(2026, 10, 19, 13, tzinfo=UTC)
        pairs = UserFundsCollectionConfig.get_wallet_pairs()

        for user_code, _ in pairs:
            account = accounts[f"{user_id}:{user_code}"]
            self._credit_user_wallet(
                app,
                user_id=user_id,
                account_id=account.id,
                wallet_code=user_code,
                amount_minor=1000,
            )

        original_create_transfer = collection_module.create_transfer
        calls = 0

        def fail_on_third_transfer(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("Simulated transfer failure")
            return original_create_transfer(*args, **kwargs)

        with app.state.session_factory() as session:
            with patch.object(
                collection_module,
                "create_transfer",
                side_effect=fail_on_third_transfer,
            ):
                with pytest.raises(RuntimeError, match="Simulated transfer failure"):
                    UserFundsCollectionService.collect_for_user(
                        session, user_id, collection_hour=collection_hour
                    )

        with app.state.session_factory() as session:
            transactions = session.execute(
                select(Transaction).where(
                    Transaction.idempotency_key.like(f"ufc:{user_id}:%")
                )
            ).scalars().all()
            assert transactions == []

            for user_code, _ in pairs:
                account = accounts[f"{user_id}:{user_code}"]
                _, _, available = account_balances_minor(session, account.id)
                assert available == 1000
