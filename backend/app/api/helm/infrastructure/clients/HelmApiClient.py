# /* ../NauTrader_Helm/payments-core/backend/app/api/helm/infrastructure/clients/HelmApiClient.py */
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException


class HelmApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 3.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_user_tariffs(self, authorization: str) -> dict[str, Any]:
        return self._get("/api/user-tariffs", authorization)

    def get_user_tariff_entity(
        self,
        authorization: str,
        entity_key: str,
    ) -> dict[str, Any]:
        return self._get(f"/api/user-tariffs/{entity_key}", authorization)

    def _get(self, path: str, authorization: str) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers={"Authorization": authorization},
                timeout=self.timeout,
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail="Helm tariff service timed out",
            ) from None
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="Helm tariff service is unavailable",
            ) from None

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Helm user tariff profile or entity not found",
            )
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=401,
                detail="Helm rejected user authorization",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Unexpected response from Helm tariff service",
            )

        try:
            payload = response.json()
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail="Invalid JSON response from Helm tariff service",
            ) from None

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=502,
                detail="Invalid response from Helm tariff service",
            )

        return payload
