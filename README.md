# codeks-evals

A small eval harness for LLM features. Write cases as JSONL, score outputs, and fail the PR when the pass rate drops.

> Status: early. Core runner, exact-match and schema scorers, and the CI gate work today. LLM-judge scoring, Supabase results, Langfuse traces and the dashboard are next (see the [roadmap](https://github.com/codeksnet/labs/blob/main/docs/PLAN.md)).

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

## Roadmap

- [x] JSONL loader, runner, exact-match + schema scorers, CLI gate
- [ ] LLM-judge scorer
- [ ] Results to Supabase, Langfuse trace per run
- [ ] Reusable GitHub Action that compares against the baseline on `main`
- [ ] Next.js dashboard (lives in [codeksnet/labs](https://github.com/codeksnet/labs))
- [ ] Target eval set: ResumeMaster suggestion prompt, ~30 synthetic cases

Maintained by [Fortan Pireva](https://github.com/FortanPireva) at [Codeks](https://codeks.net). MIT licensed.
