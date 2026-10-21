# /* ../NauTrader_Helm/payments-core/backend/app/core/execution_logging/ServiceExecutionLogger.py */
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Self


class ServiceExecutionLogger:
    def __init__(
        self,
        *,
        service_name: str,
        log_file: str | Path,
        console_logger: logging.Logger | None = None,
    ) -> None:
        self.service_name = service_name
        requested_log_file = Path(log_file)
        self.log_file = (
            requested_log_file
            if requested_log_file.is_absolute()
            else Path(__file__).resolve().parents[3] / requested_log_file
        )
        self.console_logger = console_logger or logging.getLogger(__name__)
        self.started_at: datetime | None = None
        self.duration_seconds = 0.0
        self.errors_count = 0
        self.status: str | None = None
        self._started_counter: float | None = None
        self._file_logger = logging.getLogger(f"{__name__}.{id(self)}")
        self._file_logger.setLevel(logging.INFO)
        self._file_logger.propagate = False
        self._handler: logging.FileHandler | None = None
        self._file_error: OSError | None = None
        self._finished = False

    def __enter__(self) -> Self:
        self.started_at = datetime.now(UTC)
        self._started_counter = perf_counter()
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._handler = logging.FileHandler(
                self.log_file,
                mode="a",
                encoding="utf-8",
            )
            self._handler.setFormatter(logging.Formatter("%(message)s"))
            self._file_logger.addHandler(self._handler)
        except OSError as exc:
            self._file_error = exc
            self.console_logger.exception(
                "Execution log file unavailable; continuing without file logging: %s",
                self.log_file,
            )
        self._write(
            logging.INFO,
            f"START service={self.service_name} "
            f"started_at={self.started_at.isoformat(timespec='milliseconds')}",
        )
        return self

    def record_event(self, message: str) -> None:
        details = f"EVENT message={self._single_line(message)}"
        self._write(logging.INFO, details)
        if self._file_error is not None:
            self.console_logger.info("%s", details)

    def record_error(
        self,
        message: str,
        *,
        exception: Exception | None = None,
    ) -> None:
        self.errors_count += 1
        details = f"ERROR message={self._single_line(message)}"
        if exception is not None:
            details += (
                f" exception_type={type(exception).__name__}"
                f" exception={self._single_line(str(exception))}"
            )
        self._write(logging.ERROR, details)
        if self._file_error is not None:
            self.console_logger.error("%s", details)

    def set_status(self, status: str) -> None:
        self.status = status

    def finish(self) -> None:
        if self._finished:
            return
        if self.started_at is None or self._started_counter is None:
            raise RuntimeError("Execution logger has not been started.")

        self.duration_seconds = perf_counter() - self._started_counter
        if self.status is None:
            self.status = (
                "completed_with_errors"
                if self.errors_count
                else "completed"
            )

        finished_at = datetime.now(UTC)
        self._write(
            logging.INFO,
            f"FINISH service={self.service_name} "
            f"started_at={self.started_at.isoformat(timespec='milliseconds')} "
            f"finished_at={finished_at.isoformat(timespec='milliseconds')} "
            f"duration_seconds={self.duration_seconds:.3f} "
            f"status={self.status} errors={self.errors_count}",
        )
        self._finished = True

        if self._handler is not None:
            self._file_logger.removeHandler(self._handler)
            self._handler.close()
            self._handler = None

        self.console_logger.info(
            "Execution summary: started_at=%s duration_seconds=%.3f "
            "status=%s errors=%s file_logging=%s log_file=%s",
            self.started_at.isoformat(timespec="milliseconds"),
            self.duration_seconds,
            self.status,
            "yes" if self.errors_count else "no",
            "available" if self._handler is None and self._file_error is None else "unavailable",
            self.log_file,
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> bool:
        if exc_value is not None:
            self.record_error(
                "Unhandled execution exception",
                exception=exc_value if isinstance(exc_value, Exception) else None,
            )
            self.set_status("failed")
        self.finish()
        return False

    def _write(self, level: int, message: str) -> None:
        if self._handler is None or self._file_error is not None:
            return
        self._file_logger.log(
            level,
            "%s %s",
            datetime.now(UTC).isoformat(timespec="milliseconds"),
            message,
        )

    @staticmethod
    def _single_line(value: str) -> str:
        return " ".join(value.split())
