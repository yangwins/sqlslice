"""Periodic sampler that captures repeated ProfileResult snapshots over time."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlslice.profiler import ProfileResult


@dataclass
class SamplePoint:
    """A single timed sample captured by the sampler."""

    index: int
    timestamp: float
    result: ProfileResult

    def __repr__(self) -> str:
        status = "ok" if self.result.error is None else "error"
        return f"<SamplePoint index={self.index} ts={self.timestamp:.3f} status={status}>"


@dataclass
class SamplerReport:
    """Aggregated report produced after a sampling session."""

    query: str
    samples: List[SamplePoint] = field(default_factory=list)

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def successful_samples(self) -> List[SamplePoint]:
        return [s for s in self.samples if s.result.error is None]

    @property
    def failed_samples(self) -> List[SamplePoint]:
        return [s for s in self.samples if s.result.error is not None]

    @property
    def average_duration(self) -> Optional[float]:
        durations = [s.result.total_duration for s in self.successful_samples]
        if not durations:
            return None
        return sum(durations) / len(durations)

    @property
    def peak_duration(self) -> Optional[float]:
        durations = [s.result.total_duration for s in self.successful_samples]
        return max(durations) if durations else None

    def summary(self) -> str:
        avg = f"{self.average_duration:.4f}s" if self.average_duration is not None else "n/a"
        peak = f"{self.peak_duration:.4f}s" if self.peak_duration is not None else "n/a"
        return (
            f"Query : {self.query}\n"
            f"Samples: {self.sample_count} total, "
            f"{len(self.successful_samples)} ok, "
            f"{len(self.failed_samples)} failed\n"
            f"Avg    : {avg}\n"
            f"Peak   : {peak}"
        )


class QuerySampler:
    """Runs a profiler callable repeatedly at a fixed interval."""

    def __init__(self, interval: float = 1.0) -> None:
        if interval <= 0:
            raise ValueError("interval must be positive")
        self.interval = interval

    def sample(
        self,
        profiler_fn: Callable[[], ProfileResult],
        count: int,
        on_sample: Optional[Callable[[SamplePoint], None]] = None,
    ) -> SamplerReport:
        """Collect *count* samples, sleeping *interval* seconds between each."""
        if count < 1:
            raise ValueError("count must be at least 1")

        first_result = profiler_fn()
        report = SamplerReport(query=first_result.query)

        for i in range(count):
            if i == 0:
                result = first_result
            else:
                time.sleep(self.interval)
                result = profiler_fn()

            point = SamplePoint(index=i, timestamp=time.time(), result=result)
            report.samples.append(point)

            if on_sample is not None:
                on_sample(point)

        return report
