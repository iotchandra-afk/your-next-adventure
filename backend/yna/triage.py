from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .intake import SupabaseREST
from .job_detail import fetch_job_detail
from .model_router import OpenAIResponses, estimated_cost

CAPABILITY = "RELEVANCE_TRIAGE"
OUTPUT_SCHEMA_VERSION = "relevance-triage-v1"
POLICY_VERSION = "relevance-triage-v1"

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "outcome": {"type": "string", "enum": ["RELEVANT", "POSSIBLE", "CLEAR_NO"]},
        "mandate_summary": {"type": "string"},
        "supporting_factors": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "constraints": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "material_unknowns": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "authority_signals": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "candidate_path": {"type": "string", "enum": ["DIRECT", "ADJACENT", "OUTCOMES_NATIVE", "UNCLEAR", "UNSUPPORTED"]},
        "reason_code": {"type": "string"},
        "reason_text": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "outcome", "mandate_summary", "supporting_factors", "constraints", "material_unknowns",
        "authority_signals", "candidate_path", "reason_code", "reason_text", "confidence"
    ],
}

INSTRUCTIONS = """You are the mandate-aware relevance triage capability for an executive opportunity system.
Your task is not to maximize applications and not to reward impressive titles. Determine whether the actual mandate merits further attention for this candidate.

Rules:
1. Treat title as a signal, never as the decision.
2. Prefer recall when evidence is incomplete. If a potentially valuable executive mandate cannot be safely ruled in or out, return POSSIBLE.
3. Return CLEAR_NO only when evidence supports a material mismatch such as clearly junior scope, quota-hunter sales, generic PMO without authority, unsupported deep specialist ownership, low-scope delivery, or a role that would require exaggerating candidate history.
4. Return RELEVANT when there is a credible path to meaningful enterprise/BU impact, operating leverage, AI/technology-to-value, operating-model change, platform/engineering transformation tied to business economics, customer/service transformation, strategic portfolio/value orchestration, or similarly substantial mandate.
5. Do not invent compensation, reporting line, authority, P&L, team size, technical depth, or candidate experience. Missing consequential facts belong in material_unknowns.
6. Judge transferable mandate and operating environment, not keyword overlap.
7. Keep reasons concise and evidence-grounded. No numeric fit score.
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _private_context(db: SupabaseREST) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    candidate = db.select("candidate_truth", {"id": "eq.1", "select": "version,profile", "limit": "1"})
    policy = db.select("pursuit_policy", {"id": "eq.1", "select": "version,policy", "limit": "1"})
    if not candidate or not policy:
        raise RuntimeError("Private candidate truth and pursuit policy must exist before triage")
    return candidate[0]["profile"], policy[0]["policy"], candidate[0]["version"], policy[0]["version"]


def _eligible_roles(db: SupabaseREST, limit: int) -> list[dict[str, Any]]:
    return db.select("opportunities", {
        "lifecycle_state": "eq.ACTIVE",
        "screening_stage": "eq.ELIGIBLE",
        "current_reason_code": "eq.EXECUTIVE_SCOPE_PLAUSIBLE",
        "select": "id,title,location,description_text,posted_at,first_seen_at,last_seen_at,company_id,metadata",
        "order": "first_seen_at.desc",
        "limit": str(limit),
    })


def _company(db: SupabaseREST, company_id: str) -> dict[str, Any]:
    rows = db.select("companies", {"id": f"eq.{company_id}", "select": "id,display_name,normalized_name,metadata", "limit": "1"})
    return rows[0] if rows else {"id": company_id, "display_name": "Unknown company"}


def _source_links(db: SupabaseREST, opportunity_id: str) -> list[dict[str, Any]]:
    return db.select("opportunity_sources", {
        "opportunity_id": f"eq.{opportunity_id}",
        "select": "source_record_id,is_primary",
    })


def _source_record(db: SupabaseREST, source_record_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    records = db.select("source_records", {
        "id": f"eq.{source_record_id}",
        "select": "id,external_id,canonical_url,state,content_hash,source_id,last_seen_at,raw_payload",
        "limit": "1",
    })
    if not records:
        return None
    record = records[0]
    sources = db.select("source_registry", {
        "id": f"eq.{record['source_id']}",
        "select": "source_family,display_name,source_key,metadata",
        "limit": "1",
    })
    return record, (sources[0] if sources else {})


def _ensure_description(db: SupabaseREST, role: dict[str, Any]) -> str:
    existing = role.get("description_text") or ""
    if existing.strip():
        return existing
    links = _source_links(db, role["id"])
    links = sorted(links, key=lambda item: bool(item.get("is_primary")), reverse=True)
    for link in links[:3]:
        pair = _source_record(db, link["source_record_id"])
        if not pair:
            continue
        record, source = pair
        try:
            detail = fetch_job_detail(
                source.get("source_family") or "",
                source.get("metadata") or {},
                record.get("external_id") or "",
                record.get("raw_payload") or {},
            )
        except Exception:
            detail = ""
        if detail.strip():
            db.patch("opportunities", {"id": f"eq.{role['id']}"}, {
                "description_text": detail,
                "updated_at": utcnow(),
            })
            role["description_text"] = detail
            return detail
    return ""


def _source_evidence(db: SupabaseREST, opportunity_id: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for link in _source_links(db, opportunity_id)[:4]:
        pair = _source_record(db, link["source_record_id"])
        if not pair:
            continue
        record, source = pair
        evidence.append({
            "source_family": source.get("source_family"),
            "source_name": source.get("display_name"),
            "external_id": record.get("external_id"),
            "canonical_url": record.get("canonical_url"),
            "state": record.get("state"),
            "last_seen_at": record.get("last_seen_at"),
            "is_primary": link.get("is_primary", False),
        })
    return evidence


def _already_triaged(db: SupabaseREST, opportunity_id: str, input_hash: str) -> bool:
    rows = db.select("model_runs", {
        "opportunity_id": f"eq.{opportunity_id}",
        "capability": f"eq.{CAPABILITY}",
        "input_hash": f"eq.{input_hash}",
        "status": "eq.PASSED",
        "select": "id",
        "limit": "1",
    })
    return bool(rows)


def _persist_result(
    db: SupabaseREST,
    run_id: str,
    role_id: str,
    result: dict[str, Any],
    evidence: dict[str, Any],
    route: Any,
    usage: dict[str, Any],
    trace_id: str,
) -> None:
    finished = utcnow()
    response = db.session.post(
        f"{db.base}/rpc/persist_relevance_triage_result",
        json={
            "p_opportunity_id": role_id,
            "p_model_run_id": run_id,
            "p_outcome": result["outcome"],
            "p_reason_code": result["reason_code"],
            "p_reason_text": result["reason_text"],
            "p_confidence": result["confidence"],
            "p_evidence": evidence,
            "p_policy_version": POLICY_VERSION,
            "p_model_class": route.model_class,
            "p_model_id": route.model_id,
            "p_reasoning_effort": route.reasoning_effort,
            "p_trace_id": trace_id,
            "p_input_tokens": int(usage.get("input_tokens") or 0),
            "p_output_tokens": int(usage.get("output_tokens") or 0),
            "p_estimated_cost_usd": estimated_cost(route.model_id, usage),
            "p_finished_at": finished,
        },
        timeout=60,
    )
    response.raise_for_status()


def triage_one(
    db: SupabaseREST,
    ai: OpenAIResponses,
    role: dict[str, Any],
    candidate: dict[str, Any],
    pursuit_policy: dict[str, Any],
    candidate_version: str,
    pursuit_policy_version: str,
) -> str:
    company = _company(db, role["company_id"])
    description = _ensure_description(db, role)
    sources = _source_evidence(db, role["id"])
    context = {
        "opportunity": {
            "id": role["id"],
            "company": company.get("display_name"),
            "title": role.get("title"),
            "location": role.get("location"),
            "description": description[:18000],
            "posted_at": role.get("posted_at"),
            "first_seen_at": role.get("first_seen_at"),
            "last_seen_at": role.get("last_seen_at"),
            "source_evidence": sources,
        },
        "candidate_truth": candidate,
        "candidate_truth_version": candidate_version,
        "pursuit_policy": pursuit_policy,
        "pursuit_policy_version": pursuit_policy_version,
    }
    input_hash = stable_hash(context)
    if _already_triaged(db, role["id"], input_hash):
        return "SKIPPED_UNCHANGED"

    trace_id = str(uuid.uuid4())
    run = db.insert("model_runs", {
        "capability": CAPABILITY,
        "opportunity_id": role["id"],
        "model_class": "STANDARD_REASONING",
        "model_id": "gpt-5.6-sol",
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
            "relevance_triage",
            SCHEMA,
        )
        evidence = {
            "mandate_summary": result["mandate_summary"],
            "supporting_factors": result["supporting_factors"],
            "constraints": result["constraints"],
            "material_unknowns": result["material_unknowns"],
            "authority_signals": result["authority_signals"],
            "candidate_path": result["candidate_path"],
            "sources": sources,
            "candidate_truth_version": candidate_version,
            "pursuit_policy_version": pursuit_policy_version,
            "description_available": bool(description.strip()),
        }
        _persist_result(db, run["id"], role["id"], result, evidence, route, raw.get("usage") or {}, trace_id)
        return result["outcome"]
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
    limit = max(1, min(int(os.environ.get("TRIAGE_LIMIT", "12")), 50))
    roles = _eligible_roles(db, limit)
    results = {"RELEVANT": 0, "POSSIBLE": 0, "CLEAR_NO": 0, "SKIPPED_UNCHANGED": 0, "FAILED": 0}
    for role in roles:
        try:
            outcome = triage_one(db, ai, role, candidate, pursuit_policy, candidate_version, pursuit_policy_version)
            results[outcome] += 1
        except Exception as exc:
            results["FAILED"] += 1
            db.insert("activity_events", {
                "event_type": "RELEVANCE_TRIAGE_FAILED",
                "entity_type": "opportunity",
                "entity_id": role["id"],
                "severity": "ATTENTION",
                "message": "Mandate relevance triage failed; opportunity remains retained and unsurfaced.",
                "details": {"error": f"{type(exc).__name__}: {exc}"[:1000]},
            })
    db.insert("activity_events", {
        "event_type": "RELEVANCE_TRIAGE_BATCH_COMPLETED",
        "severity": "INFO" if results["FAILED"] == 0 else "ATTENTION",
        "message": f"Mandate relevance triage evaluated {len(roles)} retained executive opportunities.",
        "details": results,
    })
    print(json.dumps(results, sort_keys=True))
    return 0 if results["FAILED"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
