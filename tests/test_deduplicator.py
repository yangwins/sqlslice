"""Tests for sqlslice.deduplicator."""

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.deduplicator import QueryDeduplicator, DeduplicationReport, DedupGroup


def _make_result(query: str, durations: list) -> ProfileResult:
    stages = [Stage(name=f"stage_{i}", duration_ms=d) for i, d in enumerate(durations)]
    return ProfileResult(query=query, stages=stages, error=None)


@pytest.fixture
def deduplicator():
    return QueryDeduplicator()


@pytest.fixture
def mixed_results():
    return [
        _make_result("SELECT * FROM users WHERE id = 1", [10.0, 20.0]),
        _make_result("SELECT * FROM users WHERE id = 2", [12.0, 18.0]),
        _make_result("SELECT * FROM orders WHERE id = 99", [5.0, 8.0]),
    ]


def test_deduplicate_returns_report(deduplicator, mixed_results):
    report = deduplicator.deduplicate(mixed_results)
    assert isinstance(report, DeduplicationReport)


def test_empty_results_raises(deduplicator):
    with pytest.raises(ValueError, match="empty"):
        deduplicator.deduplicate([])


def test_identical_queries_grouped(deduplicator):
    results = [
        _make_result("SELECT 1", [5.0]),
        _make_result("SELECT 1", [7.0]),
        _make_result("SELECT 1", [6.0]),
    ]
    report = deduplicator.deduplicate(results)
    assert report.group_count == 1
    assert report.groups[0].count == 3


def test_distinct_queries_separate_groups(deduplicator, mixed_results):
    report = deduplicator.deduplicate(mixed_results)
    # WHERE id = 1 and WHERE id = 2 share a fingerprint; orders is separate
    assert report.group_count == 2


def test_total_results_matches_input(deduplicator, mixed_results):
    report = deduplicator.deduplicate(mixed_results)
    assert report.total_results == len(mixed_results)


def test_avg_duration_ms(deduplicator):
    results = [
        _make_result("SELECT 1", [10.0]),
        _make_result("SELECT 1", [20.0]),
    ]
    report = deduplicator.deduplicate(results)
    assert report.groups[0].avg_duration_ms == pytest.approx(15.0)


def test_total_duration_ms(deduplicator):
    results = [
        _make_result("SELECT 1", [10.0]),
        _make_result("SELECT 1", [20.0]),
    ]
    report = deduplicator.deduplicate(results)
    assert report.groups[0].total_duration_ms == pytest.approx(30.0)


def test_dedup_group_repr():
    group = DedupGroup(fingerprint="abc123", canonical_query="SELECT 1")
    r = repr(group)
    assert "abc123" in r
    assert "DedupGroup" in r


def test_report_repr(deduplicator, mixed_results):
    report = deduplicator.deduplicate(mixed_results)
    r = repr(report)
    assert "DeduplicationReport" in r
    assert "groups=" in r


def test_summary_contains_fingerprint(deduplicator, mixed_results):
    report = deduplicator.deduplicate(mixed_results)
    summary = report.summary()
    assert "Deduplication Report" in summary
    assert "count=" in summary
    assert "avg=" in summary


def test_single_result(deduplicator):
    results = [_make_result("DELETE FROM logs", [3.0])]
    report = deduplicator.deduplicate(results)
    assert report.group_count == 1
    assert report.total_results == 1
