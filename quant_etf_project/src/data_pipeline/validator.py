"""Data quality validation for processed ETF bars."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import REPORTS_DIR


REQUIRED_PRICE_COLUMNS = ["open", "high", "low", "close"]


def validate_etf_bars(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Run ETF daily bar data quality checks and return issue tables."""
    checks: dict[str, pd.DataFrame] = {}
    if data.empty:
        checks["empty_dataset"] = pd.DataFrame([{"issue": "processed dataset is empty"}])
        return checks

    df = data.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    checks["duplicate_trading_days"] = df[df.duplicated(subset=["code", "date"], keep=False)]
    checks["missing_ohlc"] = df[df[REQUIRED_PRICE_COLUMNS].isna().any(axis=1)]
    checks["high_less_than_low"] = df[df["high"] < df["low"]]
    checks["close_non_positive"] = df[df["close"] <= 0]
    checks["negative_volume"] = df[df["volume"] < 0]
    checks["ohlc_outside_range"] = df[
        (df["open"] < df["low"])
        | (df["open"] > df["high"])
        | (df["close"] < df["low"])
        | (df["close"] > df["high"])
    ]

    summary = (
        df.groupby("code", dropna=False)
        .agg(
            name=("name", "first"),
            start_date=("date", "min"),
            end_date=("date", "max"),
            row_count=("date", "count"),
            missing_open=("open", lambda s: int(s.isna().sum())),
            missing_high=("high", lambda s: int(s.isna().sum())),
            missing_low=("low", lambda s: int(s.isna().sum())),
            missing_close=("close", lambda s: int(s.isna().sum())),
        )
        .reset_index()
    )
    checks["per_etf_summary"] = summary
    return checks


def write_quality_report(
    data: pd.DataFrame,
    output_path: Path | None = None,
    source: str | None = None,
) -> Path:
    """Write a Markdown data quality report and return its path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = output_path or REPORTS_DIR / "etf_data_quality_report.md"
    checks = validate_etf_bars(data)

    lines = [
        "# ETF Data Quality Report",
        "",
        f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source: {source or 'mixed/local'}",
        "- Scope: ETF historical daily bars for local research cache only.",
        "- Compliance: 本项目仅用于学习、研究和回测验证，不构成投资建议；未使用登录、验证码、付费或 Level-2 数据。",
        "",
        "## Dataset Summary",
        "",
        f"- Rows: {len(data)}",
        f"- ETF count: {data['code'].nunique() if not data.empty and 'code' in data.columns else 0}",
        "",
    ]

    issue_names = [
        "duplicate_trading_days",
        "missing_ohlc",
        "high_less_than_low",
        "close_non_positive",
        "negative_volume",
        "ohlc_outside_range",
    ]
    lines.extend(["## Issue Counts", "", "| Check | Rows |", "|---|---:|"])
    for name in issue_names:
        lines.append(f"| {name} | {len(checks.get(name, pd.DataFrame()))} |")

    summary = checks.get("per_etf_summary", pd.DataFrame())
    lines.extend(["", "## Per ETF Summary", ""])
    if summary.empty:
        lines.append("No ETF summary available.")
    else:
        lines.append(summary.to_markdown(index=False))

    lines.extend(["", "## Issue Samples", ""])
    for name in issue_names:
        sample = checks.get(name, pd.DataFrame()).head(20)
        lines.append(f"### {name}")
        lines.append("")
        if sample.empty:
            lines.append("No issues found.")
        else:
            lines.append(sample.to_markdown(index=False))
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
