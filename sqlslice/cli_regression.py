"""CLI entry-point for the regression detector.

Usage example::

    sqlslice-regression --dsn sqlite:///app.db \\
        --query "SELECT * FROM orders" \\
        --baseline-name orders_baseline \\
        --runs 3 --threshold 15
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from sqlslice.baseline import BaselineStore
from sqlslice.profiler import QueryProfiler
from sqlslice.regression import RegressionDetector
from sqlslice.export_regression import regression_to_json, regression_to_csv


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-regression",
        description="Detect performance regressions against a saved baseline.",
    )
    p.add_argument("--dsn", required=True, help="Database connection string")
    p.add_argument("--query", required=True, help="SQL query to profile")
    p.add_argument(
        "--baseline-name",
        required=True,
        metavar="NAME",
        help="Name of the baseline record to compare against",
    )
    p.add_argument(
        "--store",
        default=".sqlslice_baselines.json",
        help="Path to the baseline store file (default: .sqlslice_baselines.json)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Regression threshold in percent (default: 10)",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of profiling runs to average (default: 1)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def run_regression_session(
    dsn: str,
    query: str,
    baseline_name: str,
    store_path: str = ".sqlslice_baselines.json",
    threshold_pct: float = 10.0,
    runs: int = 1,
    fmt: str = "text",
    out=None,
) -> None:
    if out is None:
        out = sys.stdout

    store = BaselineStore(store_path)
    record = store.load(baseline_name)
    if record is None:
        print(f"[error] baseline {baseline_name!r} not found in {store_path}", file=sys.stderr)
        sys.exit(1)

    profiler = QueryProfiler(dsn)
    results = [profiler.profile(query) for _ in range(runs)]
    # Use the last successful result for comparison
    current = next((r for r in reversed(results) if r.error is None), results[-1])

    detector = RegressionDetector(threshold_pct=threshold_pct)
    report = detector.detect(record.to_profile_result(), current)

    if fmt == "json":
        out.write(regression_to_json(report) + "\n")
    elif fmt == "csv":
        out.write(regression_to_csv(report))
    else:
        print(report.summary(), file=out)


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    run_regression_session(
        dsn=args.dsn,
        query=args.query,
        baseline_name=args.baseline_name,
        store_path=args.store,
        threshold_pct=args.threshold,
        runs=args.runs,
        fmt=args.format,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
