"""Tests for sqlslice.pipeline."""
import pytest
from sqlslice.profiler import ProfileResult, Stage
from sqlslice.pipeline import PipelineStep, PipelineReport, QueryPipeline


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=30.0),
        Stage(name="execute", duration_ms=60.0),
    ]


@pytest.fixture
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, error=None)


@pytest.fixture
def pipeline():
    return QueryPipeline()


def test_pipeline_step_repr():
    step = PipelineStep(name="analyze", transform=lambda r: r)
    assert "analyze" in repr(step)


def test_add_step_returns_pipeline(pipeline, result):
    returned = pipeline.add_step("count", lambda r: len(r.stages))
    assert returned is pipeline


def test_step_count(pipeline):
    pipeline.add_step("a", lambda r: None)
    pipeline.add_step("b", lambda r: None)
    assert pipeline.step_count() == 2


def test_run_returns_pipeline_report(pipeline, result):
    pipeline.add_step("count", lambda r: len(r.stages))
    report = pipeline.run(result)
    assert isinstance(report, PipelineReport)


def test_report_query_preserved(pipeline, result):
    pipeline.add_step("noop", lambda r: None)
    report = pipeline.run(result)
    assert report.query == "SELECT 1"


def test_report_steps_list(pipeline, result):
    pipeline.add_step("alpha", lambda r: 1)
    pipeline.add_step("beta", lambda r: 2)
    report = pipeline.run(result)
    assert report.steps == ["alpha", "beta"]


def test_report_results_keyed_by_step_name(pipeline, result):
    pipeline.add_step("count", lambda r: len(r.stages))
    report = pipeline.run(result)
    assert "count" in report.results
    assert report.results["count"] == 3


def test_multiple_steps_all_present(pipeline, result):
    pipeline.add_step("total", lambda r: sum(s.duration_ms for s in r.stages))
    pipeline.add_step("names", lambda r: [s.name for s in r.stages])
    report = pipeline.run(result)
    assert report.results["total"] == pytest.approx(100.0)
    assert report.results["names"] == ["parse", "plan", "execute"]


def test_run_with_no_steps_raises(pipeline, result):
    with pytest.raises(RuntimeError, match="no steps"):
        pipeline.run(result)


def test_add_step_empty_name_raises(pipeline):
    with pytest.raises(ValueError):
        pipeline.add_step("", lambda r: None)


def test_add_step_non_callable_raises(pipeline):
    with pytest.raises(TypeError):
        pipeline.add_step("bad", "not_callable")


def test_pipeline_repr(pipeline):
    pipeline.add_step("x", lambda r: None)
    assert "QueryPipeline" in repr(pipeline)
    assert "x" in repr(pipeline)


def test_report_summary_contains_query(pipeline, result):
    pipeline.add_step("s", lambda r: None)
    report = pipeline.run(result)
    assert "SELECT 1" in report.summary()


def test_report_summary_contains_step_names(pipeline, result):
    pipeline.add_step("my_step", lambda r: None)
    report = pipeline.run(result)
    assert "my_step" in report.summary()


def test_report_repr(pipeline, result):
    pipeline.add_step("r", lambda r: None)
    report = pipeline.run(result)
    assert "PipelineReport" in repr(report)
