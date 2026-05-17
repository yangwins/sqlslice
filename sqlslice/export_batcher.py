"""Export utilities for BatchReport — JSON and CSV output."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from sqlslice.batcher import BatchReport


def batch_to_json(report: BatchReport, indent: int = 2) -> str:
    """Serialise a BatchReport to a JSON string."""
    payload = {
        "total": report.total_count,
        "success": report.success_count,
        "failed": report.failure_count,
        "total_duration_ms": report.total_duration_ms,
        "entries": [
            {
                "name": e.name,
                "query": e.query,
                "succeeded": e.succeeded,
                "total_duration_ms": (
                    e.result.total_duration_ms if e.result else None
                ),
                "error": e.error,
                "stages": (
                    [
                        {"name": s.name, "duration_ms": s.duration_ms}
                        for s in e.result.stages
                    ]
                    if e.result
                    else []
                ),
            }
            for e in report.entries
        ],
    }
    return json.dumps(payload, indent=indent)


def batch_to_csv(report: BatchReport) -> str:
    """Serialise a BatchReport to a CSV string (one row per entry)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "query", "succeeded", "total_duration_ms", "error"])
    for e in report.entries:
        writer.writerow(
            [
                e.name,
                e.query,
                e.succeeded,
                e.result.total_duration_ms if e.result else "",
                e.error or "",
            ]
        )
    return buf.getvalue()


def write_batch_to_stream(
    report: BatchReport, stream: io.TextIOBase, fmt: str = "json"
) -> None:
    """Write a BatchReport to an open text stream."""
    if fmt == "csv":
        stream.write(batch_to_csv(report))
    else:
        stream.write(batch_to_json(report))


def save_batch(
    report: BatchReport,
    path: Union[str, Path],
    fmt: str = "json",
) -> Path:
    """Write a BatchReport to *path* and return the resolved Path."""
    dest = Path(path)
    with dest.open("w", encoding="utf-8") as fh:
        write_batch_to_stream(report, fh, fmt=fmt)
    return dest
