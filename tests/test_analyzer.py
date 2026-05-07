"""Tests for sqlslice.analyzer module."""

import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.analyzer import Bottleneck, AnalysisReport, QueryAnalyzer


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=30.0),
        Stage(name="execute", duration_ms=160.0),
    ]


@pytest.fixture
def simple_result(stages):
    return ProfileResult(
        query="SELECT * FROM orders",
        stages=stages,
        total_duration_ms=200.0,
    )


@pytest.fixture
def error_result():
    return ProfileResult(
        query="SELECT bad",
        stages=[],
        total_duration_ms=0.0,
        error="syntax error",
    )


@pytest.fixture
def analyzer():
    return QueryAnalyzer(threshold_pct=20.0)


def test_analyzer_invalid_threshold():
    with pytest.raises(ValueError):
        QueryAnalyzer(threshold_pct=0)
    with pytest.raises(ValueError):
        QueryAnalyzer(threshold_pct=110)


def test_analyze_returns_report(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    assert isinstance(report, AnalysisReport)
    assert report.query == simple_result.query
    assert report.total_duration_ms == simple_result.total_duration_ms


def test_slowest_stage_identified(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    assert report.slowest_stage is not None
    assert report.slowest_stage.name == "execute"


def test_bottlenecks_above_threshold(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    names = [b.stage.name for b in report.bottlenecks]
    # execute = 80%, plan = 15%, parse = 5%
    assert "execute" in names
    assert "parse" not in names


def test_bottleneck_is_slowest_flag(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    slowest_bottleneck = next(
        (b for b in report.bottlenecks if b.stage.name == "execute"), None
    )
    assert slowest_bottleneck is not None
    assert slowest_bottleneck.is_slowest is True


def test_bottlenecks_sorted_by_pct_descending(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    pcts = [b.pct_of_total for b in report.bottlenecks]
    assert pcts == sorted(pcts, reverse=True)


def test_error_result_returns_empty_bottlenecks(analyzer, error_result):
    report = analyzer.analyze(error_result)
    assert report.bottlenecks == []
    assert report.slowest_stage is None
    assert report.error == "syntax error"


def test_analysis_report_summary_contains_query(analyzer, simple_result):
    report = analyzer.analyze(simple_result)
    summary = report.summary()
    assert simple_result.query in summary


def test_analysis_report_summary_error(analyzer, error_result):
    report = analyzer.analyze(error_result)
    assert "failed" in report.summary().lower()


def test_bottleneck_repr():
    stage = Stage(name="execute", duration_ms=160.0)
    b = Bottleneck(stage=stage, pct_of_total=80.0, is_slowest=True)
    r = repr(b)
    assert "execute" in r
    assert "SLOWEST" in r
    assert "80.0%" in r
