"""Export helpers for SplitReport: JSON, CSV, and stream/file output."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from sqlslice.splitter import SplitReport


def split_to_json(report: SplitReport) -> str:
    """Serialise a SplitReport to a JSON string."""
    payload = {
        "query": report.query,
        "slice_count": report.slice_count,
        "slices": [
            {
                "name": sl.name,
                "stage_count": len(sl.stages),
                "total_duration_ms": sl.total_duration_ms,
                "stages": [
                    {"name": s.name, "duration_ms": s.duration_ms}
                    for s in sl.stages
                ],
            }
            for sl in report.slices
        ],
    }
    return json.dumps(payload, indent=2)


def split_to_csv(report: SplitReport) -> str:
    """Serialise a SplitReport to CSV (one row per stage per slice)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["slice", "stage", "duration_ms"])
    for sl in report.slices:
        for stage in sl.stages:
            writer.writerow([sl.name, stage.name, f"{stage.duration_ms:.6f}"])
    return buf.getvalue()


def write_split_to_stream(
    report: SplitReport,
    stream: io.TextIOBase,
    fmt: str = "json",
) -> None:
    """Write a SplitReport to an open text stream."""
    if fmt == "csv":
        stream.write(split_to_csv(report))
    elif fmt == "json":
        stream.write(split_to_json(report))
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Choose 'json' or 'csv'.")


def save_split(
    report: SplitReport,
    path: Union[str, Path],
    fmt: str = "json",
) -> Path:
    """Save a SplitReport to *path* and return the resolved Path."""
    dest = Path(path)
    with dest.open("w", encoding="utf-8") as fh:
        write_split_to_stream(report, fh, fmt=fmt)
    return dest
