"""Tests for sqlslice.splitter."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.splitter import QuerySplitter, SplitReport, SplitSlice


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=5.0),
        Stage(name="plan", duration_ms=12.0),
        Stage(name="execute", duration_ms=80.0),
        Stage(name="fetch", duration_ms=20.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT * FROM orders", stages=stages)


@pytest.fixture()
def splitter():
    return QuerySplitter()


# ---------------------------------------------------------------------------
# SplitSlice
# ---------------------------------------------------------------------------

def test_split_slice_total_duration(stages):
    sl = SplitSlice(name="all", query="q", stages=stages)
    assert sl.total_duration_ms == pytest.approx(117.0)


def test_split_slice_empty_stages():
    sl = SplitSlice(name="none", query="q", stages=[])
    assert sl.total_duration_ms == 0.0


# ---------------------------------------------------------------------------
# QuerySplitter.split
# ---------------------------------------------------------------------------

def test_split_returns_split_report(splitter, result):
    splitter.add_slice("fast", lambda s: s.duration_ms < 15)
    report = splitter.split(result)
    assert isinstance(report, SplitReport)


def test_split_report_query_preserved(splitter, result):
    splitter.add_slice("any", lambda s: True)
    report = splitter.split(result)
    assert report.query == result.query


def test_split_slice_count_matches_predicates(splitter, result):
    splitter.add_slice("a", lambda s: s.duration_ms < 10)
    splitter.add_slice("b", lambda s: s.duration_ms >= 10)
    report = splitter.split(result)
    assert report.slice_count == 2


def test_split_stages_filtered_correctly(splitter, result):
    splitter.add_slice("slow", lambda s: s.duration_ms >= 20)
    report = splitter.split(result)
    slow_slice = report.get("slow")
    assert slow_slice is not None
    assert all(s.duration_ms >= 20 for s in slow_slice.stages)


def test_split_no_match_gives_empty_slice(splitter, result):
    splitter.add_slice("impossible", lambda s: s.duration_ms > 9999)
    report = splitter.split(result)
    sl = report.get("impossible")
    assert sl is not None
    assert len(sl.stages) == 0
    assert sl.total_duration_ms == 0.0


def test_split_get_unknown_name_returns_none(splitter, result):
    splitter.add_slice("x", lambda s: True)
    report = splitter.split(result)
    assert report.get("nonexistent") is None


def test_split_no_predicates_raises(splitter, result):
    with pytest.raises(ValueError, match="No slice predicates"):
        splitter.split(result)


def test_add_slice_empty_name_raises(splitter):
    with pytest.raises(ValueError, match="non-empty"):
        splitter.add_slice("", lambda s: True)


def test_add_slice_whitespace_name_raises(splitter):
    with pytest.raises(ValueError, match="non-empty"):
        splitter.add_slice("   ", lambda s: True)


def test_add_slice_returns_self_for_chaining(splitter):
    returned = splitter.add_slice("a", lambda s: True)
    assert returned is splitter


def test_split_summary_contains_query(splitter, result):
    splitter.add_slice("all", lambda s: True)
    report = splitter.split(result)
    assert result.query in report.summary()


def test_split_summary_contains_slice_name(splitter, result):
    splitter.add_slice("my_slice", lambda s: True)
    report = splitter.split(result)
    assert "my_slice" in report.summary()
