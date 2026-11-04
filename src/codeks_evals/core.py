"""Core types and the eval runner."""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A scorer takes (case, output) and returns (passed, detail).
Scorer = Callable[["Case", str], "tuple[bool, str]"]


@dataclass
class Case:
    id: str
    input: Any
    expected: Any = None
    scorer: str = "exact"
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    output: str
    detail: str
    latency_s: float


@dataclass
class RunResult:
    results: list[CaseResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "results": [r.__dict__ for r in self.results],
        }


def load_cases(path: str | Path) -> list[Case]:
    """Load a JSONL eval set. One JSON object per line; blank lines are skipped."""
    cases: list[Case] = []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            cases.append(
                Case(
                    id=str(row["id"]),
                    input=row["input"],
                    expected=row.get("expected"),
                    scorer=row.get("scorer", "exact"),
                    meta=row.get("meta", {}),
                )
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"{path}:{n}: invalid case ({e})") from e
    return cases


def run_eval(
    cases: list[Case],
    target: Callable[[Any], str],
    scorers: dict[str, Scorer] | None = None,
) -> RunResult:
    """Run `target` on every case and score the output."""
    from .scorers import BUILTIN

    table = {**BUILTIN, **(scorers or {})}
    results: list[CaseResult] = []
    for case in cases:
        if case.scorer not in table:
            raise ValueError(f"case {case.id}: unknown scorer {case.scorer!r}")
        start = time.perf_counter()
        output = target(case.input)
        latency = time.perf_counter() - start
        passed, detail = table[case.scorer](case, output)
        results.append(CaseResult(case.id, passed, output, detail, latency))
    return RunResult(results)
