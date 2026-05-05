"""Project configuration for compliant ETF data collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOG_DIR = PROJECT_ROOT / "logs"

DEFAULT_SOURCE = "baostock"
DEFAULT_LOOKBACK_YEARS = 5
DEFAULT_SLEEP_SECONDS = 0.8
DEFAULT_RETRY_TIMES = 2

# Manual ETF universe fallback. Codes should be six digits without exchange prefix.
UNIVERSE_MODE = "auto"  # "auto" fetches source universe; "manual" uses MANUAL_ETF_CODES only.
MANUAL_ETF_CODES = ["510300", "510500", "159915", "588000", "512100"]
MANUAL_ETF_NAMES = {
    "510300": "沪深300ETF",
    "510500": "中证500ETF",
    "159915": "创业板ETF",
    "588000": "科创50ETF",
    "512100": "中证1000ETF",
}


def default_start_date(today: date | None = None) -> str:
    """Return the default start date, approximately five years before today."""
    current = today or date.today()
    return (current - timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)).isoformat()


def default_end_date(today: date | None = None) -> str:
    """Return the default end date."""
    return (today or date.today()).isoformat()


@dataclass(frozen=True)
class DownloadConfig:
    """Runtime options for ETF universe and daily bar downloads."""

    source: str = DEFAULT_SOURCE
    start_date: str = field(default_factory=default_start_date)
    end_date: str = field(default_factory=default_end_date)
    force_update: bool = False
    universe_mode: str = UNIVERSE_MODE
    manual_codes: list[str] = field(default_factory=lambda: MANUAL_ETF_CODES.copy())
    sleep_seconds: float = DEFAULT_SLEEP_SECONDS
    retry_times: int = DEFAULT_RETRY_TIMES
