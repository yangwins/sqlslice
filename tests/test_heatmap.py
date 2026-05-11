"""Tests for sqlslice.heatmap."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.heatmap import (
    HeatCell,
    HeatmapReport,
    QueryHeatmap,
    _intensity_char,
)


def _make_result(durations: dict, query: str = "SELECT 1") -> ProfileResult:
    stages = [Stage(name=k, duration_ms=v) for k, v in durations.items()]
    total = sum(durations.values())
    return ProfileResult(query=query, stages=stages, total_duration_ms=total)


@pytest.fixture
def heatmap():
    return QueryHeatmap(query="SELECT 1")


# ---------------------------------------------------------------------------
# HeatCell
# ---------------------------------------------------------------------------

def test_heat_cell_repr():
    cell = HeatCell(stage_name="parse", run_index=0, duration_ms=12.5, intensity=0.8)
    assert "parse" in repr(cell)
    assert "12.50" in repr(cell)


# ---------------------------------------------------------------------------
# _intensity_char
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("val,expected", [
    (0.0, "░"),
    (0.24, "░"),
    (0.25, "▒"),
    (0.49, "▒"),
    (0.5, "▓"),
    (0.74, "▓"),
    (0.75, "█"),
    (1.0, "█"),
])
def test_intensity_char(val, expected):
    assert _intensity_char(val) == expected


# ---------------------------------------------------------------------------
# QueryHeatmap.build
# ---------------------------------------------------------------------------

def test_build_raises_when_empty(heatmap):
    with pytest.raises(ValueError, match="No results"):
        heatmap.build()


def test_add_invalid_type_raises(heatmap):
    with pytest.raises(TypeError):
        heatmap.add("not a result")  # type: ignore


def test_build_returns_heatmap_report(heatmap):
    heatmap.add(_make_result({"parse": 10.0, "execute": 20.0}))
    heatmap.add(_make_result({"parse": 15.0, "execute": 25.0}))
    report = heatmap.build()
    assert isinstance(report, HeatmapReport)


def test_run_count(heatmap):
    for _ in range(3):
        heatmap.add(_make_result({"parse": 10.0}))
    report = heatmap.build()
    assert report.run_count == 3


def test_stage_names_preserved(heatmap):
    heatmap.add(_make_result({"parse": 5.0, "plan": 8.0, "execute": 30.0}))
    heatmap.add(_make_result({"parse": 6.0, "plan": 9.0, "execute": 28.0}))
    report = heatmap.build()
    assert report.stage_names == ["parse", "plan", "execute"]


def test_cell_count(heatmap):
    heatmap.add(_make_result({"parse": 5.0, "execute": 20.0}))
    heatmap.add(_make_result({"parse": 7.0, "execute": 22.0}))
    report = heatmap.build()
    assert len(report.cells) == 4  # 2 stages * 2 runs


def test_hottest_cell_has_max_intensity(heatmap):
    heatmap.add(_make_result({"execute": 10.0}))
    heatmap.add(_make_result({"execute": 50.0}))
    report = heatmap.build()
    intensities = [c.intensity for c in report.cells if c.stage_name == "execute"]
    assert max(intensities) == pytest.approx(1.0)


def test_coolest_cell_has_min_intensity(heatmap):
    heatmap.add(_make_result({"execute": 10.0}))
    heatmap.add(_make_result({"execute": 50.0}))
    report = heatmap.build()
    intensities = [c.intensity for c in report.cells if c.stage_name == "execute"]
    assert min(intensities) == pytest.approx(0.0)


def test_uniform_stage_has_zero_intensity(heatmap):
    """When all runs have the same duration, intensity should be 0."""
    for _ in range(3):
        heatmap.add(_make_result({"parse": 10.0}))
    report = heatmap.build()
    for cell in report.cells:
        assert cell.intensity == pytest.approx(0.0)


def test_summary_contains_query(heatmap):
    heatmap.add(_make_result({"parse": 5.0}))
    report = heatmap.build()
    assert "SELECT 1" in report.summary()


def test_summary_contains_stage_name(heatmap):
    heatmap.add(_make_result({"parse": 5.0, "execute": 20.0}))
    report = heatmap.build()
    summary = report.summary()
    assert "parse" in summary
    assert "execute" in summary


def test_query_override():
    hm = QueryHeatmap(query="CUSTOM QUERY")
    hm.add(_make_result({"parse": 5.0}, query="SELECT 1"))
    report = hm.build()
    assert report.query == "CUSTOM QUERY"


def test_query_inferred_from_first_result():
    hm = QueryHeatmap()  # no explicit query
    hm.add(_make_result({"parse": 5.0}, query="SELECT 42"))
    report = hm.build()
    assert report.query == "SELECT 42"
