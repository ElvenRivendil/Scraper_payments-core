# /* ../NauTrader_Helm/payments-core/backend/app/core/guards.py */
from __future__ import annotations

from fastapi import HTTPException, Request


def require_write_access(request: Request) -> None:
    if getattr(request.state, "public_demo", True):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PUBLIC_DEMO_READ_ONLY",
                "message": "This public demo is read-only",
            },
        )
