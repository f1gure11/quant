"""Command-line entrypoint for ETF data quality validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for data quality validation."""
    parser = argparse.ArgumentParser(description="Validate processed ETF daily data.")
    parser.add_argument("--source", choices=["baostock", "akshare"], default="baostock")
    return parser.parse_args()


def main() -> int:
    """Run validation on the processed ETF daily CSV."""
    args = parse_args()
    data_path = PROCESSED_DIR / f"etf_daily_{args.source}.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"未找到已处理数据：{data_path}")

    import pandas as pd

    from src.data_pipeline.validator import write_quality_report

    data = pd.read_csv(data_path, dtype={"code": str})
    report_path = write_quality_report(data, source=args.source)
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
