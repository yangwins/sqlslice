"""Tests for sqlslice.labeler."""
import pytest
from sqlslice.profiler import Stage, ProfileResult
from sqlslice.labeler import (
    StageLabeler,
    LabelReport,
    LabeledStage,
    LABEL_OK,
    LABEL_SLOW,
    LABEL_CRITICAL,
)


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration_ms=20.0),
        Stage(name="plan", duration_ms=150.0),
        Stage(name="execute", duration_ms=600.0),
    ]


@pytest.fixture
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages)


@pytest.fixture
def labeler():
    return StageLabeler(slow_ms=100.0, critical_ms=500.0)


def test_label_returns_label_report(result, labeler):
    report = labeler.label(result)
    assert isinstance(report, LabelReport)


def test_label_report_query_preserved(result, labeler):
    report = labeler.label(result)
    assert report.query == result.query


def test_label_count_matches_stages(result, labeler):
    report = labeler.label(result)
    assert len(report.labeled_stages) == len(result.stages)


def test_ok_label_assigned(result, labeler):
    report = labeler.label(result)
    ok_stages = report.by_label(LABEL_OK)
    assert any(ls.stage.name == "parse" for ls in ok_stages)


def test_slow_label_assigned(result, labeler):
    report = labeler.label(result)
    slow_stages = report.by_label(LABEL_SLOW)
    assert any(ls.stage.name == "plan" for ls in slow_stages)


def test_critical_label_assigned(result, labeler):
    report = labeler.label(result)
    critical_stages = report.by_label(LABEL_CRITICAL)
    assert any(ls.stage.name == "execute" for ls in critical_stages)


def test_labeled_stage_repr(result, labeler):
    report = labeler.label(result)
    r = repr(report.labeled_stages[0])
    assert "LabeledStage" in r
    assert "parse" in r


def test_label_report_repr(result, labeler):
    report = labeler.label(result)
    r = repr(report)
    assert "LabelReport" in r
    assert "SELECT 1" in r


def test_summary_contains_query(result, labeler):
    report = labeler.label(result)
    s = report.summary()
    assert "SELECT 1" in s


def test_summary_contains_labels(result, labeler):
    report = labeler.label(result)
    s = report.summary()
    assert "OK" in s or "SLOW" in s or "CRITICAL" in s


def test_summary_contains_counts(result, labeler):
    report = labeler.label(result)
    s = report.summary()
    assert "Labels:" in s


def test_invalid_slow_ms_raises():
    with pytest.raises(ValueError, match="slow_ms"):
        StageLabeler(slow_ms=0)


def test_critical_not_greater_than_slow_raises():
    with pytest.raises(ValueError, match="critical_ms"):
        StageLabeler(slow_ms=200.0, critical_ms=100.0)


def test_boundary_slow_exact(labeler):
    stage = Stage(name="boundary", duration_ms=100.0)
    result = ProfileResult(query="Q", stages=[stage])
    report = labeler.label(result)
    assert report.labeled_stages[0].label == LABEL_SLOW


def test_boundary_critical_exact(labeler):
    stage = Stage(name="boundary", duration_ms=500.0)
    result = ProfileResult(query="Q", stages=[stage])
    report = labeler.label(result)
    assert report.labeled_stages[0].label == LABEL_CRITICAL


def test_empty_stages_produces_empty_report(labeler):
    result = ProfileResult(query="Q", stages=[])
    report = labeler.label(result)
    assert report.labeled_stages == []
