# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/strategies/RejectInsufficientFundsPolicy.py */

from app.services.transfers import TransferConflictError


class RejectInsufficientFundsPolicy:
    def handle(self, error: TransferConflictError) -> bool:
        raise error
