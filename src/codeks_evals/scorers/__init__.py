from .exact import exact_match
from .schema import json_schema

BUILTIN = {"exact": exact_match, "schema": json_schema}

__all__ = ["BUILTIN", "exact_match", "json_schema"]
