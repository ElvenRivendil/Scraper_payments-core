# /* ../NauTrader_Helm/payments-core/backend/app/services/demo_reset.py */
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    Account,
    Currency,
    Hold,
    LedgerEntry,
    LedgerEntryDirection,
    Transaction,
    TransactionStatus,
    TransactionType,
)


class DemoResetUnsafeError(RuntimeError):
    """Raised when demo data cannot be isolated safely."""


def reset_demo_data_safely(session: Session) -> None:
    currency_codes = ("INR", "USD", "EUR")
    expected_names = {
        f"{code} {suffix}"
        for code in currency_codes
        for suffix in (
            "Mint Source",
            "Treasury",
            "Alice Wallet",
            "Corner Shop",
            "Escrow",
        )
    }

    try:
        currencies = set(
            session.execute(
                select(Currency.code).where(Currency.code.in_(currency_codes))
            ).scalars()
        )
        if currencies != set(currency_codes):
            raise DemoResetUnsafeError(
                "Required demo currencies are missing; no data was changed."
            )

        accounts = list(
            session.execute(
                select(Account).where(
                    Account.name.in_(expected_names),
                    Account.is_demo.is_(True),
                    Account.is_system.is_(False),
                )
            ).scalars()
        )
        accounts_by_name = {account.name: account for account in accounts}
        if len(accounts) != len(expected_names) or set(accounts_by_name) != expected_names:
            raise DemoResetUnsafeError(
                "The expected isolated demo accounts were not found; no data was changed."
            )

        demo_account_ids = {account.id for account in accounts}
        demo_holds = list(
            session.execute(
                select(Hold).where(Hold.account_id.in_(demo_account_ids))
            ).scalars()
        )
        if demo_holds:
            raise DemoResetUnsafeError(
                "Demo accounts contain holds; no data was changed."
            )

        seed_keys = [f"seed:{code}:opening" for code in currency_codes]
        seed_transactions = list(
            session.execute(
                select(Transaction).where(
                    Transaction.idempotency_key.in_(seed_keys)
                )
            ).scalars()
        )
        transactions_by_key = {
            transaction.idempotency_key: transaction
            for transaction in seed_transactions
        }
        if len(seed_transactions) != len(seed_keys) or set(transactions_by_key) != set(seed_keys):
            raise DemoResetUnsafeError(
                "The exact opening seed transactions were not found; no data was changed."
            )

        transaction_ids = {transaction.id for transaction in seed_transactions}
        expected_entries = set()
        for code in currency_codes:
            transaction = transactions_by_key[f"seed:{code}:opening"]
            if (
                transaction.type != TransactionType.DEPOSIT
                or transaction.status != TransactionStatus.POSTED
                or transaction.currency_code != code
            ):
                raise DemoResetUnsafeError(
                    "An opening seed transaction has unexpected metadata; no data was changed."
                )
            expected_entries.add(
                (
                    transaction.id,
                    accounts_by_name[f"{code} Mint Source"].id,
                    code,
                    LedgerEntryDirection.DEBIT,
                    500000,
                )
            )
            expected_entries.add(
                (
                    transaction.id,
                    accounts_by_name[f"{code} Alice Wallet"].id,
                    code,
                    LedgerEntryDirection.CREDIT,
                    500000,
                )
            )

        demo_entries = list(
            session.execute(
                select(LedgerEntry).where(
                    LedgerEntry.account_id.in_(demo_account_ids)
                )
            ).scalars()
        )
        if {entry.tx_id for entry in demo_entries} != transaction_ids:
            raise DemoResetUnsafeError(
                "Demo accounts contain transactions outside the opening seed; no data was changed."
            )

        linked_entries = list(
            session.execute(
                select(LedgerEntry).where(
                    LedgerEntry.tx_id.in_(transaction_ids)
                )
            ).scalars()
        )
        actual_entries = {
            (
                entry.tx_id,
                entry.account_id,
                entry.currency_code,
                entry.direction,
                entry.amount,
            )
            for entry in linked_entries
        }
        if len(linked_entries) != len(expected_entries) or actual_entries != expected_entries:
            raise DemoResetUnsafeError(
                "Opening seed ledger entries do not match the expected demo balances; no data was changed."
            )

        external_holds = list(
            session.execute(
                select(Hold).where(
                    Hold.captured_tx_id.in_(transaction_ids),
                    Hold.account_id.not_in(demo_account_ids),
                )
            ).scalars()
        )
        if external_holds:
            raise DemoResetUnsafeError(
                "A demo transaction is referenced by a non-demo hold; no data was changed."
            )

        session.execute(
            delete(Hold).where(Hold.account_id.in_(demo_account_ids))
        )
        if transaction_ids:
            session.execute(
                delete(LedgerEntry).where(
                    LedgerEntry.tx_id.in_(transaction_ids)
                )
            )
            session.execute(
                delete(Transaction).where(Transaction.id.in_(transaction_ids))
            )

        for code in currency_codes:
            mint = accounts_by_name[f"{code} Mint Source"]
            alice = accounts_by_name[f"{code} Alice Wallet"]
            transaction = Transaction(
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.POSTED,
                currency_code=code,
                idempotency_key=f"seed:{code}:opening",
                description=f"Opening balance for {code} demo accounts",
            )
            session.add(transaction)
            session.flush()
            session.add_all(
                [
                    LedgerEntry(
                        tx_id=transaction.id,
                        account_id=mint.id,
                        currency_code=code,
                        direction=LedgerEntryDirection.DEBIT,
                        amount=500000,
                    ),
                    LedgerEntry(
                        tx_id=transaction.id,
                        account_id=alice.id,
                        currency_code=code,
                        direction=LedgerEntryDirection.CREDIT,
                        amount=500000,
                    ),
                ]
            )

        session.commit()
    except Exception:
        session.rollback()
        raise
