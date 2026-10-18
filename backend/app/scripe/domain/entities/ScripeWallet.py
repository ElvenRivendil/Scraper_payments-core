# /* payments-core/backend/app/scripe/domain/entities/ScripeWallet.py */
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScripeWallet:
    code: str
    name: str
    position: int

    @classmethod
    def standard_wallets(cls) -> tuple["ScripeWallet", ...]:
        return (
            cls(code="ER", name="Emergency Reserve", position=1),
            cls(code="IS", name="Investment Savings", position=2),
            cls(code="PM", name="Pocket Money", position=3),
            cls(code="BD", name="Bonus Department", position=4),
            cls(code="SYA", name="Staking Yield Account", position=5),
            cls(code="ITF", name="Internal Transfer Fee Account", position=6),
            cls(code="EWF", name="ER Deposit & Withdrawal Fee Account", position=7),
            cls(code="OCF", name="Order Open & Close Fee Account", position=8),
            cls(code="PCF", name="Position Open & Close Fee Account", position=9),
            cls(code="PTC", name="Profit Trade Commission Account", position=10),
            cls(code="DPA", name="Discount Plan Payment Account", position=11),
            cls(code="ILA", name="Identity Ledger Payment Account", position=12),
            cls(code="RVA", name="Reserve Account", position=13),
        )
