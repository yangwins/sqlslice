"""Export helpers for ScoreReport — JSON, CSV, and stream/file sinks."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from sqlslice.scorer import ScoreReport


def score_to_json(report: ScoreReport) -> str:
    """Serialise *report* to a JSON string."""
    payload = {
        "query": report.query,
        "overall_score": report.overall_score,
        "overall_grade": report.overall_grade,
        "stages": [
            {
                "name": ss.stage.name,
                "duration_ms": ss.stage.duration_ms,
                "score": ss.score,
                "grade": ss.grade,
            }
            for ss in report.scored_stages
        ],
    }
    return json.dumps(payload, indent=2)


def score_to_csv(report: ScoreReport) -> str:
    """Serialise *report* stages to CSV text."""
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["stage", "duration_ms", "score", "grade"],
        lineterminator="\n",
    )
    writer.writeheader()
    for ss in report.scored_stages:
        writer.writerow(
            {
                "stage": ss.stage.name,
                "duration_ms": ss.stage.duration_ms,
                "score": ss.score,
                "grade": ss.grade,
            }
        )
    return buf.getvalue()


def write_score_to_stream(
    report: ScoreReport,
    stream: io.TextIOBase,
    fmt: str = "json",
) -> None:
    """Write *report* to an open text *stream* in *fmt* format."""
    if fmt == "csv":
        stream.write(score_to_csv(report))
    else:
        stream.write(score_to_json(report))


def save_score(
    report: ScoreReport,
    path: Union[str, Path],
    fmt: str = "json",
) -> Path:
    """Persist *report* to *path* and return the resolved :class:`Path`."""
    dest = Path(path)
    with dest.open("w", encoding="utf-8") as fh:
        write_score_to_stream(report, fh, fmt=fmt)  # type: ignore[arg-type]
    return dest
