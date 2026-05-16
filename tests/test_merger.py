"""Tests for sqlslice.merger."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.merger import MergeReport, ProfileMerger


SQL = "SELECT 1"


def _make_result(stages, error=None):
    total = sum(s.duration_ms for s in stages)
    return ProfileResult(query=SQL, stages=stages, total_duration_ms=total, error=error)


@pytest.fixture()
def merger():
    return ProfileMerger()


def test_merge_returns_merge_report(merger):
    r = _make_result([Stage("parse", 10.0), Stage("execute", 20.0)])
    report = merger.merge([r])
    assert isinstance(report, MergeReport)


def test_merge_source_count(merger):
    r1 = _make_result([Stage("parse", 5.0)])
    r2 = _make_result([Stage("parse", 7.0)])
    report = merger.merge([r1, r2])
    assert report.source_count == 2


def test_merge_sums_same_stage_names(merger):
    r1 = _make_result([Stage("parse", 10.0), Stage("execute", 30.0)])
    r2 = _make_result([Stage("parse", 5.0), Stage("execute", 15.0)])
    report = merger.merge([r1, r2])
    by_name = {s.name: s.duration_ms for s in report.merged_stages}
    assert by_name["parse"] == pytest.approx(15.0)
    assert by_name["execute"] == pytest.approx(45.0)


def test_merge_total_duration(merger):
    r1 = _make_result([Stage("parse", 10.0), Stage("execute", 20.0)])
    r2 = _make_result([Stage("parse", 5.0), Stage("execute", 10.0)])
    report = merger.merge([r1, r2])
    assert report.total_duration_ms == pytest.approx(45.0)


def test_merge_skips_error_results(merger):
    good = _make_result([Stage("execute", 50.0)])
    bad = _make_result([], error="timeout")
    report = merger.merge([good, bad])
    assert len(report.errors) == 1
    assert "timeout" in report.errors


def test_merge_error_only_results_still_counted(merger):
    bad = _make_result([], error="conn refused")
    good = _make_result([Stage("execute", 20.0)])
    report = merger.merge([bad, good])
    assert report.source_count == 2


def test_merge_empty_raises(merger):
    with pytest.raises(ValueError, match="at least one"):
        merger.merge([])


def test_merge_custom_query_name():
    m = ProfileMerger(query_name="custom label")
    r = _make_result([Stage("parse", 5.0)])
    report = m.merge([r])
    assert report.query == "custom label"


def test_merge_preserves_stage_order(merger):
    r1 = _make_result([Stage("parse", 1.0), Stage("plan", 2.0), Stage("execute", 3.0)])
    r2 = _make_result([Stage("parse", 1.0), Stage("plan", 2.0), Stage("execute", 3.0)])
    report = merger.merge([r1, r2])
    names = [s.name for s in report.merged_stages]
    assert names == ["parse", "plan", "execute"]


def test_summary_contains_query(merger):
    r = _make_result([Stage("execute", 40.0)])
    report = merger.merge([r])
    assert SQL in report.summary()


def test_summary_contains_source_count(merger):
    r1 = _make_result([Stage("execute", 10.0)])
    r2 = _make_result([Stage("execute", 10.0)])
    report = merger.merge([r1, r2])
    assert "2" in report.summary()


def test_repr_contains_sources(merger):
    r = _make_result([Stage("execute", 10.0)])
    report = merger.merge([r])
    assert "sources=1" in repr(report)
