"""Tests for sqlslice.aggregator module."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.aggregator import ProfileAggregator, AggregationReport, StageStats


QUERY = "SELECT * FROM orders"


def make_result(durations: dict, error=None):
    stages = [Stage(name=k, duration=v) for k, v in durations.items()]
    total = sum(durations.values())
    return ProfileResult(query=QUERY, stages=stages, total_duration=total, error=error)


@pytest.fixture
def aggregator():
    agg = ProfileAggregator()
    agg.add(make_result({"parse": 0.1, "execute": 0.4, "fetch": 0.2}))
    agg.add(make_result({"parse": 0.2, "execute": 0.6, "fetch": 0.3}))
    agg.add(make_result({"parse": 0.15, "execute": 0.5, "fetch": 0.25}))
    return agg


def test_aggregate_returns_report(aggregator):
    report = aggregator.aggregate()
    assert isinstance(report, AggregationReport)


def test_aggregate_run_count(aggregator):
    report = aggregator.aggregate()
    assert report.run_count == 3


def test_aggregate_query_name(aggregator):
    report = aggregator.aggregate()
    assert report.query == QUERY


def test_aggregate_total_mean(aggregator):
    report = aggregator.aggregate()
    # totals: 0.7, 1.1, 0.9 => mean = 0.9
    assert report.total_mean == pytest.approx(0.9, rel=1e-3)


def test_aggregate_total_min_max(aggregator):
    report = aggregator.aggregate()
    assert report.total_min == pytest.approx(0.7, rel=1e-3)
    assert report.total_max == pytest.approx(1.1, rel=1e-3)


def test_aggregate_stage_count(aggregator):
    report = aggregator.aggregate()
    assert len(report.stage_stats) == 3


def test_aggregate_stage_names(aggregator):
    report = aggregator.aggregate()
    names = {s.name for s in report.stage_stats}
    assert names == {"parse", "execute", "fetch"}


def test_aggregate_stage_stats_values(aggregator):
    report = aggregator.aggregate()
    execute = next(s for s in report.stage_stats if s.name == "execute")
    assert execute.min_duration == pytest.approx(0.4, rel=1e-3)
    assert execute.max_duration == pytest.approx(0.6, rel=1e-3)
    assert execute.mean_duration == pytest.approx(0.5, rel=1e-3)


def test_aggregate_error_count():
    agg = ProfileAggregator()
    agg.add(make_result({"parse": 0.1, "execute": 0.3}))
    agg.add(make_result({}, error="timeout"))
    report = agg.aggregate()
    assert report.error_count == 1
    assert report.run_count == 2


def test_aggregate_empty_raises():
    agg = ProfileAggregator()
    with pytest.raises(ValueError, match="No results"):
        agg.aggregate()


def test_stage_stats_repr(aggregator):
    report = aggregator.aggregate()
    s = report.stage_stats[0]
    assert "StageStats" in repr(s)
    assert "mean=" in repr(s)


def test_summary_contains_query(aggregator):
    report = aggregator.aggregate()
    summary = report.summary()
    assert QUERY in summary


def test_summary_contains_stage_names(aggregator):
    report = aggregator.aggregate()
    summary = report.summary()
    assert "execute" in summary
    assert "fetch" in summary


def test_query_set_at_construction():
    agg = ProfileAggregator(query="SELECT 1")
    agg.add(make_result({"parse": 0.05}))
    report = agg.aggregate()
    assert report.query == "SELECT 1"
