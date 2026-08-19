import logging
import sys
import json
import re
from contextvars import ContextVar
from typing import Any, Dict
from app.core.config import settings

# Correlation Request ID context variable
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="none")


class SensitiveDataFilter(logging.Filter):
    """Masks passwords, authorization tokens, private keys, and secrets from all log records."""
    PATTERNS = [
        (re.compile(r'(password[\'"]?\s*[:=]\s*[\'"])[^\'"]+([\'"])', re.IGNORECASE), r'\1***MASKED***\2'),
        (re.compile(r'(token[\'"]?\s*[:=]\s*[\'"])[^\'"]+([\'"])', re.IGNORECASE), r'\1***MASKED***\2'),
        (re.compile(r'(secret_key[\'"]?\s*[:=]\s*[\'"])[^\'"]+([\'"])', re.IGNORECASE), r'\1***MASKED***\2'),
        (re.compile(r'(bearer\s+)[a-zA-Z0-9_\-\.]+', re.IGNORECASE), r'\1***MASKED***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_ctx_var.get()
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


class StandardLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_ctx_var.get()
        return super().format(record)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or request_id_ctx_var.get()
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": req_id,
            "file": record.filename,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    level_name = (settings.LOG_LEVEL or "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level_name, logging.INFO)

    if settings.LOG_FORMAT == "json":
        formatter = JsonLogFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = StandardLogFormatter(
            fmt="%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    filter_instance = SensitiveDataFilter()
    handler.addFilter(filter_instance)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]
    root_logger.addFilter(filter_instance)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARN
    )

    logger = logging.getLogger("reliefchain")
    logger.info(f"Logging initialized in {settings.ENVIRONMENT} mode (level: {level_name}, format: {settings.LOG_FORMAT}).")
    return logger


logger = setup_logging()
