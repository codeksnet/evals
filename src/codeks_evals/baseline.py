"""Compare a run against a stored baseline so CI can fail on regressions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .core import RunResult


@dataclass
class Comparison:
    baseline_rate: float
    current_rate: float
    max_drop: float
    newly_failing: list[str]

    @property
    def regressed(self) -> bool:
        return self.baseline_rate - self.current_rate > self.max_drop + 1e-9


def save_baseline(run: RunResult, path: str | Path) -> None:
    data = {
        "pass_rate": run.pass_rate,
        "cases": {r.case_id: r.passed for r in run.results},
    }
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def compare(run: RunResult, path: str | Path, max_drop: float = 0.0) -> Comparison:
    base = json.loads(Path(path).read_text())
    newly_failing = [
        r.case_id for r in run.results if not r.passed and base["cases"].get(r.case_id) is True
    ]
    return Comparison(base["pass_rate"], run.pass_rate, max_drop, newly_failing)
