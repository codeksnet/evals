import json

import pytest

from codeks_evals import load_cases, run_eval
from codeks_evals.cli import main


def fake_target(inp):
    return {"2+2": "4", "capital of France": "Lyon", "make a task": json.dumps({"title": "x", "done": False})}[inp]


def test_load_cases(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"id":"a","input":"i","expected":"o"}\n\n')
    assert [c.id for c in load_cases(p)] == ["a"]


def test_invalid_case_reports_line(tmp_path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"input":"i"}\n')
    with pytest.raises(ValueError, match=":1:"):
        load_cases(p)


def test_run_eval_scores():
    res = run_eval(load_cases("evalsets/example.jsonl"), fake_target)
    assert (res.passed, res.total) == (2, 3)


def test_schema_rejects_bool_as_number():
    from codeks_evals import Case
    from codeks_evals.scorers import json_schema
    ok, _ = json_schema(Case("c", "i", {"n": "number"}), '{"n": true}')
    assert not ok


def test_cli_gate(capsys):
    assert main(["run", "evalsets/example.jsonl", "--target", "tests.test_core:fake_target",
                 "--min-pass-rate", "0.5"]) == 0
    assert main(["run", "evalsets/example.jsonl", "--target", "tests.test_core:fake_target",
                 "--min-pass-rate", "0.9"]) == 1
