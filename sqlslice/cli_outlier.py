"""CLI entry-point for outlier detection."""
from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional

from sqlslice.export_outlier import outlier_to_csv, outlier_to_json
from sqlslice.outlier import OutlierDetector
from sqlslice.profiler import ProfileResult, QueryProfiler


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-outlier",
        description="Detect outlier stages in a SQL query profile.",
    )
    p.add_argument("dsn", help="Database connection string")
    p.add_argument("query", help="SQL query to profile")
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        metavar="Z",
        help="Z-score threshold for outlier detection (default: 2.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; exit 1 if outliers found",
    )
    return p


def run_outlier_session(
    dsn: str,
    query: str,
    threshold: float = 2.0,
    fmt: str = "text",
    quiet: bool = False,
    profiler: Optional[QueryProfiler] = None,
    on_report: Optional[Callable] = None,
) -> int:
    """Run outlier detection and print results.  Returns exit code."""
    if profiler is None:  # pragma: no cover
        profiler = QueryProfiler(dsn)

    result: ProfileResult = profiler.profile(query)
    detector = OutlierDetector(threshold=threshold)
    report = detector.detect(result)

    if on_report is not None:
        on_report(report)

    if not quiet:
        if fmt == "json":
            print(outlier_to_json(report))
        elif fmt == "csv":
            print(outlier_to_csv(report))
        else:
            print(report.summary())

    return 1 if report.has_outliers else 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        code = run_outlier_session(
            dsn=args.dsn,
            query=args.query,
            threshold=args.threshold,
            fmt=args.fmt,
            quiet=args.quiet,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    sys.exit(code)


if __name__ == "__main__":  # pragma: no cover
    main()
