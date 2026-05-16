"""Tests for sqlslice.summarizer."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.summarizer import QuerySummarizer, SummaryReport, StageSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=30.0),
        Stage(name="execute", duration_ms=60.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages)


@pytest.fixture()
def summarizer():
    return QuerySummarizer()


# ---------------------------------------------------------------------------
# SummaryReport
# ---------------------------------------------------------------------------

def test_build_returns_summary_report(summarizer, result):
    report = summarizer.build(result)
    assert isinstance(report, SummaryReport)


def test_summary_report_query_preserved(summarizer, result):
    report = summarizer.build(result)
    assert report.query == "SELECT 1"


def test_summary_report_total_ms(summarizer, result):
    report = summarizer.build(result)
    assert report.total_ms == pytest.approx(100.0)


def test_summary_report_stage_count(summarizer, result, stages):
    report = summarizer.build(result)
    assert len(report.stage_summaries) == len(stages)


def test_stage_summary_names(summarizer, result):
    report = summarizer.build(result)
    names = [s.name for s in report.stage_summaries]
    assert names == ["parse", "plan", "execute"]


def test_stage_summary_durations(summarizer, result):
    report = summarizer.build(result)
    durations = [s.duration_ms for s in report.stage_summaries]
    assert durations == pytest.approx([10.0, 30.0, 60.0])


def test_stage_summary_pct_of_total(summarizer, result):
    report = summarizer.build(result)
    pcts = [s.pct_of_total for s in report.stage_summaries]
    assert pcts == pytest.approx([10.0, 30.0, 60.0])


def test_pct_sums_to_100(summarizer, result):
    report = summarizer.build(result)
    total_pct = sum(s.pct_of_total for s in report.stage_summaries)
    assert total_pct == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# summary() text output
# ---------------------------------------------------------------------------

def test_summary_text_contains_query(summarizer, result):
    text = summarizer.build(result).summary()
    assert "SELECT 1" in text


def test_summary_text_contains_total(summarizer, result):
    text = summarizer.build(result).summary()
    assert "100.000" in text


def test_summary_text_contains_stage_names(summarizer, result):
    text = summarizer.build(result).summary()
    for name in ("parse", "plan", "execute"):
        assert name in text


# ---------------------------------------------------------------------------
# Edge cases / errors
# ---------------------------------------------------------------------------

def test_build_raises_on_empty_stages(summarizer):
    empty_result = ProfileResult(query="SELECT 1", stages=[])
    with pytest.raises(ValueError, match="no stages"):
        summarizer.build(empty_result)


def test_build_raises_on_wrong_type(summarizer):
    with pytest.raises(TypeError):
        summarizer.build("not a ProfileResult")  # type: ignore[arg-type]


def test_single_stage_is_100_pct(summarizer):
    single = ProfileResult(
        query="SELECT 2",
        stages=[Stage(name="execute", duration_ms=42.0)],
    )
    report = summarizer.build(single)
    assert report.stage_summaries[0].pct_of_total == pytest.approx(100.0)
