# /* ../NauTrader_Helm/payments-core/backend/app/api/execution_fee_services/application/services/ExecutionFeeServiceLogService.py */
from pathlib import Path
from fastapi import HTTPException


class ExecutionFeeServiceLogService:
    def __init__(self, *, service_name: str, config: type) -> None:
        self.service_name = service_name
        self.log_file = Path(config.LOG_DIRECTORY) / config.LOG_FILENAME

    def get_logs(self, limit: int) -> dict[str, object]:
        if not self.log_file.exists():
            return {"service_name": self.service_name, "lines": []}
        try:
            lines = self.log_file.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to read service log",
            ) from exc
        return {"service_name": self.service_name, "lines": lines[-limit:]}

    def clear_logs(self) -> dict[str, object]:
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_file.write_text("", encoding="utf-8")
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to clear service log",
            ) from exc
        return {"service_name": self.service_name, "cleared": True}
