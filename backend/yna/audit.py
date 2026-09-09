from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .intake import SupabaseREST
from .model_router import OpenAIResponses, estimated_cost
from .triage import _company, _ensure_description, _private_context, _source_evidence

CAPABILITY = "FALSE_NEGATIVE_AUDIT"
POLICY_VERSION = "false-negative-audit-v1"
OUTPUT_SCHEMA_VERSION = "false-negative-audit-v1"

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "audit_outcome": {
            "type": "string",
            "enum": ["REJECT_CONFIRMED", "FALSE_NEGATIVE_RISK", "NEEDS_MORE_DATA"],
        },
        "reason_text": {"type": "string"},
        "counterevidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "material_unknowns": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["audit_outcome", "reason_text", "counterevidence", "material_unknowns", "confidence"],
}

INSTRUCTIONS = """You are an independent false-negative auditor for an executive opportunity screening system.
You are reviewing roles that another rule or model rejected. Your purpose is to find valuable executive mandates that may have been discarded incorrectly.

Rules:
1. Do not defer to the prior decision. Re-evaluate from the underlying role evidence and candidate truth.
2. Treat title as weak evidence. Look for the actual mandate, authority, economics, scope and transferability.
3. Return FALSE_NEGATIVE_RISK when there is a credible path to a valuable executive mandate and the prior rejection may be too aggressive.
4. Return NEEDS_MORE_DATA when the rejection cannot be safely confirmed because consequential role evidence is missing or ambiguous.
5. Return REJECT_CONFIRMED only when the mismatch is materially supported, such as clearly junior scope, quota-hunter sales, generic PMO without authority, unsupported specialist ownership, or a role that would require exaggerating candidate history.
6. Do not invent reporting lines, compensation, P&L, team size, domain experience or technical ownership.
7. Prefer protecting recall when evidence is genuinely ambiguous, but do not manufacture fit.
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _latest_decision(db: SupabaseREST, opportunity_id: str) -> dict[str, Any] | None:
    rows = db.select("screening_decisions", {
        "opportunity_id": f"eq.{opportunity_id}",
        "select": "id,stage,outcome,reason_code,reason_text,confidence,evidence,policy_version,evaluator_type,model_id,trace_id,created_at",
        "order": "created_at.desc",
        "limit": "1",
    })
    return rows[0] if rows else None


def _already_audited(db: SupabaseREST, opportunity_id: str, decision_id: str | None) -> bool:
    filters: dict[str, str] = {
        "opportunity_id": f"eq.{opportunity_id}",
        "select": "id",
        "limit": "1",
    }
    if decision_id:
        filters["decision_id"] = f"eq.{decision_id}"
    rows = db.select("screening_audit_samples", filters)
    return bool(rows)


def _candidates(db: SupabaseREST, limit: int) -> list[dict[str, Any]]:
    rows = db.select("opportunities", {
        "lifecycle_state": "eq.ACTIVE",
        "screening_stage": "eq.TRIAGE_CLEAR_NO",
        "select": "id,title,location,description_text,posted_at,first_seen_at,last_seen_at,company_id,current_reason_code,current_reason_text,current_confidence,policy_version,metadata",
        "order": "updated_at.desc",
        "limit": "80",
    })
    # Stratify by rejection reason before filling remaining slots. This protects against
    # a single high-volume reason dominating the audit sample.
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        decision = _latest_decision(db, row["id"])
        row["_decision"] = decision
        if _already_audited(db, row["id"], decision.get("id") if decision else None):
            continue
        key = (decision or {}).get("reason_code") or row.get("current_reason_code") or "UNKNOWN"
        groups[key].append(row)

    selected: list[dict[str, Any]] = []
    for key in sorted(groups):
        if groups[key] and len(selected) < limit:
            selected.append(groups[key].pop(0))
    if len(selected) < limit:
        for key in sorted(groups):
            for row in groups[key]:
                if len(selected) >= limit:
                    break
                selected.append(row)
            if len(selected) >= limit:
                break
    return selected


def _persist(
    db: SupabaseREST,
    model_run_id: str,
    opportunity_id: str,
    decision_id: str | None,
    result: dict[str, Any],
    prior: dict[str, Any],
    route: Any,
    usage: dict[str, Any],
) -> None:
    outcome = result["audit_outcome"]
    status = {
        "REJECT_CONFIRMED": "PASSED",
        "FALSE_NEGATIVE_RISK": "FALSE_NEGATIVE",
        "NEEDS_MORE_DATA": "INCONCLUSIVE",
    }[outcome]
    reopen = outcome in {"FALSE_NEGATIVE_RISK", "NEEDS_MORE_DATA"}
    reason_code = "FALSE_NEGATIVE_AUDIT_REOPENED" if outcome == "FALSE_NEGATIVE_RISK" else "FALSE_NEGATIVE_AUDIT_NEEDS_DATA"
    audit_result = {
        **result,
        "prior_decision": prior,
        "audit_policy_version": POLICY_VERSION,
    }
    finished = utcnow()
    response = db.session.post(
        f"{db.base}/rpc/persist_screening_audit_result",
        json={
            "p_opportunity_id": opportunity_id,
            "p_decision_id": decision_id,
            "p_model_run_id": model_run_id,
            "p_sample_reason": "STRATIFIED_FALSE_NEGATIVE_AUDIT",
            "p_audit_status": status,
            "p_audit_result": audit_result,
            "p_notes": "Independent Astra review of a hidden rejection.",
            "p_reopen": reopen,
            "p_reopen_reason_code": reason_code,
            "p_reopen_reason_text": result["reason_text"],
            "p_model_class": route.model_class,
            "p_model_id": route.model_id,
            "p_reasoning_effort": route.reasoning_effort,
            "p_input_tokens": int(usage.get("input_tokens") or 0),
            "p_output_tokens": int(usage.get("output_tokens") or 0),
            "p_estimated_cost_usd": estimated_cost(route.model_id, usage),
            "p_finished_at": finished,
        },
        timeout=60,
    )
    response.raise_for_status()


def audit_one(
    db: SupabaseREST,
    ai: OpenAIResponses,
    role: dict[str, Any],
    candidate: dict[str, Any],
    pursuit_policy: dict[str, Any],
    candidate_version: str,
    pursuit_policy_version: str,
) -> str:
    decision = role.get("_decision")
    description = _ensure_description(db, role)
    company = _company(db, role["company_id"])
    sources = _source_evidence(db, role["id"])
    prior = {
        "decision_id": decision.get("id") if decision else None,
        "stage": decision.get("stage") if decision else role.get("screening_stage"),
        "outcome": decision.get("outcome") if decision else "CLEAR_NO",
        "reason_code": decision.get("reason_code") if decision else role.get("current_reason_code"),
        "reason_text": decision.get("reason_text") if decision else role.get("current_reason_text"),
        "policy_version": decision.get("policy_version") if decision else role.get("policy_version"),
        "evaluator_type": decision.get("evaluator_type") if decision else "DETERMINISTIC",
        "model_id": decision.get("model_id") if decision else None,
    }
    context = {
        "opportunity": {
            "id": role["id"],
            "company": company.get("display_name"),
            "title": role.get("title"),
            "location": role.get("location"),
            "description": description[:18000],
            "source_evidence": sources,
        },
        "prior_rejection": prior,
        "candidate_truth": candidate,
        "candidate_truth_version": candidate_version,
        "pursuit_policy": pursuit_policy,
        "pursuit_policy_version": pursuit_policy_version,
    }
    input_hash = stable_hash(context)
    trace_id = str(uuid.uuid4())
    run = db.insert("model_runs", {
        "capability": CAPABILITY,
        "opportunity_id": role["id"],
        "model_class": "HIGH_CONSEQUENCE_REASONING",
        "model_id": "gpt-6-astra",
        "reasoning_effort": "high",
        "status": "RUNNING",
        "input_hash": input_hash,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "trace_id": trace_id,
        "started_at": utcnow(),
    })[0]
    try:
        result, raw, route = ai.structured(
            CAPABILITY,
            INSTRUCTIONS,
            json.dumps(context, ensure_ascii=False),
            "false_negative_audit",
            SCHEMA,
        )
        _persist(
            db,
            run["id"],
            role["id"],
            decision.get("id") if decision else None,
            result,
            prior,
            route,
            raw.get("usage") or {},
        )
        return result["audit_outcome"]
    except Exception as exc:
        db.patch("model_runs", {"id": f"eq.{run['id']}"}, {
            "status": "FAILED",
            "error_text": f"{type(exc).__name__}: {exc}"[:1500],
            "finished_at": utcnow(),
        })
        raise


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
    ai = OpenAIResponses()
    candidate, pursuit_policy, candidate_version, pursuit_policy_version = _private_context(db)
    limit = max(1, min(int(os.environ.get("AUDIT_LIMIT", "6")), 12))
    roles = _candidates(db, limit)
    results = {"REJECT_CONFIRMED": 0, "FALSE_NEGATIVE_RISK": 0, "NEEDS_MORE_DATA": 0, "FAILED": 0}
    for role in roles:
        try:
            outcome = audit_one(db, ai, role, candidate, pursuit_policy, candidate_version, pursuit_policy_version)
            results[outcome] += 1
        except Exception as exc:
            results["FAILED"] += 1
            db.insert("activity_events", {
                "event_type": "FALSE_NEGATIVE_AUDIT_FAILED",
                "entity_type": "opportunity",
                "entity_id": role["id"],
                "severity": "ATTENTION",
                "message": "Independent rejection audit failed; prior state was not changed.",
                "details": {"error": f"{type(exc).__name__}: {exc}"[:1000]},
            })
    db.insert("activity_events", {
        "event_type": "FALSE_NEGATIVE_AUDIT_BATCH_COMPLETED",
        "severity": "INFO" if results["FAILED"] == 0 else "ATTENTION",
        "message": f"Independent false-negative audit reviewed {len(roles)} hidden rejections.",
        "details": results,
    })
    print(json.dumps({"audited": len(roles), **results}, sort_keys=True))
    return 0 if results["FAILED"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
