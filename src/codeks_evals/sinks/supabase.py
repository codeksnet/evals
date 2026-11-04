"""Store runs in Supabase. Schema: supabase/migrations/0001_eval_runs.sql."""
from __future__ import annotations

import os
from typing import Any

from ..core import RunResult


class SupabaseSink:
    def __init__(self, client: Any, schema: str = "evals"):
        self.client = client
        self.schema = schema

    @classmethod
    def from_env(cls, schema: str = "evals") -> SupabaseSink:
        from supabase import create_client

        client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
        return cls(client, schema)

    def save(self, run: RunResult, name: str, git_sha: str | None = None,
             trace_url: str | None = None) -> str:
        """Insert one run row and its case rows. Returns the run id."""
        db = self.client.schema(self.schema)
        latencies = [r.latency_s for r in run.results]
        row = {
            "name": name,
            "git_sha": git_sha,
            "total": run.total,
            "passed": run.passed,
            "pass_rate": run.pass_rate,
            "avg_latency_s": sum(latencies) / len(latencies) if latencies else 0,
            "trace_url": trace_url,
        }
        run_id = db.table("runs").insert(row).execute().data[0]["id"]
        if run.results:
            db.table("run_cases").insert([
                {
                    "run_id": run_id,
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "output": r.output,
                    "detail": r.detail,
                    "latency_s": r.latency_s,
                }
                for r in run.results
            ]).execute()
        return run_id
