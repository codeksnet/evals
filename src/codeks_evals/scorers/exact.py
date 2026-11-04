from __future__ import annotations


def exact_match(case, output: str) -> tuple[bool, str]:
    ok = output.strip() == str(case.expected).strip()
    return ok, "" if ok else f"expected {case.expected!r}, got {output!r}"
