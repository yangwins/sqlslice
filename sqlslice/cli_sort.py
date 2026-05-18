"""CLI entry-point for the stage sorter."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from sqlslice.profiler import QueryProfiler
from sqlslice.sorter import StageSorter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-sort",
        description="Profile a SQL query and display stages sorted by a chosen criterion.",
    )
    p.add_argument("query", help="SQL query to profile")
    p.add_argument(
        "--dsn",
        default="sqlite:///:memory:",
        help="SQLAlchemy-compatible DSN (default: sqlite:///:memory:)",
    )
    p.add_argument(
        "--key",
        choices=["duration", "name", "index"],
        default="duration",
        help="Sort criterion (default: duration)",
    )
    p.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="desc",
        help="Sort direction (default: desc)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the sorted stage list, omitting the header.",
    )
    return p


def run_sort_session(
    query: str,
    dsn: str,
    key: str = "duration",
    order: str = "desc",
    quiet: bool = False,
    argv: Optional[List[str]] = None,
) -> int:
    """Run a single profile + sort session.  Returns exit code."""
    try:
        profiler = QueryProfiler(dsn=dsn)
        result = profiler.profile(query)
    except Exception as exc:  # noqa: BLE001
        print(f"[sqlslice-sort] profiler error: {exc}", file=sys.stderr)
        return 1

    sorter = StageSorter(key=key, order=order)  # type: ignore[arg-type]
    report = sorter.sort(result)

    if quiet:
        for s in report.stages:
            print(f"{s.name}\t{s.duration_ms:.2f}")
    else:
        print(report.summary())

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    sys.exit(
        run_sort_session(
            query=args.query,
            dsn=args.dsn,
            key=args.key,
            order=args.order,
            quiet=args.quiet,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
