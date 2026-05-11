"""Stage-level time budget enforcement for SQL query profiling."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlslice.profiler import ProfileResult, Stage


@dataclass
class BudgetViolation:
    stage_name: str
    budget_ms: float
    actual_ms: float

    @property
    def excess_ms(self) -> float:
        return self.actual_ms - self.budget_ms

    def __repr__(self) -> str:
        return (
            f"BudgetViolation(stage={self.stage_name!r}, "
            f"budget={self.budget_ms:.2f}ms, "
            f"actual={self.actual_ms:.2f}ms, "
            f"excess={self.excess_ms:.2f}ms)"
        )


@dataclass
class BudgetReport:
    query: str
    violations: List[BudgetViolation] = field(default_factory=list)
    unchecked_stages: List[str] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def total_excess_ms(self) -> float:
        return sum(v.excess_ms for v in self.violations)

    def summary(self) -> str:
        lines = [f"Budget Report for: {self.query}"]
        if not self.violations:
            lines.append("  All stages within budget.")
        else:
            lines.append(f"  Violations ({len(self.violations)}):")
            for v in self.violations:
                lines.append(
                    f"    [{v.stage_name}] {v.actual_ms:.2f}ms "
                    f"(budget {v.budget_ms:.2f}ms, +{v.excess_ms:.2f}ms)"
                )
        if self.unchecked_stages:
            lines.append(f"  Unchecked stages: {', '.join(self.unchecked_stages)}")
        return "\n".join(lines)


class QueryBudget:
    """Checks a ProfileResult against per-stage time budgets (in ms)."""

    def __init__(self, budgets: Dict[str, float]) -> None:
        if not budgets:
            raise ValueError("budgets dict must not be empty")
        for name, ms in budgets.items():
            if ms <= 0:
                raise ValueError(
                    f"Budget for stage {name!r} must be positive, got {ms}"
                )
        self._budgets = budgets

    def check(self, result: ProfileResult) -> BudgetReport:
        violations: List[BudgetViolation] = []
        unchecked: List[str] = []

        stage_map: Dict[str, Stage] = {s.name: s for s in result.stages}

        for name, budget_ms in self._budgets.items():
            if name not in stage_map:
                unchecked.append(name)
                continue
            actual_ms = stage_map[name].duration_ms
            if actual_ms > budget_ms:
                violations.append(
                    BudgetViolation(
                        stage_name=name,
                        budget_ms=budget_ms,
                        actual_ms=actual_ms,
                    )
                )

        return BudgetReport(
            query=result.query,
            violations=violations,
            unchecked_stages=unchecked,
        )
