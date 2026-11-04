"""LLM-as-judge scorer.

A case using `"scorer": "judge"` puts a plain-English rubric in `expected`. The judge model
sees the input, the output and the rubric and answers with JSON: {"pass": bool, "reason": str}.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable

DEFAULT_JUDGE_MODEL = "claude-haiku-5-5"

PROMPT = """You are grading the output of an AI system against a rubric.

<input>
{input}
</input>

<output>
{output}
</output>

<rubric>
{rubric}
</rubric>

Decide whether the output satisfies the rubric. Reply with only a JSON object:
{{"pass": true or false, "reason": "one short sentence"}}"""


def anthropic_complete(model: str = DEFAULT_JUDGE_MODEL, max_tokens: int = 200) -> Callable[[str], str]:
    """Return a `prompt -> text` function backed by the Anthropic API (needs ANTHROPIC_API_KEY)."""
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover
        raise ImportError("pip install 'codeks-evals[judge]' to use the LLM judge") from e
    client = anthropic.Anthropic()

    def complete(prompt: str) -> str:
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
        )
        return "".join(b.text for b in msg.content if b.type == "text")

    return complete


def _parse(text: str) -> tuple[bool, str]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in judge reply")
    data = json.loads(match.group(0))
    if not isinstance(data.get("pass"), bool):
        raise ValueError("judge reply missing boolean 'pass'")  # noqa: TRY004
    return data["pass"], str(data.get("reason", ""))


def make_llm_judge(complete: Callable[[str], str]):
    """Build a scorer from any `prompt -> text` function. Judge failures count as failures."""

    def llm_judge(case, output: str) -> tuple[bool, str]:
        prompt = PROMPT.format(input=case.input, output=output, rubric=case.expected)
        try:
            return _parse(complete(prompt))
        except Exception as e:  # noqa: BLE001 - a broken judge must never silently pass a case
            return False, f"judge error: {e}"

    return llm_judge
