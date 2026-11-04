from __future__ import annotations

import json

_TYPES = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def json_schema(case, output: str) -> tuple[bool, str]:
    """Minimal check: output is a JSON object with the keys/types in case.expected.

    `expected` is a mapping of key -> JSON type name, e.g. {"title": "string"}.
    """
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        return False, f"output is not valid JSON ({e})"
    if not isinstance(data, dict):
        return False, "output is not a JSON object"
    for key, type_name in (case.expected or {}).items():
        if key not in data:
            return False, f"missing key {key!r}"
        if not isinstance(data[key], _TYPES[type_name]) or (
            type_name != "boolean" and isinstance(data[key], bool)
        ):
            return False, f"key {key!r} is not {type_name}"
    return True, ""
