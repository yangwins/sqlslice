"""Tests for sqlslice.pager."""
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.pager import PageResult, StagePager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage(name=f"stage_{i}", duration_ms=float(i * 10))
        for i in range(1, 8)  # 7 stages
    ]


@pytest.fixture()
def result(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration_ms=280.0)


@pytest.fixture()
def pager():
    return StagePager(page_size=3)


# ---------------------------------------------------------------------------
# StagePager construction
# ---------------------------------------------------------------------------

def test_invalid_page_size_zero_raises():
    with pytest.raises(ValueError, match="page_size"):
        StagePager(page_size=0)


def test_invalid_page_size_negative_raises():
    with pytest.raises(ValueError, match="page_size"):
        StagePager(page_size=-1)


def test_invalid_page_size_non_int_raises():
    with pytest.raises(ValueError, match="page_size"):
        StagePager(page_size=2.5)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# get_page basics
# ---------------------------------------------------------------------------

def test_get_page_returns_page_result(pager, result):
    pr = pager.get_page(result, page=1)
    assert isinstance(pr, PageResult)


def test_get_page_query_preserved(pager, result):
    pr = pager.get_page(result, page=1)
    assert pr.query == "SELECT 1"


def test_get_page_first_page_stage_count(pager, result):
    pr = pager.get_page(result, page=1)
    assert len(pr.stages) == 3


def test_get_page_last_page_partial(pager, result):
    # 7 stages, page_size=3 → page 3 has 1 stage
    pr = pager.get_page(result, page=3)
    assert len(pr.stages) == 1


def test_get_page_correct_stages(pager, result):
    pr = pager.get_page(result, page=2)
    names = [s.name for s in pr.stages]
    assert names == ["stage_4", "stage_5", "stage_6"]


def test_get_page_out_of_range_raises(pager, result):
    with pytest.raises(ValueError, match="out of range"):
        pager.get_page(result, page=99)


def test_get_page_zero_raises(pager, result):
    with pytest.raises(ValueError, match="positive integer"):
        pager.get_page(result, page=0)


# ---------------------------------------------------------------------------
# PageResult properties
# ---------------------------------------------------------------------------

def test_total_pages(pager, result):
    pr = pager.get_page(result, page=1)
    assert pr.total_pages == 3


def test_has_next_true(pager, result):
    pr = pager.get_page(result, page=1)
    assert pr.has_next is True


def test_has_next_false_on_last_page(pager, result):
    pr = pager.get_page(result, page=3)
    assert pr.has_next is False


def test_has_prev_false_on_first_page(pager, result):
    pr = pager.get_page(result, page=1)
    assert pr.has_prev is False


def test_has_prev_true(pager, result):
    pr = pager.get_page(result, page=2)
    assert pr.has_prev is True


def test_summary_contains_query(pager, result):
    pr = pager.get_page(result, page=1)
    assert "SELECT 1" in pr.summary()


def test_summary_contains_page_info(pager, result):
    pr = pager.get_page(result, page=2)
    assert "2 / 3" in pr.summary()


def test_repr_contains_page(pager, result):
    pr = pager.get_page(result, page=1)
    assert "page=1" in repr(pr)


# ---------------------------------------------------------------------------
# all_pages
# ---------------------------------------------------------------------------

def test_all_pages_count(pager, result):
    pages = pager.all_pages(result)
    assert len(pages) == 3


def test_all_pages_covers_all_stages(pager, result):
    pages = pager.all_pages(result)
    all_names = [s.name for p in pages for s in p.stages]
    expected = [f"stage_{i}" for i in range(1, 8)]
    assert all_names == expected
