"""
TripMate AI - Structured Logging System
Supports JSON formatted logs, request ID correlation via contextvars,
and sensitive data masking.
"""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from app.config import settings

# Context variable to hold request_id across async coroutines
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="system"
)
agent_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "agent_id", default="none"
)


class StructuredJsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with timestamp, level, request_id,
    and arbitrary extra context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "agent_id": agent_id_ctx.get(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Include extra attributes attached to the record
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Sanitize secrets if any keys resemble passwords or tokens
            sanitized = {
                k: ("[REDACTED]" if any(secret in k.lower() for secret in ["key", "secret", "password", "token"]) else v)
                for k, v in record.extra_data.items()
            }
            log_record["data"] = sanitized

        return json.dumps(log_record)


def setup_logging() -> None:
    """Configures root and application loggers based on app settings."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicate lines
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(StructuredJsonFormatter())
    else:
        text_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [req:%(request_id)s] %(message)s",
            defaults={"request_id": "system"},
        )
        console_handler.setFormatter(text_formatter)

    root_logger.addHandler(console_handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance with the given name."""
    return logging.getLogger(name)

