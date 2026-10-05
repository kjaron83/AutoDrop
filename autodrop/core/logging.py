"""Configurable structured and file-based logging system for AutoDrop."""

from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Any, Callable
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from autodrop.core.config import Settings, settings

logger = logging.getLogger("autodrop")


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the specified record as a JSON object string.

        Args:
            record: The log record to format.

        Returns:
            str: JSON formatted log record.
        """
        log_payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_payload["stack_info"] = self.formatStack(record.stack_info)

        # Extract extra fields added via extra={...}
        standard_keys = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }
        extra_data = {
            k: v for k, v in record.__dict__.items() if k not in standard_keys and not k.startswith("_")
        }
        if extra_data:
            log_payload["extra"] = extra_data

        return json.dumps(log_payload, default=str)


class TextFormatter(logging.Formatter):
    """Formats log records as human-readable standard text strings."""

    DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
    ) -> None:
        """Initializes the TextFormatter.

        Args:
            fmt: Optional log format string.
            datefmt: Optional date format string.
        """
        super().__init__(
            fmt=fmt or self.DEFAULT_FORMAT,
            datefmt=datefmt or self.DEFAULT_DATEFMT,
        )


def setup_logging(
    app_settings: Settings | None = None,
) -> logging.Logger:
    """Configures application-wide logging based on settings.

    Args:
        app_settings: Optional Settings instance. If None, the global settings are used.

    Returns:
        logging.Logger: The configured application logger ('autodrop').
    """
    active_settings = app_settings if app_settings is not None else settings

    log_level = getattr(logging, active_settings.LOG_LEVEL.upper(), logging.INFO)

    # Determine formatter
    formatter: logging.Formatter
    if active_settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Configure autodrop logger
    app_logger = logging.getLogger("autodrop")
    app_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplication on re-configuration
    for handler in list(app_logger.handlers):
        app_logger.removeHandler(handler)
        handler.close()

    # StreamHandler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    app_logger.addHandler(stream_handler)

    # RotatingFileHandler if LOG_FILE is configured
    if active_settings.LOG_FILE:
        log_path = Path(active_settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=active_settings.LOG_MAX_BYTES,
            backupCount=active_settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)

    app_logger.propagate = True
    return app_logger


class UnhandledExceptionLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that catches and logs unhandled 500 exceptions with full request context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processes incoming requests and logs unhandled exceptions.

        Args:
            request: The incoming HTTP request.
            call_next: Next ASGI handler in chain.

        Returns:
            Response: The HTTP response.
        """
        try:
            return await call_next(request)
        except Exception as exc:
            client_ip = request.client.host if request.client else "unknown"
            query_str = str(request.query_params)
            url_path = request.url.path
            method = request.method

            logger.error(
                f"Unhandled exception during {method} {url_path} (client: {client_ip}): {exc}",
                exc_info=True,
                extra={
                    "http_method": method,
                    "http_path": url_path,
                    "client_host": client_ip,
                    "query_params": query_str,
                },
            )

            try:
                from autodrop.core.templates import templates

                return templates.TemplateResponse(
                    request=request,
                    name="errors/500.html",
                    context={"current_user": getattr(request.state, "current_user", None)},
                    status_code=500,
                )
            except Exception:
                return HTMLResponse(
                    content="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>500 - Internal Server Error</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
    <h1>500 - Internal Server Error</h1>
    <p>An unexpected error occurred. Please try again later.</p>
</body>
</html>""",
                    status_code=500,
                )
