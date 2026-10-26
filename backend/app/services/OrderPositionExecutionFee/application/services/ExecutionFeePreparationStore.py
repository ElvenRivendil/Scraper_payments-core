# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/services/ExecutionFeePreparationStore.py */
from collections import OrderedDict
from threading import RLock
from uuid import UUID

from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeePreparation import (
    ExecutionFeePreparation,
)


class ExecutionFeePreparationStore:
    MAX_ENTRIES = 10000
    _entries: OrderedDict[tuple[str, str, str, str], ExecutionFeePreparation] = OrderedDict()
    _lock = RLock()

    @classmethod
    def _key(
        cls,
        *,
        user_id: UUID,
        event_id: str,
        mode: str,
        fee_type: str,
    ) -> tuple[str, str, str, str]:
        normalized_event_id = event_id.strip()
        if not normalized_event_id:
            raise ValueError("Execution event ID must not be empty.")
        return str(user_id), normalized_event_id, mode, fee_type

    @classmethod
    def put(cls, preparation: ExecutionFeePreparation) -> None:
        key = cls._key(
            user_id=preparation.user_id,
            event_id=preparation.event_id,
            mode=preparation.mode,
            fee_type=preparation.fee_type,
        )
        with cls._lock:
            cls._entries[key] = preparation
            cls._entries.move_to_end(key)
            while len(cls._entries) > cls.MAX_ENTRIES:
                cls._entries.popitem(last=False)

    @classmethod
    def get(
        cls,
        *,
        user_id: UUID,
        event_id: str,
        mode: str,
        fee_type: str,
    ) -> ExecutionFeePreparation | None:
        key = cls._key(
            user_id=user_id,
            event_id=event_id,
            mode=mode,
            fee_type=fee_type,
        )
        with cls._lock:
            preparation = cls._entries.get(key)
            if preparation is not None:
                cls._entries.move_to_end(key)
            return preparation

    @classmethod
    def remove(
        cls,
        *,
        user_id: UUID,
        event_id: str,
        mode: str,
        fee_type: str,
    ) -> None:
        key = cls._key(
            user_id=user_id,
            event_id=event_id,
            mode=mode,
            fee_type=fee_type,
        )
        with cls._lock:
            cls._entries.pop(key, None)
