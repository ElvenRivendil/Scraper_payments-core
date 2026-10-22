# /* ../NauTrader_Helm/payments-core/backend/app/api/execution_fee_services/application/services/ExecutionFeeServiceControlService.py */
from __future__ import annotations
import json
import os
from pathlib import Path
from threading import Lock


class ExecutionFeeServiceControlService:
    _lock = Lock()

    def __init__(self, *, service_name: str, log_directory: str) -> None:
        self.service_name = service_name
        backend_root = Path(__file__).resolve().parents[5]
        state_filename = f"{service_name.replace('-', '_')}_state.json"
        self.state_file = backend_root / log_directory / state_filename

    def get_state(self) -> dict[str, object]:
        with self._lock:
            if not self.state_file.exists():
                return {"service_name": self.service_name, "enabled": True}
            try:
                state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {"service_name": self.service_name, "enabled": True}
            if not isinstance(state, dict) or not isinstance(state.get("enabled"), bool):
                return {"service_name": self.service_name, "enabled": True}
            return {"service_name": self.service_name, "enabled": state["enabled"]}

    def set_enabled(self, enabled: bool) -> dict[str, object]:
        with self._lock:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_file = self.state_file.with_suffix(".tmp")
            payload = {"service_name": self.service_name, "enabled": enabled}
            temporary_file.write_text(
                json.dumps(payload, ensure_ascii=True),
                encoding="utf-8",
            )
            os.replace(temporary_file, self.state_file)
            return payload

    def is_enabled(self) -> bool:
        return bool(self.get_state()["enabled"])
