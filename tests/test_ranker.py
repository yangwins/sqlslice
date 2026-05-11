"""Tests for sqlslice.ranker."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.ranker import RankReport, RankedStage, StageRanker


@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=50.0),
        Stage(name="execute", duration_ms=200.0),
        Stage(name="fetch", duration_ms=30.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=290.0)


@pytest.fixture()
def ranker():
    return StageRanker()


def test_rank_returns_rank_report(ranker, result):
    report = ranker.rank(result)
    assert isinstance(report, RankReport)


def test_rank_count_matches_stages(ranker, result):
    report = ranker.rank(result)
    assert len(report.ranked_stages) == 4


def test_rank_order_slowest_first(ranker, result):
    report = ranker.rank(result)
    durations = [rs.stage.duration_ms for rs in report.ranked_stages]
    assert durations == sorted(durations, reverse=True)


def test_rank_numbers_start_at_one(ranker, result):
    report = ranker.rank(result)
    assert report.ranked_stages[0].rank == 1


def test_rank_numbers_are_sequential(ranker, result):
    report = ranker.rank(result)
    ranks = [rs.rank for rs in report.ranked_stages]
    assert ranks == list(range(1, len(ranks) + 1))


def test_slowest_is_execute(ranker, result):
    report = ranker.rank(result)
    assert report.slowest.stage.name == "execute"


def test_fastest_is_parse(ranker, result):
    report = ranker.rank(result)
    assert report.fastest.stage.name == "parse"


def test_pct_of_total_sums_to_100(ranker, result):
    report = ranker.rank(result)
    total_pct = sum(rs.pct_of_total for rs in report.ranked_stages)
    assert abs(total_pct - 100.0) < 0.01


def test_pct_of_total_execute(ranker, result):
    report = ranker.rank(result)
    execute_rs = next(rs for rs in report.ranked_stages if rs.stage.name == "execute")
    expected = 200.0 / 290.0 * 100
    assert abs(execute_rs.pct_of_total - expected) < 0.01


def test_summary_contains_query(ranker, result):
    report = ranker.rank(result)
    assert "SELECT 1" in report.summary()


def test_summary_contains_stage_names(ranker, result):
    report = ranker.rank(result)
    summary = report.summary()
    for stage in result.stages:
        assert stage.name in summary


def test_empty_stages_returns_empty_report(ranker):
    result = ProfileResult(query="SELECT 2", stages=[], total_duration_ms=0.0)
    report = ranker.rank(result)
    assert report.ranked_stages == []
    assert report.slowest is None
    assert report.fastest is None


def test_error_stages_excluded(ranker):
    stages = [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="execute", duration_ms=0.0, error="timeout"),
    ]
    result = ProfileResult(query="Q", stages=stages, total_duration_ms=10.0)
    report = ranker.rank(result)
    assert len(report.ranked_stages) == 1
    assert report.ranked_stages[0].stage.name == "parse"


def test_ranked_stage_repr(ranker, result):
    report = ranker.rank(result)
    rs = report.ranked_stages[0]
    text = repr(rs)
    assert "RankedStage" in text
    assert "rank=1" in text


def test_rank_report_repr(ranker, result):
    report = ranker.rank(result)
    text = repr(report)
    assert "RankReport" in text
    assert "SELECT 1" in text
