"""CLI entry-point: profile a query and split stages into named slices."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from sqlslice.profiler import QueryProfiler
from sqlslice.splitter import QuerySplitter
from sqlslice.export_splitter import save_split


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlslice-split",
        description="Profile a SQL query and split stages into named slices.",
    )
    parser.add_argument("query", help="SQL query to profile.")
    parser.add_argument(
        "--dsn",
        default="sqlite:///:memory:",
        help="Database DSN (default: sqlite:///:memory:).",
    )
    parser.add_argument(
        "--slice",
        metavar="NAME:MAX_MS",
        action="append",
        dest="slices",
        default=[],
        help="Define a slice as NAME:MAX_MS (stages with duration <= MAX_MS). Repeatable.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Save report to FILE (format inferred from extension: .json or .csv).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output.",
    )
    return parser


def _parse_slices(raw: List[str]) -> List[tuple[str, float]]:
    """Parse 'NAME:MAX_MS' tokens into (name, max_ms) tuples."""
    result = []
    for token in raw:
        parts = token.split(":", 1)
        if len(parts) != 2:
            raise SystemExit(f"Invalid slice spec {token!r}. Expected NAME:MAX_MS.")
        name, raw_ms = parts
        try:
            max_ms = float(raw_ms)
        except ValueError:
            raise SystemExit(f"Invalid MAX_MS value in {token!r}; must be a number.")
        result.append((name, max_ms))
    return result


def run_split_session(
    query: str,
    dsn: str,
    slices: List[tuple[str, float]],
    output: Optional[str] = None,
    quiet: bool = False,
) -> None:
    profiler = QueryProfiler(dsn=dsn)
    profile_result = profiler.profile(query)

    splitter = QuerySplitter()
    if slices:
        for name, max_ms in slices:
            splitter.add_slice(name, lambda s, m=max_ms: s.duration_ms <= m)
    else:
        # Default: split into fast (<= 10 ms) and slow (> 10 ms)
        splitter.add_slice("fast", lambda s: s.duration_ms <= 10.0)
        splitter.add_slice("slow", lambda s: s.duration_ms > 10.0)

    report = splitter.split(profile_result)

    if not quiet:
        print(report.summary())

    if output:
        fmt = "csv" if output.endswith(".csv") else "json"
        path = save_split(report, output, fmt=fmt)
        if not quiet:
            print(f"Report saved to {path}")


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    slice_specs = _parse_slices(args.slices)
    run_split_session(
        query=args.query,
        dsn=args.dsn,
        slices=slice_specs,
        output=args.output,
        quiet=args.quiet,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
