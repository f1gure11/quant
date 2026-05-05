"""Cleaning and field standardization for ETF daily bars."""

from __future__ import annotations

import pandas as pd


STANDARD_COLUMNS = ["date", "code", "name", "open", "high", "low", "close", "volume", "amount", "pct_chg", "source"]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "amount", "pct_chg"]


def clean_daily_bars(raw: pd.DataFrame, source: str, name_map: dict[str, str] | None = None) -> pd.DataFrame:
    """Normalize one source's raw daily ETF bars into the standard schema."""
    if raw.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = raw.copy()
    if source == "baostock":
        df = df.rename(columns={"pctChg": "pct_chg"})
    elif source == "akshare":
        df = df.rename(
            columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "pct_chg",
            }
        )
    else:
        raise ValueError(f"不支持的数据源：{source}")

    for column in STANDARD_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df["code"] = df["code"].astype(str).str.extract(r"(\d{6})", expand=False).fillna(df["code"].astype(str)).str.zfill(6)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["source"] = source
    if name_map:
        df["name"] = df["code"].map(name_map).fillna(df["name"])

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df[STANDARD_COLUMNS].drop_duplicates()
    df = df.sort_values(["code", "date"], na_position="last").reset_index(drop=True)
    return df


def merge_and_clean(existing: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
    """Merge existing and newly downloaded standard bars, then de-duplicate."""
    parts = [frame for frame in [existing, new_data] if frame is not None and not frame.empty]
    if not parts:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    merged = pd.concat(parts, ignore_index=True)
    merged = merged.drop_duplicates(subset=["code", "date"], keep="last")
    return merged.sort_values(["code", "date"]).reset_index(drop=True)
