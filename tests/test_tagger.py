"""Tests for sqlslice.tagger."""

import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.tagger import TaggedResult, TagRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stages():
    return [
        Stage("parse", 5.0),
        Stage("execute", 40.0),
        Stage("fetch", 10.0),
    ]


@pytest.fixture()
def profile(stages):
    return ProfileResult(query="SELECT 1", stages=stages, total_duration=55.0)


@pytest.fixture()
def registry():
    return TagRegistry()


# ---------------------------------------------------------------------------
# TaggedResult tests
# ---------------------------------------------------------------------------

def test_tagged_result_has_tag(profile):
    tr = TaggedResult(result=profile, tags=["slow", "reporting"])
    assert tr.has_tag("slow")
    assert tr.has_tag("reporting")


def test_tagged_result_has_tag_case_insensitive(profile):
    tr = TaggedResult(result=profile, tags=["SLOW"])
    assert tr.has_tag("slow")


def test_tagged_result_missing_tag(profile):
    tr = TaggedResult(result=profile, tags=["fast"])
    assert not tr.has_tag("slow")


# ---------------------------------------------------------------------------
# TagRegistry.add
# ---------------------------------------------------------------------------

def test_add_returns_tagged_result(registry, profile):
    tr = registry.add(profile, tags=["etl"])
    assert isinstance(tr, TaggedResult)
    assert tr.has_tag("etl")


def test_add_strips_whitespace_from_tags(registry, profile):
    tr = registry.add(profile, tags=["  etl  ", " slow "])
    assert "etl" in tr.tags
    assert "slow" in tr.tags


def test_add_ignores_blank_tags(registry, profile):
    tr = registry.add(profile, tags=["", "   ", "valid"])
    assert tr.tags == ["valid"]


def test_add_without_tags_defaults_to_empty(registry, profile):
    tr = registry.add(profile)
    assert tr.tags == []


def test_count_increments(registry, profile):
    assert registry.count() == 0
    registry.add(profile, tags=["a"])
    registry.add(profile, tags=["b"])
    assert registry.count() == 2


# ---------------------------------------------------------------------------
# TagRegistry.find_by_tag
# ---------------------------------------------------------------------------

def test_find_by_tag_returns_matching(registry, profile):
    registry.add(profile, tags=["slow", "etl"])
    registry.add(profile, tags=["fast"])
    results = registry.find_by_tag("slow")
    assert len(results) == 1
    assert results[0].has_tag("slow")


def test_find_by_tag_case_insensitive(registry, profile):
    registry.add(profile, tags=["SLOW"])
    assert len(registry.find_by_tag("slow")) == 1


def test_find_by_tag_no_match(registry, profile):
    registry.add(profile, tags=["fast"])
    assert registry.find_by_tag("slow") == []


# ---------------------------------------------------------------------------
# TagRegistry.all_tags
# ---------------------------------------------------------------------------

def test_all_tags_deduplicated(registry, profile):
    registry.add(profile, tags=["slow"])
    registry.add(profile, tags=["SLOW", "etl"])
    tags = registry.all_tags()
    assert tags.count("slow") == 1
    assert "etl" in tags


def test_all_tags_sorted(registry, profile):
    registry.add(profile, tags=["zebra", "apple", "mango"])
    assert registry.all_tags() == ["apple", "mango", "zebra"]


# ---------------------------------------------------------------------------
# TagRegistry.summary
# ---------------------------------------------------------------------------

def test_summary_contains_query(registry, profile):
    registry.add(profile, tags=["slow"])
    assert "SELECT 1" in registry.summary()


def test_summary_contains_tag(registry, profile):
    registry.add(profile, tags=["reporting"])
    assert "reporting" in registry.summary()
