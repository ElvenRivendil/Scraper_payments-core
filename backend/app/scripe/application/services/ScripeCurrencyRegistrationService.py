# /* payments-core/backend/app/scripe/application/services/ScripeCurrencyRegistrationService.py */
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Currency
from app.scripe.domain.entities.ScripeCurrency import ScripeCurrency


class ScripeCurrencyRegistrationService:
    @classmethod
    def register(cls, session: Session) -> Currency:
        currency_definition = ScripeCurrency()
        currency = session.get(Currency, currency_definition.code)
        if currency is not None:
            if currency.minor_unit != currency_definition.minor_unit:
                raise ValueError(
                    "Existing SCR currency has an unexpected minor-unit precision"
                )
            return currency

        session.add(
            Currency(
                code=currency_definition.code,
                minor_unit=currency_definition.minor_unit,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            currency = session.get(Currency, currency_definition.code)
            if currency is None:
                raise
            if currency.minor_unit != currency_definition.minor_unit:
                raise ValueError(
                    "Existing SCR currency has an unexpected minor-unit precision"
                )
            return currency

        return session.get(Currency, currency_definition.code)
