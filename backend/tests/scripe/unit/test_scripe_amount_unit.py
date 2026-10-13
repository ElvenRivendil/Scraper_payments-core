# /* payments-core/backend/tests/scripe/unit/test_scripe_amount_unit.py */
from decimal import Decimal

import pytest

from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount


class TestScripeAmountUnit:
    def test_converts_whole_scr_to_minor_units(self) -> None:
        assert ScripeAmount.to_minor_units("1") == 100_000_000

    def test_converts_eight_decimal_places_exactly(self) -> None:
        assert ScripeAmount.to_minor_units("1.12345678") == 112_345_678

    def test_converts_minor_units_to_decimal(self) -> None:
        assert ScripeAmount.from_minor_units(112_345_678) == Decimal("1.12345678")

    def test_formats_exactly_eight_decimal_places(self) -> None:
        assert ScripeAmount.format(1) == "0.00000001"
        assert ScripeAmount.format(100_000_000) == "1.00000000"

    def test_rejects_more_than_eight_decimal_places(self) -> None:
        with pytest.raises(ValueError, match="exceeds 8 decimal places"):
            ScripeAmount.to_minor_units("0.000000001")

    def test_rejects_float_values(self) -> None:
        with pytest.raises(TypeError, match="float is not supported"):
            ScripeAmount.to_minor_units(0.1)

    def test_rejects_non_finite_values(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            ScripeAmount.to_minor_units("NaN")
