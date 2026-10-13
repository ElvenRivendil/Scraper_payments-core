# /* ../NauTrader_Helm/payments-core/backend/app/core/auth.py */
from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: UUID
    is_active: bool = True


def require_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    authorization_header = request.headers.get("authorization")

    if credentials is None:
        if authorization_header:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request.state.public_demo = True
        return AuthenticatedUser(id=UUID(int=0))

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = request.app.state.settings
    url = f"{settings.helm_auth_base_url.rstrip('/')}/api/v1/users/me"

    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=3.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Helm authentication service is unavailable",
        ) from None

    if response.status_code in (400, 401, 403, 404):
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive Helm user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from Helm authentication service",
        )

    try:
        payload = response.json()
        user_id = UUID(str(payload["id"]))
        is_active = payload["is_active"]
        if is_active is not True:
            raise ValueError("inactive user")
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=502,
            detail="Invalid user response from Helm authentication service",
        ) from None

    request.state.public_demo = False
    return AuthenticatedUser(id=user_id, is_active=True)
