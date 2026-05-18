"""CLI entry-point for the stage labeler."""
from __future__ import annotations
import argparse
import sys
from sqlslice.labeler import StageLabeler
from sqlslice.export_labeler import write_label_to_stream


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-label",
        description="Attach severity labels (ok/slow/critical) to profiling stages.",
    )
    p.add_argument("query", help="SQL query to profile and label")
    p.add_argument(
        "--dsn",
        default="sqlite:///:memory:",
        help="Database connection string (default: sqlite:///:memory:)",
    )
    p.add_argument(
        "--slow-ms",
        type=float,
        default=100.0,
        dest="slow_ms",
        help="Duration threshold (ms) for 'slow' label (default: 100)",
    )
    p.add_argument(
        "--critical-ms",
        type=float,
        default=500.0,
        dest="critical_ms",
        help="Duration threshold (ms) for 'critical' label (default: 500)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Write output to this file instead of stdout",
    )
    return p


def run_label_session(
    query: str,
    dsn: str,
    slow_ms: float = 100.0,
    critical_ms: float = 500.0,
    fmt: str = "text",
    output: str | None = None,
) -> None:
    from sqlslice.profiler import QueryProfiler

    profiler = QueryProfiler(dsn=dsn)
    result = profiler.profile(query)
    labeler = StageLabeler(slow_ms=slow_ms, critical_ms=critical_ms)
    report = labeler.label(result)

    if fmt == "text":
        text = report.summary()
        if output:
            with open(output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        else:
            print(text)
    else:
        if output:
            with open(output, "w", encoding="utf-8") as fh:
                write_label_to_stream(report, fh, fmt=fmt)
        else:
            write_label_to_stream(report, sys.stdout, fmt=fmt)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        run_label_session(
            query=args.query,
            dsn=args.dsn,
            slow_ms=args.slow_ms,
            critical_ms=args.critical_ms,
            fmt=args.fmt,
            output=args.output,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
