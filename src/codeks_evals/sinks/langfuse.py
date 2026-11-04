"""Send a run to Langfuse as one trace: a span per case, with a pass score on each."""
from __future__ import annotations

from typing import Any

from ..core import RunResult


def report_to_langfuse(run: RunResult, name: str, client: Any = None) -> str | None:
    """Create a trace for the run and return its URL. Reads LANGFUSE_* env vars if no client."""
    if client is None:
        from langfuse import Langfuse

        client = Langfuse()
    trace_id = client.create_trace_id()
    with client.start_as_current_observation(
        trace_context={"trace_id": trace_id},
        name=f"eval:{name}",
        output={"passed": run.passed, "total": run.total, "pass_rate": run.pass_rate},
    ):
        for r in run.results:
            with client.start_as_current_observation(
                name=r.case_id,
                output=r.output,
                metadata={"passed": r.passed, "detail": r.detail, "latency_s": r.latency_s},
            ):
                pass
    client.create_score(
        trace_id=trace_id, name="pass_rate", value=run.pass_rate, data_type="NUMERIC"
    )
    client.flush()
    return client.get_trace_url(trace_id=trace_id)
