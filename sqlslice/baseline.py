"""Baseline management: save and load ProfileResult baselines for regression detection."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class BaselineRecord:
    name: str
    query: str
    stages: list[Stage]
    total_duration: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "query": self.query,
            "total_duration": self.total_duration,
            "stages": [
                {"name": s.name, "duration": s.duration, "error": s.error}
                for s in self.stages
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineRecord":
        stages = [
            Stage(name=s["name"], duration=s["duration"], error=s.get("error"))
            for s in data["stages"]
        ]
        return cls(
            name=data["name"],
            query=data["query"],
            stages=stages,
            total_duration=data["total_duration"],
        )

    def __repr__(self) -> str:
        return f"BaselineRecord(name={self.name!r}, total={self.total_duration:.4f}s)"


class BaselineStore:
    """Persist and retrieve named baselines from a JSON file."""

    def __init__(self, path: str = "baselines.json") -> None:
        self.path = path
        self._data: dict[str, dict] = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)

    def save(self, name: str, result: ProfileResult) -> BaselineRecord:
        record = BaselineRecord(
            name=name,
            query=result.query,
            stages=result.stages,
            total_duration=result.total_duration,
        )
        self._data[name] = record.to_dict()
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        return record

    def load(self, name: str) -> Optional[BaselineRecord]:
        entry = self._data.get(name)
        if entry is None:
            return None
        return BaselineRecord.from_dict(entry)

    def list_names(self) -> list[str]:
        return list(self._data.keys())

    def delete(self, name: str) -> bool:
        if name not in self._data:
            return False
        del self._data[name]
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        return True
