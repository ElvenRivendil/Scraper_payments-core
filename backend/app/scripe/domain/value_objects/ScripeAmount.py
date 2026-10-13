# /* payments-core/backend/app/scripe/domain/value_objects/ScripeAmount.py */
from decimal import Decimal, InvalidOperation


class ScripeAmount:
    MINOR_UNIT = 8
    MINOR_UNITS_PER_SCR = 100_000_000

    @classmethod
    def to_minor_units(cls, amount: Decimal | str | int) -> int:
        if isinstance(amount, bool) or isinstance(amount, float):
            raise TypeError("Amount must be Decimal, str, or int; float is not supported")
        try:
            decimal_amount = Decimal(amount)
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid SCR amount") from exc
        if not decimal_amount.is_finite():
            raise ValueError("SCR amount must be finite")
        scaled_amount = decimal_amount * cls.MINOR_UNITS_PER_SCR
        if scaled_amount != scaled_amount.to_integral_value():
            raise ValueError("SCR amount exceeds 8 decimal places")
        return int(scaled_amount)

    @classmethod
    def from_minor_units(cls, amount_minor: int) -> Decimal:
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int):
            raise TypeError("Minor units must be an integer")
        return Decimal(amount_minor).scaleb(-cls.MINOR_UNIT)

    @classmethod
    def format(cls, amount_minor: int) -> str:
        return f"{cls.from_minor_units(amount_minor):.{cls.MINOR_UNIT}f}"
