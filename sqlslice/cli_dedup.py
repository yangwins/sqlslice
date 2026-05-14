"""CLI entry point for the query deduplicator."""

from __future__ import annotations

import argparse
import sys
from typing import List

from sqlslice.profiler import QueryProfiler, ProfileResult
from sqlslice.deduplicator import QueryDeduplicator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-dedup",
        description="Profile a query N times and group results by normalized fingerprint.",
    )
    parser.add_argument("query", help="SQL query to profile")
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        metavar="N",
        help="Number of profiling runs (default: 5)",
    )
    parser.add_argument(
        "--dsn",
        default="sqlite:///:memory:",
        help="Database connection string (default: sqlite:///:memory:)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the summary, suppress per-group details",
    )
    return parser


def run_dedup_session(
    query: str,
    runs: int,
    dsn: str,
    quiet: bool = False,
    on_result=None,
) -> None:
    if runs < 1:
        raise ValueError("runs must be >= 1")

    profiler = QueryProfiler(dsn=dsn)
    results: List[ProfileResult] = []

    for i in range(runs):
        result = profiler.profile(query)
        results.append(result)
        if on_result is not None:
            on_result(i + 1, result)
        if not quiet:
            status = "ERROR" if result.error else f"{result.total_duration_ms:.2f}ms"
            print(f"  run {i + 1}/{runs}: {status}")

    deduplicator = QueryDeduplicator()
    report = deduplicator.deduplicate(results)

    print()
    print(report.summary())


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        run_dedup_session(
            query=args.query,
            runs=args.runs,
            dsn=args.dsn,
            quiet=args.quiet,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
