# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/SystemWalletAccountsService.py */
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, LedgerEntry
from app.scripe.application.services.SystemWalletProvisioningService import SystemWalletProvisioningService
from app.services.accounts import account_payload
from app.services.balances import account_balances_minor


class SystemWalletAccountsService:
    def _system_account_query(self):
        return select(Account).where(
            Account.owner_id == SystemWalletProvisioningService.SYSTEM_OWNER_ID,
            Account.is_system.is_(True),
            Account.currency_code == SystemWalletProvisioningService.CURRENCY_CODE,
        )

    def list_accounts(self, session: Session) -> list[dict]:
        accounts = session.scalars(
            self._system_account_query().order_by(Account.wallet_code)
        ).all()
        return [
            self._account_payload(session, account)
            for account in accounts
        ]

    def get_account(self, session: Session, account_id: UUID) -> dict | None:
        account = session.scalar(
            self._system_account_query().where(Account.id == account_id)
        )
        if account is None:
            return None
        return self._account_payload(session, account)

    def get_statement(
        self,
        session: Session,
        account_id: UUID,
        limit: int = 50,
    ) -> dict | None:
        account = session.scalar(
            self._system_account_query().where(Account.id == account_id)
        )
        if account is None:
            return None

        payload = self._account_payload(session, account)
        entries = session.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account.id)
            .order_by(LedgerEntry.created_at.desc(), LedgerEntry.id.desc())
            .limit(limit)
        ).all()

        return {
            "account": payload,
            "ledger_entries": [
                {
                    "id": entry.id,
                    "tx_id": entry.tx_id,
                    "account_id": entry.account_id,
                    "currency_code": entry.currency_code,
                    "direction": entry.direction.value,
                    "amount_minor": entry.amount,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ],
        }

    @staticmethod
    def _account_payload(session: Session, account: Account) -> dict:
        posted, held, _available = account_balances_minor(session, account.id)
        return account_payload(account, posted, held)
