"""Export utilities for PipelineReport."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import IO

from sqlslice.pipeline import PipelineReport


def pipeline_to_json(report: PipelineReport) -> str:
    """Serialize a PipelineReport to a JSON string."""
    payload = {
        "query": report.query,
        "steps": report.steps,
        "results": {
            k: (v if isinstance(v, (int, float, str, list, dict, bool, type(None))) else str(v))
            for k, v in report.results.items()
        },
    }
    return json.dumps(payload, indent=2)


def pipeline_to_csv(report: PipelineReport) -> str:
    """Serialize a PipelineReport to CSV with step/result rows."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["step", "result"])
    for step in report.steps:
        value = report.results.get(step, "")
        writer.writerow([step, str(value)])
    return buf.getvalue()


def write_pipeline_to_stream(report: PipelineReport, stream: IO[str], fmt: str = "json") -> None:
    """Write a PipelineReport to an open text stream."""
    if fmt == "csv":
        stream.write(pipeline_to_csv(report))
    else:
        stream.write(pipeline_to_json(report))


def save_pipeline(report: PipelineReport, path: str, fmt: str = "json") -> Path:
    """Save a PipelineReport to a file and return the resolved Path."""
    p = Path(path)
    with p.open("w", encoding="utf-8") as fh:
        write_pipeline_to_stream(report, fh, fmt=fmt)
    return p
