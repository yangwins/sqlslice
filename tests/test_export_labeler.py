"""Tests for sqlslice.export_labeler."""
import csv
import io
import json
import os
import tempfile
import pytest
from sqlslice.profiler import Stage, ProfileResult
from sqlslice.labeler import StageLabeler
from sqlslice.export_labeler import (
    label_to_json,
    label_to_csv,
    write_label_to_stream,
    save_label,
)


@pytest.fixture
def report():
    stages = [
        Stage(name="parse", duration_ms=30.0),
        Stage(name="plan", duration_ms=120.0),
        Stage(name="execute", duration_ms=550.0),
    ]
    result = ProfileResult(query="SELECT * FROM t", stages=stages)
    labeler = StageLabeler(slow_ms=100.0, critical_ms=500.0)
    return labeler.label(result)


def test_to_json_is_valid(report):
    raw = label_to_json(report)
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_to_json_has_query(report):
    data = json.loads(label_to_json(report))
    assert data["query"] == "SELECT * FROM t"


def test_to_json_has_labeled_stages(report):
    data = json.loads(label_to_json(report))
    assert "labeled_stages" in data
    assert len(data["labeled_stages"]) == 3


def test_to_json_stage_fields(report):
    data = json.loads(label_to_json(report))
    stage = data["labeled_stages"][0]
    assert "name" in stage
    assert "duration_ms" in stage
    assert "label" in stage


def test_to_json_labels_correct(report):
    data = json.loads(label_to_json(report))
    by_name = {s["name"]: s["label"] for s in data["labeled_stages"]}
    assert by_name["parse"] == "ok"
    assert by_name["plan"] == "slow"
    assert by_name["execute"] == "critical"


def test_to_csv_is_parseable(report):
    raw = label_to_csv(report)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 3


def test_to_csv_has_header(report):
    raw = label_to_csv(report)
    assert raw.startswith("stage,")


def test_to_csv_label_column(report):
    raw = label_to_csv(report)
    reader = csv.DictReader(io.StringIO(raw))
    rows = {r["stage"]: r["label"] for r in reader}
    assert rows["parse"] == "ok"
    assert rows["plan"] == "slow"
    assert rows["execute"] == "critical"


def test_write_to_stream_json(report):
    buf = io.StringIO()
    write_label_to_stream(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["query"] == report.query


def test_write_to_stream_csv(report):
    buf = io.StringIO()
    write_label_to_stream(report, buf, fmt="csv")
    assert "stage" in buf.getvalue()


def test_save_label_json(report):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_label(report, path, fmt="json")
        with open(path) as f:
            data = json.load(f)
        assert data["query"] == report.query
    finally:
        os.unlink(path)


def test_save_label_csv(report):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        save_label(report, path, fmt="csv")
        with open(path) as f:
            content = f.read()
        assert "stage" in content
    finally:
        os.unlink(path)
