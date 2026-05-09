"""Export utilities for DiffReport — JSON and CSV serialisation."""

from __future__ import annotations

import csv
import io
import json
from typing import IO

from sqlslice.differ import DiffReport


def diff_to_json(report: DiffReport) -> str:
    """Serialise a DiffReport to a JSON string."""
    payload = {
        "query": report.query,
        "run_count": report.run_count,
        "errors": [e for e in report.errors if e is not None],
        "stage_trends": [
            {
                "stage": st.stage_name,
                "mean": round(st.mean, 6),
                "min": round(st.min, 6),
                "max": round(st.max, 6),
                "trend": st.trend,
                "samples": len(st.durations),
            }
            for st in report.stage_trends
        ],
    }
    return json.dumps(payload, indent=2)


def diff_to_csv(report: DiffReport) -> str:
    """Serialise a DiffReport's stage trends to CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["stage", "mean", "min", "max", "trend", "samples"])
    for st in report.stage_trends:
        writer.writerow(
            [
                st.stage_name,
                round(st.mean, 6),
                round(st.min, 6),
                round(st.max, 6),
                st.trend,
                len(st.durations),
            ]
        )
    return output.getvalue()


def write_diff_to_stream(report: DiffReport, stream: IO[str], fmt: str = "json") -> None:
    """Write a DiffReport to an open text stream."""
    if fmt == "json":
        stream.write(diff_to_json(report))
    elif fmt == "csv":
        stream.write(diff_to_csv(report))
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Choose 'json' or 'csv'.")


def save_diff(report: DiffReport, path: str, fmt: str = "json") -> None:
    """Save a DiffReport to a file."""
    with open(path, "w", encoding="utf-8") as fh:
        write_diff_to_stream(report, fh, fmt=fmt)
