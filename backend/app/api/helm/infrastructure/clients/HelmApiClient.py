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

    def get_active_user_ids(self, internal_secret: str) -> list[UUID]:
        if not internal_secret:
            raise RuntimeError("Helm internal API secret is not configured")

        user_ids: list[UUID] = []
        skip = 0
        limit = 500
        expected_count: int | None = None

        while expected_count is None or skip < expected_count:
            try:
                response = httpx.get(
                    f"{self.base_url}/api/internal/user-funds-collection/active-users",
                    headers={"X-Helm-Internal-Secret": internal_secret},
                    params={"skip": skip, "limit": limit},
                    timeout=self.timeout,
                )
            except httpx.TimeoutException:
                raise RuntimeError("Helm active-user request timed out") from None
            except httpx.RequestError:
                raise RuntimeError("Helm active-user service is unavailable") from None

            if response.status_code != 200:
                raise RuntimeError(
                    f"Helm active-user request failed with HTTP {response.status_code}"
                )

            try:
                payload = response.json()
            except ValueError:
                raise RuntimeError("Helm returned invalid JSON for active users") from None

            if not isinstance(payload, dict):
                raise RuntimeError("Helm returned an invalid active-user response")

            data = payload.get("data")
            count = payload.get("count")
            if (
                not isinstance(data, list)
                or isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
                or any(not isinstance(item, str) for item in data)
            ):
                raise RuntimeError("Helm returned an invalid active-user payload")

            try:
                page_ids = [UUID(item) for item in data]
            except ValueError:
                raise RuntimeError("Helm returned an invalid user UUID") from None

            if expected_count is None:
                expected_count = count
            elif count != expected_count:
                raise RuntimeError("Helm active-user count changed during pagination")

            expected_page_size = min(limit, expected_count - skip)
            if len(page_ids) != expected_page_size:
                raise RuntimeError("Helm returned an incomplete or oversized active-user page")
            if len(set(page_ids)) != len(page_ids):
                raise RuntimeError("Helm returned duplicate user IDs within a page")

            user_ids.extend(page_ids)
            skip += len(page_ids)

            if not page_ids and skip < expected_count:
                raise RuntimeError("Helm returned an incomplete active-user page")

        if len(user_ids) != expected_count or len(set(user_ids)) != len(user_ids):
            raise RuntimeError("Helm returned an incomplete or duplicate active-user list")

        return user_ids

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
