"""Tests for sqlslice.capper."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.capper import CappedStage, CapReport, StageCapper


@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=250.0),
        Stage(name="execute", duration_ms=800.0),
        Stage(name="fetch", duration_ms=50.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT * FROM orders", stages=stages)


@pytest.fixture()
def capper():
    return StageCapper(ceiling_ms=200.0)


def test_cap_returns_cap_report(result, capper):
    report = capper.cap(result)
    assert isinstance(report, CapReport)


def test_cap_report_query_preserved(result, capper):
    report = capper.cap(result)
    assert report.query == result.query


def test_cap_report_ceiling_preserved(result, capper):
    report = capper.cap(result)
    assert report.ceiling_ms == 200.0


def test_stages_below_ceiling_not_capped(result, capper):
    report = capper.cap(result)
    parse = next(s for s in report.stages if s.name == "parse")
    assert not parse.was_capped
    assert parse.capped_ms == parse.original_ms


def test_stages_above_ceiling_are_capped(result, capper):
    report = capper.cap(result)
    execute = next(s for s in report.stages if s.name == "execute")
    assert execute.was_capped
    assert execute.capped_ms == 200.0


def test_capped_count(result, capper):
    report = capper.cap(result)
    # plan=250 and execute=800 exceed 200
    assert report.capped_count == 2


def test_total_capped_ms_less_than_original(result, capper):
    report = capper.cap(result)
    assert report.total_capped_ms < report.total_original_ms


def test_total_original_ms(result, capper):
    report = capper.cap(result)
    assert report.total_original_ms == pytest.approx(1110.0)


def test_total_capped_ms(result, capper):
    report = capper.cap(result)
    # parse=10, plan->200, execute->200, fetch=50
    assert report.total_capped_ms == pytest.approx(460.0)


def test_summary_contains_query(result, capper):
    report = capper.cap(result)
    assert result.query in report.summary()


def test_summary_contains_ceiling(result, capper):
    report = capper.cap(result)
    assert "200.00" in report.summary()


def test_capped_stage_repr_includes_flag():
    s = CappedStage(name="execute", original_ms=800.0, capped_ms=200.0, was_capped=True)
    assert "CAPPED" in repr(s)


def test_uncapped_stage_repr_excludes_flag():
    s = CappedStage(name="parse", original_ms=10.0, capped_ms=10.0, was_capped=False)
    assert "CAPPED" not in repr(s)


def test_cap_report_repr(result, capper):
    report = capper.cap(result)
    assert "CapReport" in repr(report)


def test_invalid_ceiling_zero_raises():
    with pytest.raises(ValueError):
        StageCapper(ceiling_ms=0)


def test_invalid_ceiling_negative_raises():
    with pytest.raises(ValueError):
        StageCapper(ceiling_ms=-50.0)


def test_invalid_ceiling_type_raises():
    with pytest.raises(TypeError):
        StageCapper(ceiling_ms="fast")


def test_invalid_result_type_raises(capper):
    with pytest.raises(TypeError):
        capper.cap("not a result")
