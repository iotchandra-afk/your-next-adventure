from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .intake import SupabaseREST
from .model_router import OpenAIResponses, estimated_cost
from .triage import _company, _ensure_description, _private_context, _source_evidence

CAPABILITY = "DEEP_QUALIFICATION"
POLICY_VERSION = "deep-qualification-v1"
OUTPUT_SCHEMA_VERSION = "deep-qualification-v1"

SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision_class": {
            "type": "string",
            "enum": [
                "TIER_1_DEEP_QUALIFY",
                "TIER_2_WORTH_EXPLORING",
                "TIER_3_MONITOR",
                "NEEDS_DATA",
                "REJECT",
            ],
        },
        "native_class": {
            "type": "string",
            "enum": [
                "NATIVE",
                "NATIVE_ADJACENT",
                "OUTCOMES_NATIVE",
                "COMPETING_AGAINST_NATIVE",
                "NON_NATIVE_STRETCH",
            ],
        },
        "why_role_exists": {"type": "string"},
        "why_now": {"type": "string"},
        "economic_outcome": {"type": "string"},
        "mechanism": {"type": "string"},
        "critical_constraint": {"type": "string"},
        "authority_assessment": {"type": "string"},
        "supporting_factors": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "constraints": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "material_unknowns": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "reason_code": {"type": "string"},
        "reason_text": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "decision_class", "native_class", "why_role_exists", "why_now", "economic_outcome",
        "mechanism", "critical_constraint", "authority_assessment", "supporting_factors",
        "constraints", "material_unknowns", "reason_code", "reason_text", "confidence"
    ],
}

