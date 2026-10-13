# /* payments-core/backend/app/scripe/application/services/ScripeWalletProvisioningService.py */
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account, AccountType, Currency
from app.scripe.domain.entities.ScripeWallet import ScripeWallet


class ScripeWalletProvisioningService:
    @classmethod
    def provision(cls, session: Session, owner_id: UUID) -> list[dict]:
        if session.get(Currency, "SCR") is None:
            raise ValueError("SCR currency is not registered")

        wallets = ScripeWallet.standard_wallets()
        wallet_codes = tuple(wallet.code for wallet in wallets)
        statement = select(Account).where(
            Account.owner_id == owner_id,
            Account.wallet_code.in_(wallet_codes),
        )
        existing = {
            account.wallet_code: account
            for account in session.execute(statement).scalars().all()
        }

        for wallet in wallets:
            if wallet.code not in existing:
                session.add(
                    Account(
                        owner_id=owner_id,
                        name=wallet.name,
                        currency_code="SCR",
                        type=AccountType.USER,
                        wallet_code=wallet.code,
                    )
                )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing_codes = set(
                session.execute(
                    select(Account.wallet_code).where(
                        Account.owner_id == owner_id,
                        Account.wallet_code.in_(wallet_codes),
                    )
                ).scalars().all()
            )
            if not set(wallet_codes).issubset(existing_codes):
                raise

        accounts = session.execute(
            select(Account).where(
                Account.owner_id == owner_id,
                Account.wallet_code.in_(wallet_codes),
            )
        ).scalars().all()
        accounts_by_code = {account.wallet_code: account for account in accounts}

        if not set(wallet_codes).issubset(accounts_by_code):
            raise RuntimeError("SCR wallet provisioning did not create all standard wallets")

        return [
            {
                "id": str(accounts_by_code[wallet.code].id),
                "owner_id": str(owner_id),
                "wallet_code": wallet.code,
                "name": wallet.name,
                "currency_code": "SCR",
            }
            for wallet in wallets
        ]
