from __future__ import annotations

from typing import Any

from .intake import SupabaseREST


def reusable_model_run(
    db: SupabaseREST,
    *,
    capability: str,
    input_hash: str,
    policy_version: str,
    output_schema_version: str,
    opportunity_id: str | None,
) -> dict[str, Any] | None:
    """Return one exact successful paid result identity, never a near match."""
    filters: dict[str, str] = {
        "capability": f"eq.{capability}",
        "input_hash": f"eq.{input_hash}",
        "policy_version": f"eq.{policy_version}",
        "output_schema_version": f"eq.{output_schema_version}",
        "status": "eq.PASSED",
        "select": "id,trace_id,model_class,model_id,reasoning_effort,finished_at,input_hash,policy_version,output_schema_version",
        "order": "finished_at.desc",
        "limit": "1",
    }
    filters["opportunity_id"] = f"eq.{opportunity_id}" if opportunity_id else "is.null"
    rows = db.select("model_runs", filters)
    return rows[0] if rows else None
