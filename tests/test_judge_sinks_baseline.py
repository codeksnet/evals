from types import SimpleNamespace

from codeks_evals import Case, CaseResult, RunResult, load_cases, run_eval
from codeks_evals.baseline import compare, save_baseline
from codeks_evals.cli import main
from codeks_evals.scorers import make_llm_judge
from codeks_evals.sinks import SupabaseSink, report_to_langfuse


def case(**kw):
    return Case(**{"id": "c", "input": "q", "expected": "is polite", **kw})


def test_judge_pass_and_fail():
    ok = make_llm_judge(lambda p: 'Sure: {"pass": true, "reason": "ok"}')
    bad = make_llm_judge(lambda p: '{"pass": false, "reason": "rude"}')
    assert ok(case(), "hi") == (True, "ok")
    assert bad(case(), "hi") == (False, "rude")


def test_judge_prompt_contains_rubric_and_output():
    seen = []
    make_llm_judge(lambda p: seen.append(p) or '{"pass": true}')(case(), "OUT")
    assert "is polite" in seen[0] and "OUT" in seen[0]


def test_judge_garbage_or_exception_fails_closed():
    assert make_llm_judge(lambda p: "no json")(case(), "x")[0] is False
    assert make_llm_judge(lambda p: '{"pass": "yes"}')(case(), "x")[0] is False

    def boom(p):
        raise RuntimeError("down")

    ok, detail = make_llm_judge(boom)(case(), "x")
    assert not ok and "down" in detail


def mkrun(*passed):
    return RunResult([CaseResult(f"c{i}", p, "o", "d", 0.1) for i, p in enumerate(passed)])


def test_baseline_regression(tmp_path):
    path = tmp_path / "b.json"
    save_baseline(mkrun(True, True, True, False), path)
    same = compare(mkrun(True, True, True, False), path)
    assert not same.regressed
    worse = compare(mkrun(True, False, True, False), path)
    assert worse.regressed and worse.newly_failing == ["c1"]
    assert not compare(mkrun(True, False, True, False), path, max_drop=0.25).regressed


class FakeTable:
    def __init__(self, store, name):
        self.store, self.name = store, name

    def insert(self, rows):
        self.rows = rows
        self.store.setdefault(self.name, []).append(rows)
        return self

    def execute(self):
        return SimpleNamespace(data=[{"id": "run-1"}])


class FakeSupabase:
    def __init__(self):
        self.store = {}

    def schema(self, _):
        return self

    def table(self, name):
        return FakeTable(self.store, name)


def test_supabase_sink():
    fake = FakeSupabase()
    run_id = SupabaseSink(fake).save(mkrun(True, False), "demo", git_sha="abc")
    assert run_id == "run-1"
    assert fake.store["runs"][0]["pass_rate"] == 0.5
    assert [r["case_id"] for r in fake.store["run_cases"][0]] == ["c0", "c1"]


class FakeLangfuse:
    def __init__(self):
        self.spans, self.scores, self.flushed = [], [], False

    def create_trace_id(self):
        return "t1"

    def start_as_current_observation(self, **kw):
        self.spans.append(kw["name"])
        from contextlib import nullcontext
        return nullcontext()

    def create_score(self, **kw):
        self.scores.append(kw)

    def flush(self):
        self.flushed = True

    def get_trace_url(self, trace_id):
        return f"https://lf/{trace_id}"


def test_langfuse_report():
    lf = FakeLangfuse()
    url = report_to_langfuse(mkrun(True, False), "demo", client=lf)
    assert url == "https://lf/t1" and lf.flushed
    assert lf.spans == ["eval:demo", "c0", "c1"]
    assert lf.scores[0]["value"] == 0.5


def good_target(inp):
    return {"2+2": "4", "capital of France": "Paris"}.get(inp, '{"title": "x", "done": true}')


def test_cli_baseline_roundtrip(tmp_path):
    base = str(tmp_path / "base.json")
    args = ["run", "evalsets/example.jsonl", "--target", "tests.test_judge_sinks_baseline:good_target"]
    assert main(args + ["--save-baseline", base]) == 0
    assert main(args + ["--baseline", base]) == 0
    # a target that now fails everything regresses against that baseline
    bad = ["run", "evalsets/example.jsonl", "--target", "tests.test_core:fake_target",
           "--baseline", base]
    assert main(bad) == 1


def test_run_eval_uses_custom_judge_scorer(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"id":"j","input":"q","expected":"polite","scorer":"judge"}\n')
    judge = make_llm_judge(lambda _: '{"pass": true}')
    res = run_eval(load_cases(p), lambda i: "hello", {"judge": judge})
    assert res.passed == 1
