# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/application/services/OrderPositionExecutionFeesControlService.py */
from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig,
)


class OrderPositionExecutionFeesControlService:
    SERVICE_NAME = "order-position-execution-fees"
    _lock = Lock()

    def __init__(self) -> None:
        backend_root = Path(__file__).resolve().parents[5]
        self.state_file = (
            backend_root
            / OrderPositionExecutionFeeConfig.LOG_DIRECTORY
            / "order_position_execution_fees_state.json"
        )

    def get_state(self) -> dict[str, object]:
        with self._lock:
            if not self.state_file.exists():
                return {"service_name": self.SERVICE_NAME, "enabled": True}
            try:
                state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {"service_name": self.SERVICE_NAME, "enabled": True}
            if not isinstance(state, dict) or not isinstance(state.get("enabled"), bool):
                return {"service_name": self.SERVICE_NAME, "enabled": True}
            return {"service_name": self.SERVICE_NAME, "enabled": state["enabled"]}

    def set_enabled(self, enabled: bool) -> dict[str, object]:
        with self._lock:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_file = self.state_file.with_suffix(".tmp")
            payload = {"service_name": self.SERVICE_NAME, "enabled": enabled}
            temporary_file.write_text(
                json.dumps(payload, ensure_ascii=True),
                encoding="utf-8",
            )
            os.replace(temporary_file, self.state_file)
            return payload

    def is_enabled(self) -> bool:
        return bool(self.get_state()["enabled"])
