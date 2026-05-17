"""Pipeline: chain multiple profiling stages into a single pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Any

from sqlslice.profiler import ProfileResult


@dataclass
class PipelineStep:
    name: str
    transform: Callable[[ProfileResult], Any]

    def __repr__(self) -> str:
        return f"PipelineStep(name={self.name!r})"


@dataclass
class PipelineReport:
    query: str
    steps: List[str]
    results: dict = field(default_factory=dict)

    def summary(self) -> str:
        lines = [f"Pipeline for: {self.query}", f"Steps ({len(self.steps)}):"]  
        for step in self.steps:
            lines.append(f"  - {step}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"PipelineReport(query={self.query!r}, steps={self.steps!r})"


class QueryPipeline:
    """Chains multiple analysis steps over a single ProfileResult."""

    def __init__(self) -> None:
        self._steps: List[PipelineStep] = []

    def add_step(self, name: str, transform: Callable[[ProfileResult], Any]) -> "QueryPipeline":
        if not name or not isinstance(name, str):
            raise ValueError("Step name must be a non-empty string.")
        if not callable(transform):
            raise TypeError("transform must be callable.")
        self._steps.append(PipelineStep(name=name, transform=transform))
        return self

    def run(self, result: ProfileResult) -> PipelineReport:
        if not self._steps:
            raise RuntimeError("Pipeline has no steps. Add at least one step before running.")
        report = PipelineReport(
            query=result.query,
            steps=[s.name for s in self._steps],
            results={},
        )
        for step in self._steps:
            report.results[step.name] = step.transform(result)
        return report

    def step_count(self) -> int:
        return len(self._steps)

    def __repr__(self) -> str:
        return f"QueryPipeline(steps={[s.name for s in self._steps]!r})"
