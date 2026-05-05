"""AKShare public interface loader for ETF universe and daily bars."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd


def _import_akshare():
    """Import akshare lazily so setup errors are clear."""
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        raise ImportError("请先安装 akshare：pip install -r requirements.txt") from exc
    return ak


def fetch_etf_universe(logger: object | None = None) -> pd.DataFrame:
    """Fetch ETF spot list from AKShare's public fund ETF interface."""
    ak = _import_akshare()
    df = ak.fund_etf_spot_em()
    if df.empty:
        return pd.DataFrame(columns=["code", "name", "exchange", "list_date", "status", "source"])

    rename_map = {
        "代码": "code",
        "名称": "name",
        "市场": "exchange",
    }
    out = df.rename(columns=rename_map).copy()
    out["code"] = out["code"].astype(str).str.zfill(6)
    if "name" not in out.columns:
        out["name"] = ""
    if "exchange" not in out.columns:
        out["exchange"] = ""
    out["exchange"] = out["exchange"].replace({"": pd.NA})
    out["exchange"] = out["exchange"].fillna(out["code"].map(_infer_exchange))
    out["list_date"] = ""
    out["status"] = "active"
    out["source"] = "akshare"
    return out[["code", "name", "exchange", "list_date", "status", "source"]].drop_duplicates("code")


def fetch_daily_bars(
    code: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
    sleep_seconds: float = 0.8,
) -> pd.DataFrame:
    """Download daily ETF bars from AKShare's public historical ETF interface."""
    ak = _import_akshare()
    start = start_date.replace("-", "")
    end = end_date.replace("-", "")
    df = ak.fund_etf_hist_em(symbol=str(code).zfill(6), period="daily", start_date=start, end_date=end, adjust=adjust)
    time.sleep(sleep_seconds)
    if df.empty:
        return df
    df["code"] = str(code).zfill(6)
    return df


def _infer_exchange(code: Any) -> str:
    """Infer exchange from Chinese ETF code prefix."""
    text = str(code).zfill(6)
    if text.startswith("5"):
        return "SH"
    if text.startswith("1"):
        return "SZ"
    return ""
