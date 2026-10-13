# /* payments-core/backend/tests/support/AuthenticatedTestUserDependency.py */
from uuid import UUID

from fastapi import Request

from app.core.auth import AuthenticatedUser


class AuthenticatedTestUserDependency:
    def __init__(self, user_id: UUID = UUID(int=1)) -> None:
        self.user_id = user_id

    def __call__(self, request: Request) -> AuthenticatedUser:
        request.state.public_demo = False
        return AuthenticatedUser(id=self.user_id)
