"""
Logging utilities for ETL Pipeline.

Provides structured logging with JSON format support for production.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logger(
    name: str = "etl_pipeline",
    level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        use_json: Whether to use JSON formatting.
        log_file: Optional file path for logging to file.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logger("my_module", level="DEBUG")
        >>> logger.info("Processing started", extra={"extra_fields": {"count": 100}})
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if use_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter to add contextual information."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and add extra fields.

        Args:
            msg: Log message.
            kwargs: Additional keyword arguments.

        Returns:
            Processed message and kwargs.
        """
        # Add context to extra fields
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        if "extra_fields" not in kwargs["extra"]:
            kwargs["extra"]["extra_fields"] = {}

        # Merge context with extra fields
        kwargs["extra"]["extra_fields"].update(self.extra)

        return msg, kwargs


def get_context_logger(logger: logging.Logger, **context: Any) -> LoggerAdapter:
    """
    Get logger adapter with contextual information.

    Args:
        logger: Base logger.
        **context: Context key-value pairs to add to all log messages.

    Returns:
        Logger adapter with context.

    Example:
        >>> base_logger = setup_logger()
        >>> logger = get_context_logger(base_logger, job_id="job_123", user="admin")
        >>> logger.info("Task completed")
    """
    return LoggerAdapter(logger, context)
