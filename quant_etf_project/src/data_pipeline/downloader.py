"""Batch ETF daily data downloader with local cache and incremental updates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR, DownloadConfig
from src.data_pipeline.cleaner import STANDARD_COLUMNS, clean_daily_bars, merge_and_clean
from src.data_pipeline.etf_universe import load_or_build_universe
from src.data_pipeline.validator import write_quality_report
from src.data_sources import akshare_loader, baostock_loader
from src.utils.logger import ensure_parent, get_logger


@dataclass
class DownloadResult:
    """Summary of a batch ETF download run."""

    source: str
    success_codes: list[str] = field(default_factory=list)
    failures: dict[str, str] = field(default_factory=dict)
    raw_paths: list[Path] = field(default_factory=list)
    processed_path: Path | None = None
    report_path: Path | None = None


def download_etf_dataset(config: DownloadConfig) -> DownloadResult:
    """Download, clean, cache, and validate ETF daily bars for a universe."""
    logger = get_logger()
    source = config.source.lower()
    if source not in {"baostock", "akshare"}:
        raise ValueError("source must be 'baostock' or 'akshare'")

    logger.info(
        "ETF download started | source=%s | start=%s | end=%s | force_update=%s",
        source,
        config.start_date,
        config.end_date,
        config.force_update,
    )

    universe = load_or_build_universe(
        preferred_source=source,
        force_update=config.force_update,
        universe_mode=config.universe_mode,
        logger=logger,
    )
    name_map = dict(zip(universe["code"].astype(str).str.zfill(6), universe["name"].fillna("")))
    result = DownloadResult(source=source)

    if source == "baostock":
        with baostock_loader.BaoStockSession(logger=logger):
            _download_codes(universe, config, source, name_map, baostock_loader.fetch_daily_bars, result, logger)
    else:
        _download_codes(universe, config, source, name_map, akshare_loader.fetch_daily_bars, result, logger)

    processed_frames = []
    for path in sorted((RAW_DIR / source).glob("*.csv")):
        try:
            processed_frames.append(pd.read_csv(path, dtype={"code": str}))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed reading raw cache %s: %s", path, exc)

    processed = pd.concat(processed_frames, ignore_index=True) if processed_frames else pd.DataFrame(columns=STANDARD_COLUMNS)
    processed = processed.drop_duplicates(subset=["code", "date"], keep="last").sort_values(["code", "date"]).reset_index(drop=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = PROCESSED_DIR / f"etf_daily_{source}.csv"
    processed.to_csv(processed_path, index=False, encoding="utf-8-sig")
    report_path = write_quality_report(processed, source=source)

    result.processed_path = processed_path
    result.report_path = report_path
    logger.info(
        "ETF download finished | source=%s | success=%s | failed=%s | processed=%s | report=%s",
        source,
        len(result.success_codes),
        len(result.failures),
        processed_path,
        report_path,
    )
    if result.failures:
        logger.info("Failed ETF codes: %s", result.failures)
    return result


def _download_codes(
    universe: pd.DataFrame,
    config: DownloadConfig,
    source: str,
    name_map: dict[str, str],
    fetcher: Callable[..., pd.DataFrame],
    result: DownloadResult,
    logger: object,
) -> None:
    """Download each ETF independently and continue after failures."""
    for _, row in universe.iterrows():
        code = str(row["code"]).zfill(6)
        raw_path = RAW_DIR / source / f"{code}.csv"
        try:
            existing = _read_existing(raw_path)
            start_date = _incremental_start(config.start_date, config.end_date, existing, config.force_update)
            if existing is not None and not config.force_update and start_date is None:
                logger.info("Skip %s: local cache already covers requested end date", code)
                result.success_codes.append(code)
                result.raw_paths.append(raw_path)
                continue

            raw = _fetch_with_retry(fetcher, code, start_date or config.start_date, config.end_date, config.retry_times, config.sleep_seconds)
            cleaned = clean_daily_bars(raw, source=source, name_map=name_map)
            merged = merge_and_clean(pd.DataFrame(columns=STANDARD_COLUMNS) if config.force_update else existing, cleaned)
            ensure_parent(raw_path)
            merged.to_csv(raw_path, index=False, encoding="utf-8-sig")
            result.success_codes.append(code)
            result.raw_paths.append(raw_path)
            logger.info("Saved %s rows for %s to %s", len(merged), code, raw_path)
        except Exception as exc:  # noqa: BLE001
            result.failures[code] = str(exc)
            logger.exception("Failed downloading ETF %s: %s", code, exc)


def _read_existing(path: Path) -> pd.DataFrame | None:
    """Read an existing raw cache file if present."""
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"code": str})


def _incremental_start(
    requested_start: str,
    requested_end: str,
    existing: pd.DataFrame | None,
    force_update: bool,
) -> str | None:
    """Return the next start date for incremental update or None when complete."""
    if force_update or existing is None or existing.empty or "date" not in existing.columns:
        return requested_start
    max_date = pd.to_datetime(existing["date"], errors="coerce").max()
    if pd.isna(max_date):
        return requested_start
    if max_date.date() >= pd.to_datetime(requested_end).date():
        return None
    next_date = max_date + pd.Timedelta(days=1)
    if next_date.date() > pd.to_datetime(requested_end).date():
        return None
    return max(next_date.strftime("%Y-%m-%d"), requested_start)


def _fetch_with_retry(
    fetcher: Callable[..., pd.DataFrame],
    code: str,
    start_date: str,
    end_date: str,
    retry_times: int,
    sleep_seconds: float,
) -> pd.DataFrame:
    """Call a source fetcher with bounded retries."""
    last_error: Exception | None = None
    for _ in range(retry_times + 1):
        try:
            return fetcher(code=code, start_date=start_date, end_date=end_date, sleep_seconds=sleep_seconds)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(str(last_error))
