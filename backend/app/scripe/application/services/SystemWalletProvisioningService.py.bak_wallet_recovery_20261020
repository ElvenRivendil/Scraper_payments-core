# /* payments-core/backend/app/scripe/application/services/SystemWalletProvisioningService.py */
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountType, Currency


class SystemWalletProvisioningService:
    SYSTEM_OWNER_ID = UUID("d5f4a08f-e37c-4b30-818c-65144a28ebf1")
    CURRENCY_CODE = "SCR"

    SYSTEM_WALLETS = (
        ("ERP", "Emergency Reserve Account"),
        ("ISP", "Investment Savings Account"),
        ("PMP", "Pocket Money Account"),
        ("BDP", "Bonus Department Account"),
        ("SYAP", "Staking Yield Account"),
        ("ITFP", "Internal Transfer Fee Account"),
        ("EWFP", "Emergency Reserve Deposit and Withdrawal Fee Account"),
        ("OCFP", "Order Open and Close Fee Account"),
        ("PCFP", "Position Open and Close Fee Account"),
        ("PTCP", "Profit Trade Commission Account"),
        ("DPAP", "Discount Plan Payment Account"),
        ("ILAP", "Identity Ledger Payment Account"),
        ("RVAP", "Reserve Account"),
        ("14PR", "Reserved System Account 14"),
        ("15PR", "Reserved System Account 15"),
        ("16PR", "Reserved System Account 16"),
        ("SCAP", "System Consolidation Account"),
        ("SPAP", "Staking Pool Account"),
        ("WRAP", "Website Revenue Account"),
        ("20PR", "Reserved System Account 20"),
        ("21PR", "Reserved System Account 21"),
        ("22PR", "Reserved System Account 22"),
        ("23PR", "Reserved System Account 23"),
        ("24PR", "Reserved System Account 24"),
        ("25PR", "Reserved System Account 25"),
    )

    def provision(self, session: Session) -> list[Account]:
        with session.begin():
            currency_exists = session.scalar(
                select(Currency.code).where(Currency.code == self.CURRENCY_CODE)
            )
            if currency_exists is None:
                raise RuntimeError("Required system-wallet currency SCR is missing.")

            existing_accounts = session.scalars(
                select(Account)
                .where(
                    Account.owner_id == self.SYSTEM_OWNER_ID,
                    Account.wallet_code.in_(
                        [code for code, _ in self.SYSTEM_WALLETS]
                    ),
                )
                .with_for_update()
            ).all()
            existing_by_code = {
                account.wallet_code: account for account in existing_accounts
            }

            for code, name in self.SYSTEM_WALLETS:
                account = existing_by_code.get(code)
                if account is None:
                    continue
                if (
                    account.name != name
                    or account.currency_code != self.CURRENCY_CODE
                    or account.type != AccountType.USER
                    or account.owner_id != self.SYSTEM_OWNER_ID
                    or not account.is_system
                ):
                    raise RuntimeError(
                        f"System wallet {code} exists with conflicting properties."
                    )

            for code, name in self.SYSTEM_WALLETS:
                if code in existing_by_code:
                    continue
                session.add(
                    Account(
                        owner_id=self.SYSTEM_OWNER_ID,
                        name=name,
                        wallet_code=code,
                        currency_code=self.CURRENCY_CODE,
                        type=AccountType.USER,
                        is_system=True,
                    )
                )

            session.flush()
            result = session.scalars(
                select(Account)
                .where(
                    Account.owner_id == self.SYSTEM_OWNER_ID,
                    Account.wallet_code.in_(
                        [code for code, _ in self.SYSTEM_WALLETS]
                    ),
                )
                .order_by(Account.wallet_code)
            ).all()

            if len(result) != len(self.SYSTEM_WALLETS):
                raise RuntimeError(
                    f"Expected 25 system wallets, found {len(result)}."
                )

            return result
