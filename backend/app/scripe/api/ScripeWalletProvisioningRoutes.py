# /* payments-core/backend/app/scripe/api/ScripeWalletProvisioningRoutes.py */
import hmac
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)


class ScripeWalletProvisioningRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/internal/scripe-wallets",
            tags=["internal-scripe-wallets"],
        )
        self.router.add_api_route(
            "/{owner_id}/provision",
            self.provision,
            methods=["POST"],
            status_code=200,
        )

    def provision(
        self,
        owner_id: UUID,
        request: Request,
        x_scripe_provisioning_secret: str | None = Header(default=None),
    ) -> list[dict]:
        configured_secret = request.app.state.settings.scripe_provisioning_secret
        if not configured_secret:
            raise HTTPException(
                status_code=503,
                detail="SCR wallet provisioning is not configured",
            )
        if not x_scripe_provisioning_secret or not hmac.compare_digest(
            x_scripe_provisioning_secret,
            configured_secret,
        ):
            raise HTTPException(status_code=403, detail="Invalid internal credentials")

        with request.app.state.session_factory() as session:
            try:
                return ScripeWalletProvisioningService.provision(session, owner_id)
            except ValueError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
