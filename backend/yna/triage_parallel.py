from __future__ import annotations

import json
import os
import uuid
from typing import Any

from .intake import SupabaseREST, utcnow
from .model_router import OpenAIResponses
from .triage import (
    CAPABILITY, INSTRUCTIONS, OUTPUT_SCHEMA_VERSION, POLICY_VERSION, SCHEMA,
    _company, _eligible_roles, _ensure_description, _persist_result,
    _passed_run, _private_context, _reconcile_durable_decision,
    _source_evidence, semantic_input_hash,
)

DEFAULT_LIMIT = 96
MAX_LIMIT = 160
DEFAULT_BATCH_SIZE = 8
MAX_BATCH_SIZE = 12

BATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decisions"],
    "properties": {
        "decisions": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_BATCH_SIZE,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["opportunity_id", *SCHEMA["required"]],
                "properties": {"opportunity_id": {"type": "string"}, **SCHEMA["properties"]},
            },
        }
    },
}


def _context(db: SupabaseREST, role: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    company = _company(db, role["company_id"])
    description = _ensure_description(db, role)
    sources = _source_evidence(db, role["id"])
    return ({
        "id": role["id"],
        "company": company.get("display_name"),
        "title": role.get("title"),
        "location": role.get("location"),
        "description": description[:18000],
        "posted_at": role.get("posted_at"),
        "first_seen_at": role.get("first_seen_at"),
        "last_seen_at": role.get("last_seen_at"),
        "source_evidence": sources,
    }, sources)


def validate_batch_decisions(result: dict[str, Any], expected_ids: set[str]) -> list[dict[str, Any]]:
    decisions = result.get("decisions") or []
    actual = [str(item.get("opportunity_id") or "") for item in decisions]
    if len(actual) != len(set(actual)) or set(actual) != expected_ids:
        raise RuntimeError("Batch triage response must contain exactly one decision for every claimed opportunity.")
    return decisions


def triage_batch(
    db: SupabaseREST,
    ai: OpenAIResponses,
    roles: list[dict[str, Any]],
    candidate: dict[str, Any],
    pursuit_policy: dict[str, Any],
    candidate_version: str,
    pursuit_policy_version: str,
) -> list[str]:
    contexts: list[dict[str, Any]] = []
    sources_by_id: dict[str, list[dict[str, Any]]] = {}
    hashes_by_id: dict[str, str] = {}
    outcomes: list[str] = []
    for role in roles:
        context, sources = _context(db, role)
        input_hash = semantic_input_hash(
            role, context.get("company"), context.get("description") or "", sources,
            candidate_version, pursuit_policy_version,
        )
        passed = _passed_run(db, role["id"], input_hash)
        if passed and _reconcile_durable_decision(db, role["id"], passed):
            outcomes.append("SKIPPED_UNCHANGED")
            continue
        contexts.append(context)
        sources_by_id[role["id"]] = sources
        hashes_by_id[role["id"]] = input_hash
    if not contexts:
        return outcomes
    request = {
        "opportunities": contexts,
        "candidate_truth": candidate,
        "candidate_truth_version": candidate_version,
        "pursuit_policy": pursuit_policy,
        "pursuit_policy_version": pursuit_policy_version,
        "batch_rule": "Return exactly one independent decision for every opportunity_id. Never let one role's evidence affect another role.",
    }
    trace_id = str(uuid.uuid4())
    runs_by_id: dict[str, str] = {}
    for context in contexts:
        run = db.insert("model_runs", {
            "capability": CAPABILITY,
            "opportunity_id": context["id"],
            "model_class": "STANDARD_REASONING",
            "model_id": "gpt-5.6-sol",
            "reasoning_effort": "high",
            "status": "RUNNING",
            "input_hash": hashes_by_id[context["id"]],
            "output_schema_version": OUTPUT_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "trace_id": trace_id,
            "started_at": utcnow(),
        })[0]
        runs_by_id[context["id"]] = run["id"]
    try:
        result, raw, route = ai.structured(
            CAPABILITY,
            INSTRUCTIONS + "\nBatch requirement: evaluate each supplied opportunity independently and return exactly one decision per opportunity_id.",
            json.dumps(request, ensure_ascii=False),
            "relevance_triage_batch",
            BATCH_SCHEMA,
            model_run_id=next(iter(runs_by_id.values())),
        )
        decisions = validate_batch_decisions(result, {role["id"] for role in roles})
        usage = raw.get("usage") or {}
        divisor = max(1, len(decisions))
        per_role_usage = {
            "input_tokens": int(usage.get("input_tokens") or 0) // divisor,
            "output_tokens": int(usage.get("output_tokens") or 0) // divisor,
        }
        for decision in decisions:
            role_id = decision["opportunity_id"]
            evidence = {
                "mandate_summary": decision["mandate_summary"],
                "supporting_factors": decision["supporting_factors"],
                "constraints": decision["constraints"],
                "material_unknowns": decision["material_unknowns"],
                "authority_signals": decision["authority_signals"],
                "candidate_path": decision["candidate_path"],
                "sources": sources_by_id[role_id],
                "candidate_truth_version": candidate_version,
                "pursuit_policy_version": pursuit_policy_version,
                "batch_trace_id": trace_id,
            }
            _persist_result(db, runs_by_id[role_id], role_id, decision, evidence, route, per_role_usage, trace_id)
            outcomes.append(decision["outcome"])
        return outcomes
    except Exception as exc:
        for run_id in runs_by_id.values():
            db.patch("model_runs", {"id": f"eq.{run_id}", "status": "eq.RUNNING"}, {
                "status": "FAILED",
                "error_text": f"{type(exc).__name__}: {exc}"[:1500],
                "finished_at": utcnow(),
            })
        raise


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret or not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("SUPABASE_SECRET_KEY and OPENAI_API_KEY are required")
    url = os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co")
    limit = max(1, min(int(os.environ.get("TRIAGE_LIMIT", str(DEFAULT_LIMIT))), MAX_LIMIT))
    batch_size = max(1, min(int(os.environ.get("TRIAGE_BATCH_SIZE", str(DEFAULT_BATCH_SIZE))), MAX_BATCH_SIZE))
    db = SupabaseREST(url, secret)
    ai = OpenAIResponses()
    candidate, pursuit_policy, candidate_version, pursuit_policy_version = _private_context(db)
    roles = _eligible_roles(db, limit)
    results = {"RELEVANT": 0, "POSSIBLE": 0, "CLEAR_NO": 0, "SKIPPED_UNCHANGED": 0, "FAILED": 0}
    attempted = 0
    for start in range(0, len(roles), batch_size):
        batch = roles[start:start + batch_size]
        attempted += len(batch)
        try:
            for outcome in triage_batch(db, ai, batch, candidate, pursuit_policy, candidate_version, pursuit_policy_version):
                results[outcome] += 1
        except Exception as exc:
            results["FAILED"] += len(batch)
            db.insert("activity_events", {
                "event_type": "RELEVANCE_TRIAGE_FAILED",
                "severity": "ATTENTION",
                "message": "A claimed triage batch failed; every role remains awaiting triage for idempotent retry.",
                "details": {"opportunity_ids": [role["id"] for role in batch], "error": f"{type(exc).__name__}: {exc}"[:1000]},
            })
            # A batch-level provider or schema failure is shared evidence about the
            # worker, not eight independent role outcomes. Stop claiming more work;
            # later roles remain untouched and the scheduler can retry after recovery.
            break
    evaluated = results["RELEVANT"] + results["POSSIBLE"] + results["CLEAR_NO"] + results["SKIPPED_UNCHANGED"]
    unclaimed = len(roles) - attempted
    db.insert("activity_events", {
        "event_type": "RELEVANCE_TRIAGE_BATCH_COMPLETED",
        "severity": "INFO" if results["FAILED"] == 0 else "ATTENTION",
        "message": f"Mandate relevance triage evaluated {evaluated} of {attempted} attempted roles; {unclaimed} selected roles remained unclaimed.",
        "details": {**results, "selected": len(roles), "attempted": attempted, "evaluated": evaluated, "unclaimed": unclaimed, "batch_size": batch_size, "limit": limit},
    })
    print(json.dumps({**results, "selected": len(roles), "attempted": attempted, "evaluated": evaluated, "unclaimed": unclaimed, "batch_size": batch_size, "limit": limit}, sort_keys=True))
    return 0 if results["FAILED"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
