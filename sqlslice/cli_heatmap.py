"""CLI entry-point for the heatmap feature."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from sqlslice.heatmap import QueryHeatmap
from sqlslice.profiler import QueryProfiler


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-heatmap",
        description="Run a query N times and display a stage-duration heatmap.",
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
        default=None,
        metavar="DSN",
        help="Database connection string (optional)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-run output",
    )
    return parser


def run_heatmap_session(
    query: str,
    runs: int,
    profiler: QueryProfiler,
    *,
    quiet: bool = False,
    out=None,
) -> QueryHeatmap:
    """Execute *runs* profiles and return the populated QueryHeatmap."""
    if out is None:
        out = sys.stdout

    if runs < 1:
        raise ValueError(f"runs must be >= 1, got {runs}")

    heatmap = QueryHeatmap(query=query)
    for i in range(runs):
        result = profiler.profile(query)
        heatmap.add(result)
        if not quiet:
            out.write(f"  run {i + 1}/{runs} — {result.total_duration_ms:.2f} ms\n")

    report = heatmap.build()
    out.write("\n" + report.summary() + "\n")
    return heatmap


def main(argv: Optional[list] = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.runs < 1:
        parser.error("--runs must be a positive integer")

    profiler = QueryProfiler(dsn=args.dsn)
    try:
        run_heatmap_session(
            query=args.query,
            runs=args.runs,
            profiler=profiler,
            quiet=args.quiet,
        )
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
