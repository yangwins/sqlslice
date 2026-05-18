"""Export utilities for LabelReport: JSON, CSV, and stream/file helpers."""
from __future__ import annotations
import csv
import io
import json
from typing import IO
from sqlslice.labeler import LabelReport


def label_to_json(report: LabelReport) -> str:
    """Serialise a LabelReport to a JSON string."""
    data = {
        "query": report.query,
        "labeled_stages": [
            {
                "name": ls.stage.name,
                "duration_ms": ls.stage.duration_ms,
                "label": ls.label,
            }
            for ls in report.labeled_stages
        ],
    }
    return json.dumps(data, indent=2)


def label_to_csv(report: LabelReport) -> str:
    """Serialise a LabelReport to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["stage", "duration_ms", "label"])
    for ls in report.labeled_stages:
        writer.writerow([ls.stage.name, f"{ls.stage.duration_ms:.4f}", ls.label])
    return buf.getvalue()


def write_label_to_stream(report: LabelReport, stream: IO[str], fmt: str = "json") -> None:
    """Write a LabelReport to an open text stream."""
    if fmt == "csv":
        stream.write(label_to_csv(report))
    else:
        stream.write(label_to_json(report))


def save_label(report: LabelReport, path: str, fmt: str = "json") -> None:
    """Persist a LabelReport to *path* in the requested format."""
    with open(path, "w", encoding="utf-8") as fh:
        write_label_to_stream(report, fh, fmt=fmt)
