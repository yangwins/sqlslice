"""Tests for sqlslice.baseline module."""

import json
import os
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.baseline import BaselineRecord, BaselineStore


@pytest.fixture
def stages():
    return [
        Stage(name="parse", duration=0.01),
        Stage(name="execute", duration=0.25),
        Stage(name="fetch", duration=0.05),
    ]


@pytest.fixture
def profile_result(stages):
    return ProfileResult(query="SELECT 1", stages=stages)


@pytest.fixture
def store(tmp_path):
    return BaselineStore(path=str(tmp_path / "baselines.json"))


def test_save_returns_baseline_record(store, profile_result):
    record = store.save("my_baseline", profile_result)
    assert isinstance(record, BaselineRecord)
    assert record.name == "my_baseline"


def test_saved_record_total_duration(store, profile_result):
    record = store.save("b1", profile_result)
    assert record.total_duration == pytest.approx(profile_result.total_duration)


def test_load_returns_record(store, profile_result):
    store.save("b1", profile_result)
    loaded = store.load("b1")
    assert loaded is not None
    assert loaded.name == "b1"
    assert loaded.query == "SELECT 1"


def test_load_missing_returns_none(store):
    result = store.load("nonexistent")
    assert result is None


def test_loaded_stages_count(store, profile_result, stages):
    store.save("b1", profile_result)
    loaded = store.load("b1")
    assert len(loaded.stages) == len(stages)


def test_loaded_stage_durations(store, profile_result, stages):
    store.save("b1", profile_result)
    loaded = store.load("b1")
    for orig, loaded_stage in zip(stages, loaded.stages):
        assert loaded_stage.duration == pytest.approx(orig.duration)


def test_list_names_empty(store):
    assert store.list_names() == []


def test_list_names_after_save(store, profile_result):
    store.save("alpha", profile_result)
    store.save("beta", profile_result)
    names = store.list_names()
    assert "alpha" in names
    assert "beta" in names


def test_delete_existing(store, profile_result):
    store.save("temp", profile_result)
    removed = store.delete("temp")
    assert removed is True
    assert store.load("temp") is None


def test_delete_nonexistent(store):
    assert store.delete("ghost") is False


def test_persisted_to_disk(tmp_path, profile_result):
    path = str(tmp_path / "baselines.json")
    store1 = BaselineStore(path=path)
    store1.save("disk_test", profile_result)
    store2 = BaselineStore(path=path)
    loaded = store2.load("disk_test")
    assert loaded is not None
    assert loaded.name == "disk_test"


def test_baseline_record_repr(store, profile_result):
    record = store.save("repr_test", profile_result)
    r = repr(record)
    assert "repr_test" in r
    assert "BaselineRecord" in r


def test_baseline_record_with_error_stage(store):
    stages = [Stage(name="execute", duration=0.0, error="timeout")]
    result = ProfileResult(query="SELECT bad", stages=stages)
    record = store.save("err_base", result)
    loaded = store.load("err_base")
    assert loaded.stages[0].error == "timeout"
