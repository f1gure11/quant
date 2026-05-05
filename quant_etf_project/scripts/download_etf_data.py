"""Command-line entrypoint for compliant ETF data downloads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DownloadConfig, default_end_date, default_start_date  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for ETF data download."""
    parser = argparse.ArgumentParser(description="Download China ETF daily data for local research cache.")
    parser.add_argument("--source", choices=["baostock", "akshare"], default="baostock", help="public data source")
    parser.add_argument("--start", default=default_start_date(), help="start date, YYYY-MM-DD")
    parser.add_argument("--end", default=default_end_date(), help="end date, YYYY-MM-DD")
    parser.add_argument("--force-update", action="store_true", help="re-download existing local files")
    return parser.parse_args()


def main() -> int:
    """Run ETF download pipeline."""
    args = parse_args()
    config = DownloadConfig(
        source=args.source,
        start_date=args.start,
        end_date=args.end,
        force_update=args.force_update,
    )
    from src.data_pipeline.downloader import download_etf_dataset

    result = download_etf_dataset(config)
    print(f"source={result.source}")
    print(f"success={len(result.success_codes)} failed={len(result.failures)}")
    print(f"processed={result.processed_path}")
    print(f"report={result.report_path}")
    if result.failures:
        print("failed_codes=" + ",".join(result.failures.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
