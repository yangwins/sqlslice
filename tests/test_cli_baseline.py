"""Tests for sqlslice.cli_baseline module."""

import json
import pytest

from sqlslice.profiler import ProfileResult, Stage
from sqlslice.baseline import BaselineStore
from sqlslice.cli_baseline import main


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "test_baselines.json")


@pytest.fixture
def populated_store(store_path):
    store = BaselineStore(path=store_path)
    stages = [Stage(name="parse", duration=0.02), Stage(name="run", duration=0.18)]
    result = ProfileResult(query="SELECT count(*) FROM t", stages=stages)
    store.save("baseline_a", result)
    store.save("baseline_b", result)
    return store_path


def test_list_empty(store_path, capsys):
    main(["--store", store_path, "list"])
    out = capsys.readouterr().out
    assert "No baselines" in out


def test_list_shows_names(populated_store, capsys):
    main(["--store", populated_store, "list"])
    out = capsys.readouterr().out
    assert "baseline_a" in out
    assert "baseline_b" in out


def test_list_shows_total(populated_store, capsys):
    main(["--store", populated_store, "list"])
    out = capsys.readouterr().out
    assert "total=" in out


def test_show_displays_query(populated_store, capsys):
    main(["--store", populated_store, "show", "baseline_a"])
    out = capsys.readouterr().out
    assert "SELECT count" in out


def test_show_displays_stages(populated_store, capsys):
    main(["--store", populated_store, "show", "baseline_a"])
    out = capsys.readouterr().out
    assert "parse" in out
    assert "run" in out


def test_show_missing_exits(store_path):
    with pytest.raises(SystemExit) as exc:
        main(["--store", store_path, "show", "ghost"])
    assert exc.value.code == 1


def test_delete_existing(populated_store, capsys):
    main(["--store", populated_store, "delete", "baseline_a"])
    out = capsys.readouterr().out
    assert "Deleted" in out
    store = BaselineStore(path=populated_store)
    assert store.load("baseline_a") is None


def test_delete_nonexistent_exits(store_path):
    with pytest.raises(SystemExit) as exc:
        main(["--store", store_path, "delete", "missing"])
    assert exc.value.code == 1


def test_delete_preserves_other(populated_store):
    main(["--store", populated_store, "delete", "baseline_a"])
    store = BaselineStore(path=populated_store)
    assert store.load("baseline_b") is not None
