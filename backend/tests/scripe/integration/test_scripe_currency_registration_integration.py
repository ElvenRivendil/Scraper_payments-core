# /* payments-core/backend/tests/scripe/integration/test_scripe_currency_registration_integration.py */
from sqlalchemy import select

from app.models import Currency
from app.scripe.application.services.ScripeCurrencyRegistrationService import (
    ScripeCurrencyRegistrationService,
)


class TestScripeCurrencyRegistrationIntegration:
    def test_registers_scr_with_eight_decimal_places(self, app) -> None:
        with app.state.session_factory() as session:
            currency = ScripeCurrencyRegistrationService.register(session)
            assert currency.code == "SCR"
            assert currency.minor_unit == 8

    def test_registration_is_idempotent(self, app) -> None:
        with app.state.session_factory() as session:
            first = ScripeCurrencyRegistrationService.register(session)
            second = ScripeCurrencyRegistrationService.register(session)
            currencies = session.execute(
                select(Currency).where(Currency.code == "SCR")
            ).scalars().all()

            assert first.code == second.code == "SCR"
            assert len(currencies) == 1
