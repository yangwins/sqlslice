"""CLI entry point for running repeated profiling and showing a diff report."""

from __future__ import annotations

import argparse
import sys
import time
from typing import Callable, Optional

from sqlslice.differ import ProfileDiffer
from sqlslice.profiler import QueryProfiler, ProfileResult


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-differ",
        description="Run a query multiple times and show stage-level trend diff.",
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
        "--delay",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Delay between runs in seconds (default: 0)",
    )
    parser.add_argument(
        "--dsn",
        default=None,
        metavar="DSN",
        help="Database connection string (optional)",
    )
    return parser


def run_differ_session(
    query: str,
    runs: int,
    profiler: QueryProfiler,
    delay: float = 0.0,
    on_result: Optional[Callable[[int, ProfileResult], None]] = None,
) -> None:
    """Execute repeated profiling runs and print a DiffReport."""
    if runs < 1:
        raise ValueError("runs must be >= 1")

    differ = ProfileDiffer()

    for i in range(1, runs + 1):
        result = profiler.profile(query)
        differ.add(result)
        if on_result:
            on_result(i, result)
        if delay > 0 and i < runs:
            time.sleep(delay)

    report = differ.diff()
    print(report.summary())


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.runs < 1:
        print("Error: --runs must be at least 1.", file=sys.stderr)
        sys.exit(1)

    try:
        profiler = QueryProfiler(dsn=args.dsn)
    except Exception as exc:
        print(f"Error creating profiler: {exc}", file=sys.stderr)
        sys.exit(1)

    def _on_result(i: int, result: ProfileResult) -> None:
        status = f"[error: {result.error}]" if result.error else "ok"
        total = sum(s.duration for s in result.stages)
        print(f"  Run {i:>3}: total={total:.4f}s  {status}")

    print(f"Profiling {args.runs} run(s) of: {args.query}")
    print("-" * 50)

    run_differ_session(
        query=args.query,
        runs=args.runs,
        profiler=profiler,
        delay=args.delay,
        on_result=_on_result,
    )


if __name__ == "__main__":
    main()
