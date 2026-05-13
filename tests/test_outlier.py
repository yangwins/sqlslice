"""Tests for sqlslice.outlier."""
import pytest

from sqlslice.outlier import OutlierDetector, OutlierReport, OutlierStage
from sqlslice.profiler import ProfileResult, Stage


@pytest.fixture()
def stages():
    return [
        Stage(name="parse", duration_ms=10.0),
        Stage(name="plan", duration_ms=12.0),
        Stage(name="execute", duration_ms=200.0),  # outlier
        Stage(name="fetch", duration_ms=11.0),
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=233.0)


@pytest.fixture()
def detector():
    return OutlierDetector(threshold=2.0)


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        OutlierDetector(threshold=0)


def test_negative_threshold_raises():
    with pytest.raises(ValueError):
        OutlierDetector(threshold=-1.5)


def test_detect_returns_outlier_report(detector, result):
    report = detector.detect(result)
    assert isinstance(report, OutlierReport)


def test_outlier_detected(detector, result):
    report = detector.detect(result)
    assert report.has_outliers


def test_outlier_is_execute_stage(detector, result):
    report = detector.detect(result)
    names = [o.stage.name for o in report.outliers]
    assert "execute" in names


def test_outlier_z_score_positive(detector, result):
    report = detector.detect(result)
    execute_outlier = next(o for o in report.outliers if o.stage.name == "execute")
    assert execute_outlier.z_score > 0


def test_no_outliers_when_uniform():
    uniform_stages = [Stage(name=f"s{i}", duration_ms=50.0) for i in range(4)]
    r = ProfileResult(query="Q", stages=uniform_stages, total_duration_ms=200.0)
    detector = OutlierDetector(threshold=2.0)
    report = detector.detect(r)
    assert not report.has_outliers


def test_report_mean_ms(detector, result):
    report = detector.detect(result)
    assert report.mean_ms == pytest.approx((10 + 12 + 200 + 11) / 4, rel=1e-3)


def test_report_stdev_ms_positive(detector, result):
    report = detector.detect(result)
    assert report.stdev_ms > 0


def test_outlier_repr(detector, result):
    report = detector.detect(result)
    o = report.outliers[0]
    assert "OutlierStage" in repr(o)
    assert "execute" in repr(o)


def test_summary_contains_query(detector, result):
    report = detector.detect(result)
    assert "SELECT 1" in report.summary()


def test_summary_no_outliers_message():
    uniform_stages = [Stage(name=f"s{i}", duration_ms=50.0) for i in range(4)]
    r = ProfileResult(query="Q", stages=uniform_stages, total_duration_ms=200.0)
    report = OutlierDetector(threshold=2.0).detect(r)
    assert "No outlier stage" in report.summary()


def test_single_stage_no_outliers():
    r = ProfileResult(
        query="Q",
        stages=[Stage(name="only", duration_ms=99.0)],
        total_duration_ms=99.0,
    )
    report = OutlierDetector(threshold=2.0).detect(r)
    assert not report.has_outliers


def test_error_stages_excluded():
    stages = [
        Stage(name="a", duration_ms=10.0),
        Stage(name="b", duration_ms=10.0),
        Stage(name="bad", duration_ms=0.0, error="timeout"),
    ]
    r = ProfileResult(query="Q", stages=stages, total_duration_ms=20.0)
    report = OutlierDetector(threshold=1.0).detect(r)
    names = [o.stage.name for o in report.outliers]
    assert "bad" not in names
