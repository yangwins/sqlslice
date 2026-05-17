"""Tests for sqlslice.scorer."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.scorer import QueryScorer, ScoreReport, ScoredStage, _grade


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=50.0),
        Stage(name="plan", duration_ms=200.0),
        Stage(name="execute", duration_ms=400.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=650.0)


@pytest.fixture()
def scorer():
    return QueryScorer(budget_ms=500.0)


# ---------------------------------------------------------------------------
# Construction guards
# ---------------------------------------------------------------------------

def test_invalid_budget_zero_raises():
    with pytest.raises(ValueError, match="budget_ms"):
        QueryScorer(budget_ms=0)


def test_invalid_budget_negative_raises():
    with pytest.raises(ValueError):
        QueryScorer(budget_ms=-100)


def test_invalid_budget_string_raises():
    with pytest.raises(ValueError):
        QueryScorer(budget_ms="fast")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_score_returns_score_report(scorer, result):
    report = scorer.score(result)
    assert isinstance(report, ScoreReport)


def test_score_report_has_correct_stage_count(scorer, result):
    report = scorer.score(result)
    assert len(report.scored_stages) == len(result.stages)


def test_scored_stage_type(scorer, result):
    report = scorer.score(result)
    for ss in report.scored_stages:
        assert isinstance(ss, ScoredStage)


# ---------------------------------------------------------------------------
# Score values
# ---------------------------------------------------------------------------

def test_zero_duration_scores_100():
    r = ProfileResult(
        query="Q",
        stages=[Stage(name="s", duration_ms=0.0)],
        total_duration_ms=0.0,
    )
    report = QueryScorer(budget_ms=500.0).score(r)
    assert report.scored_stages[0].score == 100


def test_duration_at_budget_scores_zero():
    r = ProfileResult(
        query="Q",
        stages=[Stage(name="s", duration_ms=500.0)],
        total_duration_ms=500.0,
    )
    report = QueryScorer(budget_ms=500.0).score(r)
    assert report.scored_stages[0].score == 0


def test_duration_exceeding_budget_scores_zero():
    r = ProfileResult(
        query="Q",
        stages=[Stage(name="s", duration_ms=999.0)],
        total_duration_ms=999.0,
    )
    report = QueryScorer(budget_ms=500.0).score(r)
    assert report.scored_stages[0].score == 0


def test_overall_score_is_average(scorer, result):
    report = scorer.score(result)
    expected = round(sum(ss.score for ss in report.scored_stages) / len(report.scored_stages))
    assert report.overall_score == expected


# ---------------------------------------------------------------------------
# Grades
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(95) == "A"


def test_grade_b():
    assert _grade(80) == "B"


def test_grade_f():
    assert _grade(10) == "F"


def test_score_report_overall_grade_matches_score(scorer, result):
    report = scorer.score(result)
    assert report.overall_grade == _grade(report.overall_score)


# ---------------------------------------------------------------------------
# Summary / repr
# ---------------------------------------------------------------------------

def test_summary_contains_query(scorer, result):
    assert result.query in scorer.score(result).summary()


def test_summary_contains_stage_name(scorer, result):
    report = scorer.score(result)
    assert "execute" in report.summary()


def test_summary_contains_overall(scorer, result):
    assert "Overall" in scorer.score(result).summary()


def test_repr_contains_overall_score(scorer, result):
    report = scorer.score(result)
    assert str(report.overall_score) in repr(report)


def test_scored_stage_repr(scorer, result):
    ss = scorer.score(result).scored_stages[0]
    assert ss.stage.name in repr(ss)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_stages_raises(scorer):
    empty = ProfileResult(query="Q", stages=[], total_duration_ms=0.0)
    with pytest.raises(ValueError, match="no stages"):
        scorer.score(empty)


def test_single_stage_overall_equals_stage_score():
    r = ProfileResult(
        query="Q",
        stages=[Stage(name="only", duration_ms=250.0)],
        total_duration_ms=250.0,
    )
    report = QueryScorer(budget_ms=500.0).score(r)
    assert report.overall_score == report.scored_stages[0].score
