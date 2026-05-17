"""Tests for sqlslice.grouper."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.grouper import GroupedBucket, GroupReport, ProfileGrouper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(query: str, durations: list[float]) -> ProfileResult:
    stages = [
        Stage(name=f"stage_{i}", duration_ms=d)
        for i, d in enumerate(durations)
    ]
    return ProfileResult(query=query, stages=stages, error=None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def grouper() -> ProfileGrouper:
    return ProfileGrouper()


@pytest.fixture()
def mixed_results() -> list[ProfileResult]:
    return [
        _make_result("SELECT 1", [10.0, 20.0]),
        _make_result("SELECT 2", [5.0]),
        _make_result("SELECT 1", [15.0, 25.0]),
        _make_result("SELECT 2", [8.0]),
        _make_result("SELECT 1", [12.0]),
    ]


# ---------------------------------------------------------------------------
# Tests — GroupedBucket
# ---------------------------------------------------------------------------

def test_grouped_bucket_count():
    r = _make_result("SELECT 1", [10.0])
    bucket = GroupedBucket(key="a", results=[r, r])
    assert bucket.count == 2


def test_grouped_bucket_total_duration():
    r1 = _make_result("SELECT 1", [10.0, 20.0])
    r2 = _make_result("SELECT 1", [5.0])
    bucket = GroupedBucket(key="a", results=[r1, r2])
    assert bucket.total_duration_ms == pytest.approx(35.0)


def test_grouped_bucket_avg_duration():
    r1 = _make_result("SELECT 1", [40.0])
    r2 = _make_result("SELECT 1", [20.0])
    bucket = GroupedBucket(key="a", results=[r1, r2])
    assert bucket.avg_duration_ms == pytest.approx(30.0)


def test_grouped_bucket_avg_empty():
    bucket = GroupedBucket(key="empty")
    assert bucket.avg_duration_ms == 0.0


# ---------------------------------------------------------------------------
# Tests — ProfileGrouper.group
# ---------------------------------------------------------------------------

def test_group_returns_group_report(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert isinstance(report, GroupReport)


def test_group_empty_raises(grouper):
    with pytest.raises(ValueError, match="empty"):
        grouper.group([])


def test_group_bucket_count(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert report.bucket_count == 2


def test_group_query_preserved(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert report.query == "SELECT 1"


def test_group_select1_has_three_runs(grouper, mixed_results):
    report = grouper.group(mixed_results)
    bucket = report.get("SELECT 1")
    assert bucket is not None
    assert bucket.count == 3


def test_group_select2_has_two_runs(grouper, mixed_results):
    report = grouper.group(mixed_results)
    bucket = report.get("SELECT 2")
    assert bucket is not None
    assert bucket.count == 2


def test_group_get_missing_key_returns_none(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert report.get("NONEXISTENT") is None


def test_group_custom_key_fn():
    results = [
        _make_result("SELECT a FROM t WHERE id=1", [10.0]),
        _make_result("SELECT a FROM t WHERE id=2", [20.0]),
        _make_result("SELECT b FROM t WHERE id=3", [30.0]),
    ]
    # Group by first word after SELECT
    grouper = ProfileGrouper(key_fn=lambda r: r.query.split()[1])
    report = grouper.group(results)
    assert report.bucket_count == 2
    assert report.get("a").count == 2
    assert report.get("b").count == 1


# ---------------------------------------------------------------------------
# Tests — GroupReport
# ---------------------------------------------------------------------------

def test_summary_contains_query(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert "SELECT 1" in report.summary()


def test_summary_contains_bucket_keys(grouper, mixed_results):
    report = grouper.group(mixed_results)
    s = report.summary()
    assert "SELECT 1" in s
    assert "SELECT 2" in s


def test_summary_contains_runs_label(grouper, mixed_results):
    report = grouper.group(mixed_results)
    assert "runs=" in report.summary()
