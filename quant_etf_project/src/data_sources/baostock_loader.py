"""BaoStock ETF data loader.

BaoStock is used through its public Python package. The loader keeps requests
low-frequency and stores local CSV files for reproducible research use.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import pandas as pd


def _import_baostock():
    """Import baostock lazily so the project can be inspected before install."""
    try:
        import baostock as bs  # type: ignore
    except ImportError as exc:
        raise ImportError("请先安装 baostock：pip install -r requirements.txt") from exc
    return bs


def to_baostock_code(code: str) -> str:
    """Convert a six-digit ETF code to BaoStock's exchange-prefixed format."""
    clean = str(code).strip().lower().replace("sh.", "").replace("sz.", "")
    if clean.startswith(("5", "6")):
        return f"sh.{clean}"
    if clean.startswith(("0", "1", "2", "3")):
        return f"sz.{clean}"
    raise ValueError(f"无法判断交易所的证券代码：{code}")


@dataclass
class BaoStockSession:
    """Context manager for BaoStock login/logout lifecycle."""

    logger: object | None = None

    def __enter__(self):
        self.bs = _import_baostock()
        result = self.bs.login()
        if result.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败：{result.error_msg}")
        if self.logger:
            self.logger.info("BaoStock login success")
        return self.bs

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.bs.logout()
        if self.logger:
            self.logger.info("BaoStock logout")


def fetch_etf_universe(logger: object | None = None) -> pd.DataFrame:
    """Fetch a best-effort ETF universe from BaoStock tradeable securities."""
    bs = _import_baostock()
    rows: list[list[str]] = []
    with BaoStockSession(logger=logger):
        rs = bs.query_all_stock()
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
    if not rows:
        return pd.DataFrame(columns=["code", "name", "exchange", "list_date", "status", "source"])

    fields = getattr(rs, "fields", ["code", "tradeStatus", "code_name"])
    df = pd.DataFrame(rows, columns=fields)
    if "code_name" not in df.columns:
        return pd.DataFrame(columns=["code", "name", "exchange", "list_date", "status", "source"])

    mask = df["code_name"].astype(str).str.contains("ETF|交易型开放式", case=False, na=False)
    etf = df.loc[mask].copy()
    if etf.empty:
        return pd.DataFrame(columns=["code", "name", "exchange", "list_date", "status", "source"])

    etf["exchange"] = etf["code"].str.split(".").str[0].str.upper()
    etf["code"] = etf["code"].str.split(".").str[1]
    etf["name"] = etf["code_name"]
    etf["list_date"] = ""
    etf["status"] = etf.get("tradeStatus", "")
    etf["source"] = "baostock"
    return etf[["code", "name", "exchange", "list_date", "status", "source"]].drop_duplicates("code")


def fetch_daily_bars(
    code: str,
    start_date: str,
    end_date: str,
    adjustflag: str = "2",
    sleep_seconds: float = 0.8,
) -> pd.DataFrame:
    """Download daily ETF bars from BaoStock for one code.

    adjustflag: BaoStock adjustment flag. "2" means pre-adjusted data when
    supported by the source; exact availability is determined by BaoStock.
    """
    bs = _import_baostock()
    bs_code = to_baostock_code(code)
    fields = "date,code,open,high,low,close,volume,amount,pctChg"
    rows: list[list[str]] = []

    rs = bs.query_history_k_data_plus(
        bs_code,
        fields,
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag=adjustflag,
    )
    if rs.error_code != "0":
        raise RuntimeError(f"BaoStock 下载失败 {code}: {rs.error_msg}")

    while rs.next():
        rows.append(rs.get_row_data())

    time.sleep(sleep_seconds)
    df = pd.DataFrame(rows, columns=rs.fields)
    if df.empty:
        return df
    df["code"] = df["code"].astype(str).str.split(".").str[-1]
    return df
