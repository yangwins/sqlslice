"""CLI entry point for the pipeline runner."""
from __future__ import annotations

import argparse
import sys

from sqlslice.analyzer import QueryAnalyzer
from sqlslice.ranker import QueryRanker
from sqlslice.summarizer import QuerySummarizer
from sqlslice.profiler import QueryProfiler
from sqlslice.pipeline import QueryPipeline
from sqlslice.export_pipeline import save_pipeline


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlslice-pipeline",
        description="Run a multi-step analysis pipeline over a profiled query.",
    )
    p.add_argument("query", help="SQL query to profile and analyze.")
    p.add_argument("--dsn", default="sqlite:///:memory:", help="Database DSN.")
    p.add_argument(
        "--steps",
        nargs="+",
        choices=["analyze", "rank", "summarize"],
        default=["analyze", "rank", "summarize"],
        help="Pipeline steps to execute (default: all).",
    )
    p.add_argument("--threshold", type=float, default=10.0, help="Bottleneck threshold ms.")
    p.add_argument("--top", type=int, default=3, help="Top N stages for ranker.")
    p.add_argument("--output", default=None, help="Save report to file (JSON).")
    p.add_argument("--quiet", action="store_true", help="Suppress summary output.")
    return p


def run_pipeline_session(
    query: str,
    dsn: str,
    steps: list,
    threshold: float,
    top: int,
    output: str | None,
    quiet: bool,
) -> None:
    profiler = QueryProfiler(dsn=dsn)
    result = profiler.profile(query)

    pipeline = QueryPipeline()

    step_map = {
        "analyze": ("analyze", lambda r: QueryAnalyzer(threshold_ms=threshold).analyze(r)),
        "rank": ("rank", lambda r: QueryRanker(top_n=top).rank(r)),
        "summarize": ("summarize", lambda r: QuerySummarizer().build(r)),
    }

    for key in steps:
        name, fn = step_map[key]
        pipeline.add_step(name, fn)

    report = pipeline.run(result)

    if not quiet:
        print(report.summary())
        for step_name, step_result in report.results.items():
            print(f"\n[{step_name}]")
            if hasattr(step_result, "summary"):
                print(step_result.summary())
            else:
                print(str(step_result))

    if output:
        saved = save_pipeline(report, output)
        if not quiet:
            print(f"\nReport saved to {saved}")


def main(argv: list | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        run_pipeline_session(
            query=args.query,
            dsn=args.dsn,
            steps=args.steps,
            threshold=args.threshold,
            top=args.top,
            output=args.output,
            quiet=args.quiet,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
