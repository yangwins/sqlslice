"""Tests for sqlslice.export_splitter."""
import csv
import io
import json
from pathlib import Path

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.splitter import QuerySplitter
from sqlslice.export_splitter import (
    split_to_json,
    split_to_csv,
    write_split_to_stream,
    save_split,
)


@pytest.fixture()
def report():
    stages = [
        Stage(name="parse", duration_ms=4.0),
        Stage(name="execute", duration_ms=96.0),
    ]
    result = ProfileResult(query="SELECT 1", stages=stages)
    splitter = QuerySplitter()
    splitter.add_slice("fast", lambda s: s.duration_ms < 10)
    splitter.add_slice("slow", lambda s: s.duration_ms >= 10)
    return splitter.split(result)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def test_to_json_is_valid(report):
    data = json.loads(split_to_json(report))
    assert isinstance(data, dict)


def test_to_json_has_query(report):
    data = json.loads(split_to_json(report))
    assert data["query"] == "SELECT 1"


def test_to_json_slice_count(report):
    data = json.loads(split_to_json(report))
    assert data["slice_count"] == 2


def test_to_json_slices_list(report):
    data = json.loads(split_to_json(report))
    assert len(data["slices"]) == 2


def test_to_json_slice_fields(report):
    data = json.loads(split_to_json(report))
    sl = data["slices"][0]
    assert "name" in sl
    assert "stage_count" in sl
    assert "total_duration_ms" in sl
    assert "stages" in sl


def test_to_json_stage_duration(report):
    data = json.loads(split_to_json(report))
    slow_slice = next(s for s in data["slices"] if s["name"] == "slow")
    assert slow_slice["total_duration_ms"] == pytest.approx(96.0)


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def test_to_csv_has_header(report):
    text = split_to_csv(report)
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    assert header == ["slice", "stage", "duration_ms"]


def test_to_csv_row_count(report):
    text = split_to_csv(report)
    rows = list(csv.reader(io.StringIO(text)))
    # 1 header + 2 stage rows
    assert len(rows) == 3


def test_to_csv_slice_name_present(report):
    text = split_to_csv(report)
    assert "fast" in text
    assert "slow" in text


# ---------------------------------------------------------------------------
# write_split_to_stream
# ---------------------------------------------------------------------------

def test_write_to_stream_json(report):
    buf = io.StringIO()
    write_split_to_stream(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert "slices" in data


def test_write_to_stream_csv(report):
    buf = io.StringIO()
    write_split_to_stream(report, buf, fmt="csv")
    assert "slice" in buf.getvalue()


def test_write_to_stream_invalid_fmt(report):
    buf = io.StringIO()
    with pytest.raises(ValueError, match="Unsupported format"):
        write_split_to_stream(report, buf, fmt="xml")


# ---------------------------------------------------------------------------
# save_split
# ---------------------------------------------------------------------------

def test_save_split_creates_file(tmp_path, report):
    dest = tmp_path / "out.json"
    result_path = save_split(report, dest)
    assert result_path.exists()


def test_save_split_returns_path(tmp_path, report):
    dest = tmp_path / "out.json"
    result_path = save_split(report, dest)
    assert isinstance(result_path, Path)


def test_save_split_csv(tmp_path, report):
    dest = tmp_path / "out.csv"
    save_split(report, dest, fmt="csv")
    content = dest.read_text()
    assert "slice" in content
