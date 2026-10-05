"""Unit and integration tests for the configurable logging system."""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from autodrop.core.config import Settings
from autodrop.core.logging import (
    JSONFormatter,
    TextFormatter,
    UnhandledExceptionLoggingMiddleware,
    setup_logging,
)


def test_logging_configuration_defaults():
    """Verifies default settings for the logging system."""
    settings = Settings()
    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FORMAT == "text"
    assert settings.LOG_FILE is None
    assert settings.LOG_MAX_BYTES == 10_485_760
    assert settings.LOG_BACKUP_COUNT == 5


def test_text_formatter():
    """Verifies TextFormatter formatting."""
    formatter = TextFormatter()
    record = logging.LogRecord(
        name="autodrop.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=42,
        msg="Test warning message: %s",
        args=("sample",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "[WARNING]" in formatted
    assert "[autodrop.test]" in formatted
    assert "Test warning message: sample" in formatted


def test_json_formatter():
    """Verifies JSONFormatter produces valid structured JSON with all metadata."""
    formatter = JSONFormatter()

    try:
        raise ValueError("Simulated failure for json test")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="autodrop.test_json",
        level=logging.ERROR,
        pathname=__file__,
        lineno=50,
        msg="Database query error",
        args=(),
        exc_info=exc_info,
    )
    record.custom_tag = "auth_event"

    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "autodrop.test_json"
    assert payload["message"] == "Database query error"
    assert "timestamp" in payload
    assert "ValueError: Simulated failure for json test" in payload["exception"]
    assert payload["extra"]["custom_tag"] == "auth_event"


def test_setup_logging_stream_handler(caplog):
    """Verifies setup_logging sets up stdout StreamHandler with correct level."""
    test_settings = Settings(
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="text",
        LOG_FILE=None,
    )
    app_logger = setup_logging(test_settings)
    assert app_logger.level == logging.DEBUG
    assert len(app_logger.handlers) == 1
    assert isinstance(app_logger.handlers[0], logging.StreamHandler)
    assert isinstance(app_logger.handlers[0].formatter, TextFormatter)

    with caplog.at_level(logging.DEBUG, logger="autodrop"):
        app_logger.debug("Debug event message")


def test_setup_logging_with_rotating_file_handler(tmp_path: Path):
    """Verifies setup_logging creates file handler and writes logs to rotating file."""
    log_file = tmp_path / "nested_dir" / "test_app.log"
    test_settings = Settings(
        LOG_LEVEL="INFO",
        LOG_FORMAT="json",
        LOG_FILE=str(log_file),
        LOG_MAX_BYTES=1024,
        LOG_BACKUP_COUNT=3,
    )

    app_logger = setup_logging(test_settings)
    assert len(app_logger.handlers) == 2  # StreamHandler + RotatingFileHandler

    file_handlers = [h for h in app_logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    fh = file_handlers[0]
    assert fh.maxBytes == 1024
    assert fh.backupCount == 3
    assert isinstance(fh.formatter, JSONFormatter)

    app_logger.info("Structured file log test message")
    fh.flush()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8").strip()
    entry = json.loads(content)
    assert entry["level"] == "INFO"
    assert entry["message"] == "Structured file log test message"

    # Cleanup handler
    for h in list(app_logger.handlers):
        app_logger.removeHandler(h)
        h.close()


def test_unhandled_exception_logging_middleware(caplog):
    """Verifies that unhandled exceptions are caught, logged with traceback and metadata, and return 500."""
    test_app = FastAPI()
    test_app.add_middleware(UnhandledExceptionLoggingMiddleware)

    @test_app.get("/trigger-error")
    def trigger_error(request: Request):
        raise RuntimeError("Something went catastrophically wrong!")

    test_client = TestClient(test_app)

    with caplog.at_level(logging.ERROR, logger="autodrop"):
        response = test_client.get("/trigger-error?ref=test_param")

    assert response.status_code == 500
    assert "500" in response.text

    assert any(
        "Unhandled exception during GET /trigger-error" in record.getMessage()
        for record in caplog.records
    )
    assert "RuntimeError: Something went catastrophically wrong!" in caplog.text
