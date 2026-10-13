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
        )
