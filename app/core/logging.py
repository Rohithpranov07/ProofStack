"""Centralized structured logging for ProofStack.

All engines and services should import `logger` (standard Python logger)
or `structured_log` (JSON-style dict emitter) from this module.

Usage:
    from app.core.logging import logger, structured_log

    logger.info("plain text message")          # traditional
    structured_log("engine_complete", run_id="abc", engine="github", duration_ms=312)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("proofstack")

_struct_logger = logging.getLogger("proofstack.structured")
_struct_handler = logging.StreamHandler()
_struct_handler.setFormatter(logging.Formatter("%(message)s"))
_struct_logger.addHandler(_struct_handler)
_struct_logger.propagate = False
_struct_logger.setLevel(logging.INFO)


def structured_log(event: str, *, level: str = "info", **fields: Any) -> None:
    """Emit a single-line JSON log entry for observability.

    Example output:
        {"event": "engine_complete", "run_id": "abc", "engine": "github", "duration_ms": 312}
    """
    payload: dict[str, Any] = {"event": event, **fields}
    line = json.dumps(payload, default=str)
    getattr(_struct_logger, level, _struct_logger.info)(line)


class TimerContext:
    """Context-manager that records elapsed wall-clock milliseconds.

    Usage:
        timer = TimerContext()
        with timer:
            await some_work()
        print(timer.elapsed_ms)  # e.g. 312
    """

    def __init__(self) -> None:
        self.elapsed_ms: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> "TimerContext":
        self._start = time.monotonic()
        return self

    def __exit__(self, *_: Any) -> None:
        self.elapsed_ms = round((time.monotonic() - self._start) * 1000, 1)
