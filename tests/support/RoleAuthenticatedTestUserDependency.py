# /* ../NauTrader_Helm/payments-core/tests/support/RoleAuthenticatedTestUserDependency.py */
from uuid import UUID

from fastapi import Request

from app.core.auth import AuthenticatedUser


class RoleAuthenticatedTestUserDependency:
    def __init__(
        self,
        effective_role: str,
        user_id: UUID = UUID(int=1),
    ) -> None:
        self.effective_role = effective_role
        self.user_id = user_id

    def __call__(self, request: Request) -> AuthenticatedUser:
        request.state.public_demo = False
        return AuthenticatedUser(
            id=self.user_id,
            is_active=True,
            effective_role=self.effective_role,
        )
