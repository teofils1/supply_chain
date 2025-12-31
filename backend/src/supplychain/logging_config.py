"""
Structured logging configuration using structlog.

This module provides a consistent logging setup for the Supply Chain application
with the following features:

- Structured JSON logging for production (machine-readable)
- Pretty console logging for development (human-readable)
- Automatic context binding (request_id, user_id, etc.)
- Integration with Django's logging
- Log file rotation support
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

import structlog


def configure_logging(
    debug: bool = False,
    log_level: str = "INFO",
    log_dir: Path | None = None,
    json_logs: bool | None = None,
):
    """
    Configure structured logging for the application.

    Args:
        debug: Enable debug mode (pretty console output)
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None to disable file logging)
        json_logs: Force JSON output (None = auto based on debug)
    """
    # Determine if we should use JSON format
    if json_logs is None:
        json_logs = not debug

    # Set up timestamper
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # Shared processors for all logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON format for log aggregation
        renderer = structlog.processors.JSONRenderer()
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    else:
        # Development: Pretty console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set up handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (if log directory specified)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main application log
        app_log_file = log_dir / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        # Always use JSON for file logs (easier to parse)
        file_formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

        # Separate error log
        error_log_file = log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        handlers.append(error_handler)

        # Audit log for request/response logging
        audit_log_file = log_dir / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_file,
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=10,
            encoding="utf-8",
        )
        audit_handler.setFormatter(file_formatter)
        # Add filter to only log request/response events
        audit_handler.addFilter(AuditLogFilter())
        handlers.append(audit_handler)

    # Convert string log level to int
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    for handler in handlers:
        if handler.level == logging.NOTSET:
            handler.setLevel(numeric_level)
        root_logger.addHandler(handler)

    # Configure Django loggers
    _configure_django_loggers(numeric_level)

    return root_logger


def _configure_django_loggers(level: int):
    """Configure Django's built-in loggers to use structlog."""
    # Django's main logger
    django_logger = logging.getLogger("django")
    django_logger.setLevel(level)

    # Database queries (only log in debug mode)
    db_logger = logging.getLogger("django.db.backends")
    db_logger.setLevel(logging.WARNING)  # Reduce noise

    # Security logger (always log)
    security_logger = logging.getLogger("django.security")
    security_logger.setLevel(logging.WARNING)

    # Request logger
    request_logger = logging.getLogger("django.request")
    request_logger.setLevel(level)

    # Server logger (runserver output)
    server_logger = logging.getLogger("django.server")
    server_logger.setLevel(logging.WARNING)  # Reduce noise since we have our own


class AuditLogFilter(logging.Filter):
    """Filter to only allow audit-related log events."""

    AUDIT_EVENTS = {
        "request_started",
        "request_completed",
        "request_exception",
    }

    def filter(self, record):
        """Return True if this is an audit event."""
        # structlog adds event to the message
        if hasattr(record, "msg"):
            msg = record.msg
            if isinstance(msg, str):
                # Check if any audit event is in the message
                return any(event in msg for event in self.AUDIT_EVENTS)
            elif isinstance(msg, dict):
                return msg.get("event") in self.AUDIT_EVENTS
        return False


def get_logger(name: str | None = None):
    """
    Get a structlog logger instance.

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        Bound structlog logger
    """
    return structlog.get_logger(name)
