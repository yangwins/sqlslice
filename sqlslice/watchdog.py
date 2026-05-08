"""Watchdog module: monitors repeated query runs and alerts when duration exceeds a threshold."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from sqlslice.profiler import ProfileResult


@dataclass
class WatchdogAlert:
    query: str
    run_index: int
    total_duration: float
    threshold: float
    message: str = ""

    def __post_init__(self):
        if not self.message:
            self.message = (
                f"Query '{self.query}' exceeded threshold: "
                f"{self.total_duration:.4f}s > {self.threshold:.4f}s (run #{self.run_index})"
            )

    def __repr__(self) -> str:
        return f"WatchdogAlert(run={self.run_index}, duration={self.total_duration:.4f}s, threshold={self.threshold:.4f}s)"


@dataclass
class WatchdogReport:
    query: str
    threshold: float
    alerts: List[WatchdogAlert] = field(default_factory=list)
    total_runs: int = 0

    @property
    def alert_count(self) -> int:
        return len(self.alerts)

    @property
    def clean_runs(self) -> int:
        return self.total_runs - self.alert_count

    def summary(self) -> str:
        lines = [
            f"Watchdog Report for: {self.query}",
            f"  Threshold : {self.threshold:.4f}s",
            f"  Total runs: {self.total_runs}",
            f"  Alerts    : {self.alert_count}",
            f"  Clean runs: {self.clean_runs}",
        ]
        for alert in self.alerts:
            lines.append(f"  [!] {alert.message}")
        return "\n".join(lines)


class QueryWatchdog:
    """Watches a sequence of ProfileResults and fires alerts when total duration exceeds threshold."""

    def __init__(
        self,
        threshold: float,
        on_alert: Optional[Callable[[WatchdogAlert], None]] = None,
    ):
        if threshold <= 0:
            raise ValueError("threshold must be a positive number")
        self.threshold = threshold
        self.on_alert = on_alert

    def watch(self, results: List[ProfileResult]) -> WatchdogReport:
        if not results:
            raise ValueError("results list must not be empty")

        query = results[0].query
        report = WatchdogReport(query=query, threshold=self.threshold, total_runs=len(results))

        for idx, result in enumerate(results):
            duration = sum(s.duration for s in result.stages)
            if duration > self.threshold:
                alert = WatchdogAlert(
                    query=result.query,
                    run_index=idx,
                    total_duration=duration,
                    threshold=self.threshold,
                )
                report.alerts.append(alert)
                if self.on_alert:
                    self.on_alert(alert)

        return report
