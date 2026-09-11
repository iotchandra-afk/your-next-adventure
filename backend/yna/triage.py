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
from .paid_cache import reusable_model_run

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
            "content_hash": record.get("content_hash"),
            "state": record.get("state"),
            "last_seen_at": record.get("last_seen_at"),
            "is_primary": link.get("is_primary", False),
        })
    return evidence


def semantic_input_hash(
    role: dict[str, Any],
    company_name: str | None,
    description: str,
    sources: list[dict[str, Any]],
    candidate_version: str,
    pursuit_policy_version: str,
) -> str:
    """Hash only decision-relevant state, never sync timestamps.

    This prevents an unchanged intake heartbeat from spending model tokens or invalidating
    a durable decision. A content hash, role text, candidate truth version, or pursuit
    policy version change still forces re-evaluation.
    """
    source_fingerprint = sorted(
        [
            {
                "source_family": s.get("source_family"),
                "external_id": s.get("external_id"),
                "canonical_url": s.get("canonical_url"),
                "content_hash": s.get("content_hash"),
            }
            for s in sources
        ],
        key=lambda x: (str(x.get("source_family")), str(x.get("external_id")), str(x.get("canonical_url"))),
    )
    return stable_hash({
        "company": company_name,
        "title": role.get("title"),
        "location": role.get("location"),
        "description": description[:18000],
        "posted_at": role.get("posted_at"),
        "sources": source_fingerprint,
        "candidate_truth_version": candidate_version,
        "pursuit_policy_version": pursuit_policy_version,
        "triage_policy_version": POLICY_VERSION,
    })


def _passed_run(db: SupabaseREST, opportunity_id: str, input_hash: str) -> dict[str, Any] | None:
    return reusable_model_run(
        db,
        capability=CAPABILITY,
        input_hash=input_hash,
        policy_version=POLICY_VERSION,
        output_schema_version=OUTPUT_SCHEMA_VERSION,
        opportunity_id=opportunity_id,
    )


def _reconcile_durable_decision(db: SupabaseREST, role_id: str, run: dict[str, Any]) -> str | None:
    trace_id = run.get("trace_id")
    if not trace_id:
        return None
    decisions = db.select("screening_decisions", {
        "trace_id": f"eq.{trace_id}",
        "stage": "eq.MANDATE_RELEVANCE_TRIAGE",
        "select": "outcome,reason_code,reason_text,confidence,evidence,policy_version",
        "limit": "1",
    })
    if not decisions:
        return None
    decision = decisions[0]
    current = db.select("opportunities", {"id": f"eq.{role_id}", "select": "metadata", "limit": "1"})
    metadata = dict((current[0].get("metadata") if current else {}) or {})
    metadata.update({"triage": decision.get("evidence") or {}, "triage_trace_id": trace_id})
    outcome = decision["outcome"]
    stage = {"RELEVANT": "TRIAGE_RELEVANT", "POSSIBLE": "TRIAGE_POSSIBLE", "CLEAR_NO": "TRIAGE_CLEAR_NO"}[outcome]
    visibility = {"RELEVANT": "SURFACED", "POSSIBLE": "GRAY_ZONE", "CLEAR_NO": "HIDDEN"}[outcome]
    db.patch("opportunities", {"id": f"eq.{role_id}"}, {
        "screening_stage": stage,
        "visibility": visibility,
        "current_reason_code": decision.get("reason_code"),
        "current_reason_text": decision.get("reason_text"),
        "current_confidence": decision.get("confidence"),
        "policy_version": decision.get("policy_version") or POLICY_VERSION,
        "metadata": metadata,
        "updated_at": utcnow(),
    })
    return outcome


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
    input_hash = semantic_input_hash(
        role, company.get("display_name"), description, sources,
        candidate_version, pursuit_policy_version,
    )
    passed = _passed_run(db, role["id"], input_hash)
    if passed and _reconcile_durable_decision(db, role["id"], passed):
        return "SKIPPED_UNCHANGED"

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
            model_run_id=run["id"],
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
