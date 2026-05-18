"""Tests for sqlslice.sorter."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.sorter import SortReport, StageSorter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=50.0),
        Stage(name="execute", duration_ms=30.0),
        Stage(name="fetch", duration_ms=5.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, error=None)


@pytest.fixture()
def sorter():
    return StageSorter()


# ---------------------------------------------------------------------------
# Construction guards
# ---------------------------------------------------------------------------

def test_invalid_key_raises():
    with pytest.raises(ValueError, match="Invalid sort key"):
        StageSorter(key="unknown")


def test_invalid_order_raises():
    with pytest.raises(ValueError, match="Invalid order"):
        StageSorter(order="sideways")


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_sort_returns_sort_report(sorter, result):
    report = sorter.sort(result)
    assert isinstance(report, SortReport)


def test_sort_report_query_preserved(sorter, result):
    report = sorter.sort(result)
    assert report.query == result.query


def test_sort_report_stage_count_unchanged(sorter, result):
    report = sorter.sort(result)
    assert len(report.stages) == len(result.stages)


# ---------------------------------------------------------------------------
# Sorting by duration
# ---------------------------------------------------------------------------

def test_sort_by_duration_desc(result):
    sorter = StageSorter(key="duration", order="desc")
    report = sorter.sort(result)
    durations = [s.duration_ms for s in report.stages]
    assert durations == sorted(durations, reverse=True)


def test_sort_by_duration_asc(result):
    sorter = StageSorter(key="duration", order="asc")
    report = sorter.sort(result)
    durations = [s.duration_ms for s in report.stages]
    assert durations == sorted(durations)


# ---------------------------------------------------------------------------
# Sorting by name
# ---------------------------------------------------------------------------

def test_sort_by_name_asc(result):
    sorter = StageSorter(key="name", order="asc")
    report = sorter.sort(result)
    names = [s.name.lower() for s in report.stages]
    assert names == sorted(names)


def test_sort_by_name_desc(result):
    sorter = StageSorter(key="name", order="desc")
    report = sorter.sort(result)
    names = [s.name.lower() for s in report.stages]
    assert names == sorted(names, reverse=True)


# ---------------------------------------------------------------------------
# Sorting by index (original order)
# ---------------------------------------------------------------------------

def test_sort_by_index_asc_preserves_order(result):
    sorter = StageSorter(key="index", order="asc")
    report = sorter.sort(result)
    assert [s.name for s in report.stages] == [s.name for s in result.stages]


def test_sort_by_index_desc_reverses_order(result):
    sorter = StageSorter(key="index", order="desc")
    report = sorter.sort(result)
    assert [s.name for s in report.stages] == [
        s.name for s in reversed(result.stages)
    ]


# ---------------------------------------------------------------------------
# Summary / repr
# ---------------------------------------------------------------------------

def test_summary_contains_query(sorter, result):
    report = sorter.sort(result)
    assert result.query in report.summary()


def test_summary_contains_stage_names(sorter, result):
    report = sorter.sort(result)
    summary = report.summary()
    for stage in result.stages:
        assert stage.name in summary


def test_repr_contains_key_and_order(result):
    sorter = StageSorter(key="name", order="asc")
    report = sorter.sort(result)
    r = repr(report)
    assert "name" in r
    assert "asc" in r
