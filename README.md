# codeks-evals

A small eval harness for LLM features. Write cases as JSONL, score outputs, and fail the PR when the pass rate drops.

> Status: early. Runner, exact-match / schema / LLM-judge scorers, baseline gate, Supabase results and Langfuse traces work (tested against fakes; not yet run against live accounts). The dashboard is next (see the [roadmap](https://github.com/codeksnet/labs/blob/main/docs/PLAN.md)).

## Install

```sh
pip install codeks-evals   # not yet published; use `pip install -e .` for now
```

## Use

An eval set is JSONL, one case per line:

```jsonl
{"id": "ex-1", "input": "2+2", "expected": "4"}
{"id": "ex-3", "input": "make a task", "expected": {"title": "string", "done": "boolean"}, "scorer": "schema"}
```

Point it at a function that takes the input and returns a string, and set a floor:

```sh
codeks-evals run evalsets/example.jsonl --target myapp.llm:suggest --min-pass-rate 0.9
```

Exit code is 1 below the floor, which is what the GitHub Action gates on.

### Scorers

| `scorer` | `expected` | Passes when |
|---|---|---|
| `exact` (default) | a string | output equals it (trimmed) |
| `schema` | `{"key": "string\|number\|integer\|boolean\|array\|object"}` | output is a JSON object with those keys and types |
| `judge` | a plain-English rubric | an LLM judge (default `claude-haiku-5-5`, needs `ANTHROPIC_API_KEY`, `pip install 'codeks-evals[judge]'`) says it meets the rubric. Judge errors fail the case. |

### Gate a PR against a baseline

```sh
codeks-evals run evalsets/x.jsonl --target app:fn --save-baseline evalsets/x.baseline.json  # on main
codeks-evals run evalsets/x.jsonl --target app:fn --baseline evalsets/x.baseline.json --max-drop 0.02
```

Or use the composite action:

```yaml
- uses: codeksnet/evals@main
  with:
    evalset: evalsets/x.jsonl
    target: app:fn
    baseline: evalsets/x.baseline.json
```

### Record runs

- `--supabase` saves the run (needs `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`; apply `supabase/migrations/0001_eval_runs.sql` and add `evals` to the exposed schemas in the Supabase API settings).
- `--langfuse` sends a trace with a span per case and a `pass_rate` score (needs `LANGFUSE_*`).

## Roadmap

- [x] JSONL loader, runner, exact-match + schema scorers, CLI gate
- [x] LLM-judge scorer
- [x] Results to Supabase, Langfuse trace per run
- [x] Reusable GitHub Action that compares against a baseline
- [ ] Next.js dashboard (lives in [codeksnet/labs](https://github.com/codeksnet/labs))
- [ ] Target eval set: ResumeMaster suggestion prompt, ~30 synthetic cases

Maintained by [Fortan Pireva](https://github.com/FortanPireva) at [Codeks](https://codeks.net). MIT licensed.
