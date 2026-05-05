"""ETF universe construction with automatic and manual modes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import MANUAL_ETF_CODES, PROCESSED_DIR, UNIVERSE_MODE
from src.data_sources import akshare_loader, baostock_loader


UNIVERSE_COLUMNS = ["code", "name", "exchange", "list_date", "status", "source"]


def build_manual_universe(codes: list[str] | None = None) -> pd.DataFrame:
    """Build a manual ETF universe from configured six-digit ETF codes."""
    rows = []
    for code in codes or MANUAL_ETF_CODES:
        text = str(code).strip().zfill(6)
        rows.append(
            {
                "code": text,
                "name": "",
                "exchange": _infer_exchange(text),
                "list_date": "",
                "status": "manual",
                "source": "manual_config",
            }
        )
    return pd.DataFrame(rows, columns=UNIVERSE_COLUMNS).drop_duplicates("code")


def fetch_auto_universe(preferred_source: str = "baostock", logger: object | None = None) -> pd.DataFrame:
    """Fetch ETF universe automatically, falling back to AKShare if needed."""
    source = preferred_source.lower()
    frames: list[pd.DataFrame] = []

    if source == "baostock":
        try:
            frames.append(baostock_loader.fetch_etf_universe(logger=logger))
        except Exception as exc:  # noqa: BLE001 - log and fallback across data sources
            if logger:
                logger.warning("BaoStock ETF universe fetch failed: %s", exc)
    elif source == "akshare":
        try:
            frames.append(akshare_loader.fetch_etf_universe(logger=logger))
        except Exception as exc:  # noqa: BLE001
            if logger:
                logger.warning("AKShare ETF universe fetch failed: %s", exc)
    else:
        raise ValueError("source must be 'baostock' or 'akshare'")

    if not frames or all(frame.empty for frame in frames):
        try:
            frames.append(akshare_loader.fetch_etf_universe(logger=logger))
        except Exception as exc:  # noqa: BLE001
            if logger:
                logger.warning("AKShare ETF universe fallback failed: %s", exc)

    auto = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True) if frames else pd.DataFrame()
    if auto.empty:
        return build_manual_universe()

    manual = build_manual_universe()
    merged = pd.concat([auto, manual], ignore_index=True)
    merged["code"] = merged["code"].astype(str).str.zfill(6)
    for column in UNIVERSE_COLUMNS:
        if column not in merged.columns:
            merged[column] = ""
    return merged[UNIVERSE_COLUMNS].drop_duplicates("code", keep="first").sort_values("code").reset_index(drop=True)


def save_universe(universe: pd.DataFrame, path: Path | None = None) -> Path:
    """Save ETF universe CSV and return the output path."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = path or PROCESSED_DIR / "etf_universe.csv"
    universe.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def load_or_build_universe(
    preferred_source: str = "baostock",
    force_update: bool = False,
    universe_mode: str = UNIVERSE_MODE,
    logger: object | None = None,
) -> pd.DataFrame:
    """Load cached ETF universe or build a new one."""
    path = PROCESSED_DIR / "etf_universe.csv"
    if universe_mode.lower() == "manual":
        universe = build_manual_universe()
        save_universe(universe, path)
        return universe
    if universe_mode.lower() != "auto":
        raise ValueError("UNIVERSE_MODE must be 'auto' or 'manual'")

    if path.exists() and not force_update:
        return pd.read_csv(path, dtype={"code": str}).assign(code=lambda x: x["code"].str.zfill(6))

    universe = fetch_auto_universe(preferred_source=preferred_source, logger=logger)
    save_universe(universe, path)
    return universe


def _infer_exchange(code: str) -> str:
    """Infer SH/SZ exchange from common ETF code prefixes."""
    if code.startswith("5"):
        return "SH"
    if code.startswith("1"):
        return "SZ"
    return ""
