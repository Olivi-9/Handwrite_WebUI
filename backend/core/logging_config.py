from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path

from .settings import (
    BACKEND_LOG_BACKUP_COUNT,
    BACKEND_LOG_FILE_PATH,
    BACKEND_LOG_LEVEL,
    BACKEND_LOG_MAX_BYTES,
)


def configure_logging() -> None:
    """Configure application and Uvicorn loggers with file + console handlers."""
    log_file = Path(BACKEND_LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": BACKEND_LOG_LEVEL,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": str(log_file),
                    "maxBytes": BACKEND_LOG_MAX_BYTES,
                    "backupCount": BACKEND_LOG_BACKUP_COUNT,
                    "encoding": "utf-8",
                    "level": BACKEND_LOG_LEVEL,
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["console", "file"],
                    "level": BACKEND_LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console", "file"],
                    "level": BACKEND_LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console", "file"],
                    "level": BACKEND_LOG_LEVEL,
                    "propagate": False,
                },
                "backend": {
                    "handlers": ["console", "file"],
                    "level": BACKEND_LOG_LEVEL,
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": BACKEND_LOG_LEVEL,
            },
        }
    )

    logging.getLogger("backend").info("Logging configured. File path: %s", log_file)
