"""Tests for sqlslice.export_pipeline."""
import io
import json
import csv
import tempfile
from pathlib import Path

import pytest
from sqlslice.pipeline import PipelineReport
from sqlslice.export_pipeline import (
    pipeline_to_json,
    pipeline_to_csv,
    write_pipeline_to_stream,
    save_pipeline,
)


@pytest.fixture
def report():
    return PipelineReport(
        query="SELECT count(*) FROM orders",
        steps=["count", "names", "total"],
        results={
            "count": 3,
            "names": ["parse", "plan", "execute"],
            "total": 100.0,
        },
    )


def test_to_json_is_valid(report):
    raw = pipeline_to_json(report)
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_to_json_has_query(report):
    data = json.loads(pipeline_to_json(report))
    assert data["query"] == "SELECT count(*) FROM orders"


def test_to_json_has_steps(report):
    data = json.loads(pipeline_to_json(report))
    assert data["steps"] == ["count", "names", "total"]


def test_to_json_has_results(report):
    data = json.loads(pipeline_to_json(report))
    assert "results" in data
    assert data["results"]["count"] == 3


def test_to_json_list_result_preserved(report):
    data = json.loads(pipeline_to_json(report))
    assert data["results"]["names"] == ["parse", "plan", "execute"]


def test_to_csv_has_header(report):
    raw = pipeline_to_csv(report)
    reader = csv.reader(io.StringIO(raw))
    header = next(reader)
    assert header == ["step", "result"]


def test_to_csv_row_count(report):
    raw = pipeline_to_csv(report)
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 4  # header + 3 steps


def test_to_csv_step_names_present(report):
    raw = pipeline_to_csv(report)
    assert "count" in raw
    assert "names" in raw
    assert "total" in raw


def test_write_to_stream_json(report):
    buf = io.StringIO()
    write_pipeline_to_stream(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["query"] == report.query


def test_write_to_stream_csv(report):
    buf = io.StringIO()
    write_pipeline_to_stream(report, buf, fmt="csv")
    assert "step" in buf.getvalue()


def test_save_pipeline_creates_file(report):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "pipeline.json"
        result = save_pipeline(report, str(out))
        assert result.exists()


def test_save_pipeline_returns_path(report):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "pipeline.json"
        returned = save_pipeline(report, str(out))
        assert isinstance(returned, Path)


def test_save_pipeline_csv(report):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "pipeline.csv"
        save_pipeline(report, str(out), fmt="csv")
        content = out.read_text()
        assert "step" in content
