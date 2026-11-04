"""`codeks-evals run` — gate a PR on pass rate against a baseline."""
from __future__ import annotations

import argparse
import importlib
import json
import sys

from .core import load_cases, run_eval


def _load_target(spec: str):
    module, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module), attr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="codeks-evals")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run an eval set against a target function")
    r.add_argument("evalset", help="path to a JSONL eval set")
    r.add_argument("--target", required=True, help="module:function, takes input, returns str")
    r.add_argument("--min-pass-rate", type=float, default=None,
                   help="exit 1 if pass rate is below this (0-1)")
    r.add_argument("--out", help="write full results as JSON")
    args = p.parse_args(argv)

    result = run_eval(load_cases(args.evalset), _load_target(args.target))
    print(f"{result.passed}/{result.total} passed ({result.pass_rate:.0%})")
    for c in result.results:
        if not c.passed:
            print(f"  FAIL {c.case_id}: {c.detail}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
    if args.min_pass_rate is not None and result.pass_rate < args.min_pass_rate:
        print(f"pass rate {result.pass_rate:.2f} < {args.min_pass_rate:.2f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
