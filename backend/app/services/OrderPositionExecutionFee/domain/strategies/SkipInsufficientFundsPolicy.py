# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/strategies/SkipInsufficientFundsPolicy.py */

from app.services.transfers import TransferConflictError


class SkipInsufficientFundsPolicy:
    def handle(self, error: TransferConflictError) -> bool:
        return False
