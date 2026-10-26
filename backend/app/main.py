from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.accounts import router as accounts_router
from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.currencies import router as currencies_router
from app.api.routes.demo import router as demo_router
from app.api.routes.dlq import router as dlq_router
from app.api.routes.health import router as health_router
from app.api.routes.holds import router as holds_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.reconcile import router as reconcile_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.transfers import router as transfers_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.auth import require_current_user
from app.core.config import Settings, get_settings
from app.core.db import create_engine_and_session
from app.core.logging import configure_logging
from app.core.metrics import HTTP_REQUESTS, refresh_runtime_gauges
from app.seed import seed_demo_data, seed_public_demo_data
from app.scripe.application.services.ScripeCurrencyRegistrationService import ScripeCurrencyRegistrationService
from app.scripe.api.ScripeWalletProvisioningRoutes import ScripeWalletProvisioningRoutes
from app.scripe.api.ScripeWalletOperationsRoutes import ScripeWalletOperationsRoutes
from app.scripe.api.ScripeSyaWithdrawalRoutes import ScripeSyaWithdrawalRoutes
from app.scripe.api.SystemWalletAccountsRoutes import SystemWalletAccountsRoutes
from app.api.helm.api.HelmTariffRoutes import HelmTariffRoutes
from app.api.system_wallets_management.api.SystemWalletsManagementRoutes import SystemWalletsManagementRoutes
from app.api.order_position_execution_fees.api.OrderPositionExecutionFeesRoutes import OrderPositionExecutionFeesRoutes
from app.api.order_position_execution_fees.api.InternalOrderPositionExecutionFeesRoutes import (
    InternalOrderPositionExecutionFeesRoutes,
)
from app.api.position_percent_value_execution_fees.api.PositionPercentValueExecutionFeesRoutes import PositionPercentValueExecutionFeesRoutes
from app.api.profitable_closed_trade_execution_fees.api.ProfitableClosedTradeExecutionFeesRoutes import ProfitableClosedTradeExecutionFeesRoutes
from app.api.profitable_closed_trade_execution_fees.api.InternalProfitableClosedTradeExecutionFeesRoutes import (
    InternalProfitableClosedTradeExecutionFeesRoutes,
)
from app.features.transfers.api.TransferRoutes import TransferRoutes


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    engine, session_factory = create_engine_and_session(settings.database_url)

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def record_http_metrics(request: Request, call_next):
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = route.path if route is not None else request.url.path
        HTTP_REQUESTS.labels(request.method, route_path, str(response.status_code)).inc()
        return response

    @app.on_event("startup")
    def on_startup() -> None:
        with session_factory() as session:
            should_seed_on_empty = settings.app_env.lower() == "production" and settings.auto_seed_on_empty
            if should_seed_on_empty:
                seed_public_demo_data(session)
            elif settings.auto_seed:
                seed_demo_data(session)
            ScripeCurrencyRegistrationService.register(session)
            refresh_runtime_gauges(session)

    @app.get("/", tags=["health"])
    def read_root():
        return {
            "service": settings.app_name,
            "status": "ok",
            "docs": "/docs",
            "health": "/health",
            "capabilities": "/capabilities",
            "metrics": "/metrics",
        }

    app.include_router(ScripeWalletProvisioningRoutes().router)
    app.include_router(ScripeWalletOperationsRoutes().router)
    app.include_router(ScripeSyaWithdrawalRoutes().router)
    app.include_router(SystemWalletAccountsRoutes().router)
    app.include_router(HelmTariffRoutes().router)
    app.include_router(SystemWalletsManagementRoutes().router)
    app.include_router(OrderPositionExecutionFeesRoutes().router)
    app.include_router(InternalOrderPositionExecutionFeesRoutes().router)
    app.include_router(PositionPercentValueExecutionFeesRoutes().router)
    app.include_router(ProfitableClosedTradeExecutionFeesRoutes().router)
    app.include_router(InternalProfitableClosedTradeExecutionFeesRoutes().router)
    app.include_router(TransferRoutes().router)
    app.include_router(health_router)
    app.include_router(capabilities_router)
    app.include_router(accounts_router, dependencies=[Depends(require_current_user)])
    app.include_router(currencies_router)
    app.include_router(holds_router, dependencies=[Depends(require_current_user)])
    app.include_router(transfers_router, dependencies=[Depends(require_current_user)])
    app.include_router(transactions_router, dependencies=[Depends(require_current_user)])
    app.include_router(webhooks_router, dependencies=[Depends(require_current_user)])
    app.include_router(dlq_router, dependencies=[Depends(require_current_user)])
    app.include_router(reconcile_router, dependencies=[Depends(require_current_user)])
    app.include_router(demo_router, dependencies=[Depends(require_current_user)])
    app.include_router(metrics_router, dependencies=[Depends(require_current_user)])

    return app


app = create_app()
