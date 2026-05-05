"""Logging helpers for ETF data downloads."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import LOG_DIR


def get_logger(name: str = "etf_data") -> logging.Logger:
    """Create or return a project logger writing to console and log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "data_download.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def ensure_parent(path: Path) -> None:
    """Ensure that a file path's parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
