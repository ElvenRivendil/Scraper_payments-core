# /* payments-core/backend/app/scripe/domain/entities/ScripeCurrency.py */
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScripeCurrency:
    code: str = "SCR"
    minor_unit: int = 8

    def __post_init__(self) -> None:
        if self.code != "SCR":
            raise ValueError("Scripe currency code must be SCR")
        if self.minor_unit != 8:
            raise ValueError("Scripe currency must use exactly 8 decimal places")
