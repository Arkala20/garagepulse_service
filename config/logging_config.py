"""
config/logging_config.py

Central logging configuration for GaragePulse.
Creates log directory if needed and configures both file + console logging.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from config.settings import settings


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


def setup_logging() -> None:
    """
    Configure application logging.

    Creates:
    - console logger
    - rotating file logger

    Safe to call once at app startup.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_file = settings.LOG_FILE

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger(__name__).info(
        "Logging initialized. Level=%s, File=%s",
        settings.LOG_LEVEL.upper(),
        log_file,
    )