INSTRUCTIONS = """You are the deep-qualification and prioritization capability for a senior executive opportunity system.
The role has already survived broad relevance screening. Decide how much scarce executive attention it deserves.

Decision classes:
- TIER_1_DEEP_QUALIFY: unusually strong mandate, credible candidate path, meaningful authority/economics, and worth immediate deep pursuit.
- TIER_2_WORTH_EXPLORING: credible and valuable, but material constraints or unknowns keep it below Tier 1.
- TIER_3_MONITOR: relevant enough to retain, but current mandate/economics/trajectory do not justify active pursuit.
- NEEDS_DATA: potentially high-value, but consequential missing evidence prevents responsible prioritization.
- REJECT: deeper evidence reveals a material mismatch that broad triage did not establish.

Native-candidate classes are qualitative, never pseudo-precise fit scores:
NATIVE, NATIVE_ADJACENT, OUTCOMES_NATIVE, COMPETING_AGAINST_NATIVE, NON_NATIVE_STRETCH.

Rules:
1. Judge the actual business mandate, not title prestige or keyword overlap.
2. Identify why the role exists, why now, the economically meaningful outcome, the mechanism, and the critical constraint. If the evidence does not support one, state it as unknown rather than inventing it.
3. Weight authority, decision rights, business access, team/budget ownership, enterprise/BU scope, measurable value and career economics.
4. Distinguish direct proof from transferable/outcomes-native proof. Do not inflate the candidate's technical, domain, P&L, board, product or AI-strategy ownership.
5. A large company or impressive title alone is not Tier 1. A less obvious title can be Tier 1 if the mandate is economically consequential.
6. Missing compensation is not an early rejection. Unsupported specialist requirements, low authority, quota-hunter sales, generic PMO and innovation theater are material negatives.
7. Prefer NEEDS_DATA over forced certainty when a consequential fact could change the tier.
8. No numeric fit score. The confidence field reflects confidence in the classification, not candidate fit.
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _triage_decision(db: SupabaseREST, opportunity_id: str) -> dict[str, Any] | None:
    rows = db.select("screening_decisions", {
        "opportunity_id": f"eq.{opportunity_id}",
        "stage": "eq.MANDATE_RELEVANCE_TRIAGE",
        "outcome": "eq.RELEVANT",
        "select": "id,outcome,reason_code,reason_text,confidence,evidence,policy_version,trace_id",
        "order": "created_at.desc",
        "limit": "1",
    })
    return rows[0] if rows else None


def _candidates(db: SupabaseREST, limit: int) -> list[dict[str, Any]]:
    return db.select("opportunities", {
        "lifecycle_state": "eq.ACTIVE",
        "screening_stage": "eq.TRIAGE_RELEVANT",
        "visibility": "eq.SURFACED",
        "select": "id,title,location,description_text,posted_at,company_id,metadata",
        "order": "updated_at.asc",
        "limit": str(limit),
    })


def semantic_input_hash(
    role: dict[str, Any],
    company_name: str | None,
    description: str,
    sources: list[dict[str, Any]],
    triage_decision: dict[str, Any] | None,
    candidate_version: str,
    pursuit_policy_version: str,
) -> str:
    source_fingerprint = sorted([
        {
            "source_family": s.get("source_family"),
            "external_id": s.get("external_id"),
            "canonical_url": s.get("canonical_url"),
            "content_hash": s.get("content_hash"),
        }
        for s in sources
    ], key=lambda x: (str(x.get("source_family")), str(x.get("external_id"))))
    triage_fingerprint = {
        "outcome": (triage_decision or {}).get("outcome"),
        "reason_code": (triage_decision or {}).get("reason_code"),
        "policy_version": (triage_decision or {}).get("policy_version"),
        "evidence": (triage_decision or {}).get("evidence"),
    }
    return stable_hash({
        "company": company_name,
        "title": role.get("title"),
        "location": role.get("location"),
        "description": description[:18000],
        "posted_at": role.get("posted_at"),
        "sources": source_fingerprint,
        "triage": triage_fingerprint,
        "candidate_truth_version": candidate_version,
        "pursuit_policy_version": pursuit_policy_version,
        "qualification_policy_version": POLICY_VERSION,
    })


def _passed_run(db: SupabaseREST, opportunity_id: str, input_hash: str) -> bool:
    rows = db.select("model_runs", {
        "opportunity_id": f"eq.{opportunity_id}",
        "capability": f"eq.{CAPABILITY}",
        "input_hash": f"eq.{input_hash}",
        "status": "eq.PASSED",
        "select": "id",
        "limit": "1",
    })
    return bool(rows)


def _persist(
    db: SupabaseREST,
    role_id: str,
    run_id: str,
    result: dict[str, Any],
    evidence: dict[str, Any],
    route: Any,
    usage: dict[str, Any],
    trace_id: str,
) -> None:
    response = db.session.post(
        f"{db.base}/rpc/persist_deep_qualification_result",
        json={
            "p_opportunity_id": role_id,
            "p_model_run_id": run_id,
            "p_decision_class": result["decision_class"],
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
            "p_finished_at": utcnow(),
        },
        timeout=60,
    )
    response.raise_for_status()


def qualify_one(
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
    triage = _triage_decision(db, role["id"])
    input_hash = semantic_input_hash(
        role, company.get("display_name"), description, sources, triage,
        candidate_version, pursuit_policy_version,
    )
    if _passed_run(db, role["id"], input_hash):
        return "SKIPPED_UNCHANGED"

    context = {
        "opportunity": {
            "id": role["id"],
            "company": company.get("display_name"),
            "title": role.get("title"),
            "location": role.get("location"),
            "description": description[:18000],
            "source_evidence": sources,
            "relevance_triage": triage,
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
            "deep_qualification",
            SCHEMA,
        )
        evidence = {
            "native_class": result["native_class"],
            "why_role_exists": result["why_role_exists"],
            "why_now": result["why_now"],
            "economic_outcome": result["economic_outcome"],
            "mechanism": result["mechanism"],
            "critical_constraint": result["critical_constraint"],
            "authority_assessment": result["authority_assessment"],
            "supporting_factors": result["supporting_factors"],
            "constraints": result["constraints"],
            "material_unknowns": result["material_unknowns"],
            "sources": sources,
            "triage_decision_id": triage.get("id") if triage else None,
            "candidate_truth_version": candidate_version,
            "pursuit_policy_version": pursuit_policy_version,
        }
        _persist(db, role["id"], run["id"], result, evidence, route, raw.get("usage") or {}, trace_id)
        return result["decision_class"]
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
    limit = max(1, min(int(os.environ.get("QUALIFY_LIMIT", "6")), 12))
    roles = _candidates(db, limit)
    results = {
        "TIER_1_DEEP_QUALIFY": 0,
        "TIER_2_WORTH_EXPLORING": 0,
        "TIER_3_MONITOR": 0,
        "NEEDS_DATA": 0,
        "REJECT": 0,
        "SKIPPED_UNCHANGED": 0,
        "FAILED": 0,
    }
    for role in roles:
        try:
            results[qualify_one(db, ai, role, candidate, pursuit_policy, candidate_version, pursuit_policy_version)] += 1
        except Exception as exc:
            results["FAILED"] += 1
            db.insert("activity_events", {
                "event_type": "DEEP_QUALIFICATION_FAILED",
                "entity_type": "opportunity",
                "entity_id": role["id"],
                "severity": "ATTENTION",
                "message": "Deep qualification failed; the prior relevance decision remains intact.",
                "details": {"error": f"{type(exc).__name__}: {exc}"[:1000]},
            })
    db.insert("activity_events", {
        "event_type": "DEEP_QUALIFICATION_BATCH_COMPLETED",
        "severity": "INFO" if results["FAILED"] == 0 else "ATTENTION",
        "message": f"Deep qualification evaluated {len(roles)} relevant opportunities.",
        "details": results,
    })
    print(json.dumps({"qualified": len(roles), **results}, sort_keys=True))
    return 0 if results["FAILED"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
