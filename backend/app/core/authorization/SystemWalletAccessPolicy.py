# /* ../NauTrader_Helm/payments-core/backend/app/core/authorization/SystemWalletAccessPolicy.py */
from fastapi import HTTPException
from app.core.auth import AuthenticatedUser


class SystemWalletAccessPolicy:
    REQUIRED_ROLE = "SUPER_ADMIN"

    def require_access(self, current_user: AuthenticatedUser) -> None:
        if not current_user.is_active or current_user.effective_role != self.REQUIRED_ROLE:
            raise HTTPException(
                status_code=403,
                detail="SUPER_ADMIN role is required to access system wallets",
            )
