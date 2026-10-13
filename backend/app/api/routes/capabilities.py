from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.schemas import CapabilitiesOut, DashboardStatsOut
from app.services.reconciliation import dashboard_stats

router = APIRouter(tags=["capabilities"])


@router.get("/capabilities", response_model=CapabilitiesOut)
def read_capabilities(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_current_user),
):
    settings = request.app.state.settings
    public_read_only = bool(request.state.public_demo)
    return {
        "public_demo": public_read_only,
        "read_only": public_read_only,
        "demo_endpoints_enabled": bool(settings.demo_endpoints_enabled),
        "writes_enabled": not public_read_only,
        "replay_enabled": not public_read_only,
        "reconcile_run_enabled": not public_read_only,
    }


@router.get("/stats", response_model=DashboardStatsOut)
def read_dashboard_stats(session: Session = Depends(get_db)):
    return dashboard_stats(session)
