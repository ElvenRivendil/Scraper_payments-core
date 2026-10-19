# /* ../NauTrader_Helm/payments-core/backend/app/api/helm/api/HelmTariffRoutes.py */
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.helm.application.services.HelmTariffService import HelmTariffService
from app.api.helm.domain.models.HelmTariffResponse import HelmTariffResponse
from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.core.auth import AuthenticatedUser, require_current_user


class HelmTariffRoutes:
    ALLOWED_ENTITY_KEYS = frozenset({
        "orders_positions_tariffs",
        "profit_trade_commission",
        "position_collateral",
        "scr_transfers_profit_fees",
        "identitybook_subscription",
        "discount_plans",
    })

    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/helm/tariffs",
            tags=["helm-tariffs"],
        )
        self.router.add_api_route(
            "/me",
            self.get_user_tariffs,
            methods=["GET"],
            response_model=HelmTariffResponse,
        )
        self.router.add_api_route(
            "/me/{entity_key}",
            self.get_user_tariff_entity,
            methods=["GET"],
        )

    def get_user_tariffs(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> HelmTariffResponse:
        self._require_real_user(request, current_user)
        authorization = request.headers.get("authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Bearer token required")
        return self._service(request).get_user_tariffs(authorization)

    def get_user_tariff_entity(
        self,
        entity_key: str,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict:
        self._require_real_user(request, current_user)
        if entity_key not in self.ALLOWED_ENTITY_KEYS:
            raise HTTPException(
                status_code=404,
                detail="Unknown tariff entity",
            )
        authorization = request.headers.get("authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Bearer token required")
        return self._service(request).get_user_tariff_entity(
            authorization,
            entity_key,
        )

    @staticmethod
    def _require_real_user(
        request: Request,
        current_user: AuthenticatedUser,
    ) -> None:
        if current_user.id.int == 0 or getattr(request.state, "public_demo", False):
            raise HTTPException(
                status_code=401,
                detail="Authentication is required to access user tariffs",
            )

    @staticmethod
    def _service(request: Request) -> HelmTariffService:
        settings = request.app.state.settings
        client = HelmApiClient(
            base_url=settings.helm_auth_base_url,
        )
        return HelmTariffService(client)
