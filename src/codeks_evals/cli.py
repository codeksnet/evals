"""`codeks-evals run` — score an eval set and gate a PR on pass rate."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

from .baseline import compare, save_baseline
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
    r.add_argument("--name", help="run name for Supabase/Langfuse (default: eval set filename)")
    r.add_argument("--min-pass-rate", type=float, help="exit 1 if pass rate is below this (0-1)")
    r.add_argument("--baseline", help="baseline JSON; exit 1 if pass rate drops vs. it")
    r.add_argument("--max-drop", type=float, default=0.0,
                   help="allowed pass-rate drop vs. baseline (default 0)")
    r.add_argument("--save-baseline", metavar="PATH", help="write this run as the new baseline")
    r.add_argument("--judge-model", help="model for `judge` cases (default: claude-haiku-5-5)")
    r.add_argument("--supabase", action="store_true", help="save the run to Supabase (SUPABASE_*)")
    r.add_argument("--langfuse", action="store_true", help="send a trace to Langfuse (LANGFUSE_*)")
    r.add_argument("--out", help="write full results as JSON")
    args = p.parse_args(argv)

    cases = load_cases(args.evalset)
    scorers = {}
    if any(c.scorer == "judge" for c in cases):
        from .scorers.judge import DEFAULT_JUDGE_MODEL, anthropic_complete, make_llm_judge

        scorers["judge"] = make_llm_judge(anthropic_complete(args.judge_model or DEFAULT_JUDGE_MODEL))

    result = run_eval(cases, _load_target(args.target), scorers)
    print(f"{result.passed}/{result.total} passed ({result.pass_rate:.0%})")
    for c in result.results:
        if not c.passed:
            print(f"  FAIL {c.case_id}: {c.detail}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

    name = args.name or os.path.splitext(os.path.basename(args.evalset))[0]
    trace_url = None
    if args.langfuse:
        from .sinks.langfuse import report_to_langfuse

        trace_url = report_to_langfuse(result, name)
        print(f"langfuse: {trace_url}")
    if args.supabase:
        from .sinks.supabase import SupabaseSink

        run_id = SupabaseSink.from_env().save(
            result, name, git_sha=os.environ.get("GITHUB_SHA"), trace_url=trace_url
        )
        print(f"supabase run: {run_id}")

    failed = False
    if args.min_pass_rate is not None and result.pass_rate < args.min_pass_rate:
        print(f"pass rate {result.pass_rate:.2f} < floor {args.min_pass_rate:.2f}", file=sys.stderr)
        failed = True
    if args.baseline:
        cmp = compare(result, args.baseline, args.max_drop)
        print(f"baseline {cmp.baseline_rate:.0%} -> {cmp.current_rate:.0%}")
        if cmp.newly_failing:
            print(f"  newly failing: {', '.join(cmp.newly_failing)}")
        if cmp.regressed:
            print(f"pass rate dropped more than {args.max_drop:.0%} vs. baseline", file=sys.stderr)
            failed = True
    if args.save_baseline:
        save_baseline(result, args.save_baseline)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
