from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .intake import SupabaseREST
from .model_router import (
    OpenAIResponses,
    ROUTES,
    estimated_cost,
    estimated_tool_cost,
    web_search_call_count,
)
from .triage import _company, _ensure_description, _private_context, _source_evidence

POLICY_VERSION = "opportunity-intelligence-v1"
CAPABILITY_VERSIONS = {
    "COMPANY_TRAJECTORY": "company-trajectory-v1",
    "NATIVE_CANDIDATE": "native-candidate-v1",
    "COMMERCIAL_PRESSURE": "commercial-pressure-v1",
    "STAKEHOLDER_CONTEXT": "stakeholder-context-v1",
    "TWO_NOTCH_UP": "two-notch-up-v1",
    "CORE_X": "core-x-v1",
}


def obj(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "properties": properties, "required": required}


def strings(max_items: int = 8) -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}, "maxItems": max_items}


COMPANY_SCHEMA = obj({
    "current_health": {"type": "string"},
    "growth_trajectory": {"type": "string"},
    "margin_trajectory": {"type": "string"},
    "strategic_priorities": strings(),
    "operating_pressures": strings(),
    "technology_pressures": strings(),
    "organizational_pressures": strings(),
    "risk_pressures": strings(),
    "talent_pressures": strings(),
    "biggest_pain_points": strings(),
    "contradictions_or_uncertainties": strings(),
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, [
    "current_health", "growth_trajectory", "margin_trajectory", "strategic_priorities",
    "operating_pressures", "technology_pressures", "organizational_pressures",
    "risk_pressures", "talent_pressures", "biggest_pain_points",
    "contradictions_or_uncertainties", "confidence",
])

NATIVE_SCHEMA = obj({
    "native_candidate_archetype": {"type": "string"},
    "native_class": {"type": "string", "enum": [
        "NATIVE", "NATIVE_ADJACENT", "OUTCOMES_NATIVE", "COMPETING_AGAINST_NATIVE", "NON_NATIVE_STRETCH"
    ]},
    "candidate_advantages": strings(6),
    "native_candidate_advantages": strings(6),
    "fatal_gap": {"type": "boolean"},
    "win_thesis": {"type": "string"},
    "skepticism_to_overcome": strings(6),
    "evidence_answering_skepticism": strings(6),
    "commentary": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, [
    "native_candidate_archetype", "native_class", "candidate_advantages", "native_candidate_advantages",
    "fatal_gap", "win_thesis", "skepticism_to_overcome", "evidence_answering_skepticism",
    "commentary", "confidence",
])

COMMERCIAL_SCHEMA = obj({
    "statement": {"type": "string"},
    "pressure_tree": strings(8),
    "success_6_months": {"type": "string"},
    "success_12_months": {"type": "string"},
    "success_18_months": {"type": "string"},
    "likely_objections_to_candidate": strings(6),
    "what_hm_needs_to_believe": strings(6),
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, [
    "statement", "pressure_tree", "success_6_months", "success_12_months", "success_18_months",
    "likely_objections_to_candidate", "what_hm_needs_to_believe", "confidence",
])

STAKEHOLDER_ITEM = obj({
    "identity": {"type": "string"},
    "title": {"type": "string"},
    "role_in_decision": {"type": "string", "enum": ["DECIDES", "SPONSORS", "INFLUENCES", "VALIDATES", "RECRUITS", "CONNECTS"]},
    "likely_interest": {"type": "string"},
    "likely_objection": {"type": "string"},
    "relationship_to_role": {"type": "string"},
    "verification_status": {"type": "string", "enum": ["VERIFIED", "HIGH_CONFIDENCE", "PROBABLE", "UNKNOWN"]},
    "evidence_urls": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
}, [
    "identity", "title", "role_in_decision", "likely_interest", "likely_objection",
    "relationship_to_role", "verification_status", "evidence_urls",
])
STAKEHOLDER_SCHEMA = obj({
    "exact_hiring_manager": {"type": "string"},
    "hiring_manager_verification": {"type": "string", "enum": ["VERIFIED", "HIGH_CONFIDENCE", "PROBABLE", "UNKNOWN"]},
    "stakeholders": {"type": "array", "items": STAKEHOLDER_ITEM, "maxItems": 12},
    "alternate_hypotheses": strings(6),
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, ["exact_hiring_manager", "hiring_manager_verification", "stakeholders", "alternate_hypotheses", "confidence"])

TWO_NOTCH_SCHEMA = obj({
    "level_0_stated_job": {"type": "string"},
    "level_1_underlying_outcome": {"type": "string"},
    "level_2_game_changer": {"type": "string"},
    "future_business_or_operating_model": {"type": "string"},
    "economic_consequence": {"type": "string"},
    "role_reinterpretation": {"type": "string"},
    "candidate_legitimacy": {"type": "string"},
    "overreach_boundary": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, [
    "level_0_stated_job", "level_1_underlying_outcome", "level_2_game_changer",
    "future_business_or_operating_model", "economic_consequence", "role_reinterpretation",
    "candidate_legitimacy", "overreach_boundary", "confidence",
])

CORE_X_SCHEMA = obj({
    "statement": {"type": "string"},
    "why_now": {"type": "string"},
    "success_definition": {"type": "string"},
    "failure_definition": {"type": "string"},
    "evidence_chain": strings(8),
    "inference_chain": strings(8),
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
}, ["statement", "why_now", "success_definition", "failure_definition", "evidence_chain", "inference_chain", "confidence"])

COMPANY_INSTRUCTIONS = """You are the company-trajectory capability for an executive pursuit system.
Use current web research and prioritize primary sources: earnings, annual/quarterly reports, investor materials,
regulatory filings, official strategy/leadership communications, M&A/restructuring and capital-allocation evidence.
Secondary sources may supplement but not replace primary evidence.
Do not write a generic company profile. Identify economic, operating, technology, organizational, risk and talent
pressures that could shape senior transformation/AI/technology mandates. If a material fact is not established, say UNKNOWN.
Separate observed trajectory from inference. Do not invent financials, priorities or management commitments.
The confidence field is confidence in this evidence-grounded trajectory assessment, not an investment rating.
"""

NATIVE_INSTRUCTIONS = """You are the Native Candidate / winability capability for a senior executive pursuit system.
Ask who the hiring manager could choose if they wanted the most literal candidate from this role's world, then assess
whether the candidate is NATIVE, NATIVE_ADJACENT, OUTCOMES_NATIVE, COMPETING_AGAINST_NATIVE, or NON_NATIVE_STRETCH.
Use only supplied candidate truth. Distinguish direct from transferable evidence. Never manufacture domain, technical,
P&L, quota, product, board, model-risk, FinOps or enterprise-AI-strategy ownership. No numeric fit score.
The commentary must say whether this is a real fit or a manufactured one and what a skeptical native-domain leader would question.
"""

COMMERCIAL_INSTRUCTIONS = """You are the hiring-manager commercial-pressure capability.
Build the causal chain: company economics -> executive priority -> hiring-manager accountability -> operating constraint
-> role mandate -> consequence of success/failure. Do not simply summarize the JD or guess a manager's KPI.
Use UNKNOWN where the evidence cannot establish a time-bound outcome. Identify what this hire should remove from the
leader's plate and what they must believe about the candidate. Avoid manufacturing reporting lines or financial accountability.
"""

STAKEHOLDER_INSTRUCTIONS = """You are the stakeholder-decision-system capability for an executive pursuit.
Use current web research to identify the decision system around the role. Never declare a hiring manager from title proximity alone.
VERIFIED requires direct authoritative evidence tying the person to this role/reporting line. HIGH_CONFIDENCE requires multiple
strong current signals. PROBABLE is a reasoned hypothesis. UNKNOWN is preferable to invented certainty.
Map decision roles as DECIDES, SPONSORS, INFLUENCES, VALIDATES, RECRUITS, or CONNECTS. Preserve alternate hypotheses.
Evidence URLs in the output must be URLs actually found during research. If exact hiring manager is not verified, return UNKNOWN.
"""

TWO_NOTCH_INSTRUCTIONS = """You are the Two-Notch-Up / Aditya Lens capability.
Do not merely restate the problem above the JD. Start with the stated job, identify its underlying outcome, then ask what
technological, customer, competitive, regulatory or economic discontinuity could make today's framing obsolete.
Describe a plausible future business/operating model, its economic consequence, what the hire should build toward now,
and why the candidate can credibly help. State an explicit overreach boundary. The thesis must be grounded in supplied evidence,
not a futuristic essay mechanically attached to the role.
"""

CORE_X_INSTRUCTIONS = """You are the Core of X capability. Produce the unmistakable economically meaningful reason this company
is hiring for this role. The statement must follow this logic: They need X to [change an economically meaningful outcome]
by [specific operating mechanism] while [protecting or overcoming the critical constraint].
Reject generic formulations such as drive innovation, lead strategy, accelerate AI, transform customer experience, modernize
technology, or improve efficiency unless they are made economically and operationally specific. Separate evidence from inference.
Do not lock a confident Core X if company trajectory, role evidence and hiring-manager pressure do not support it.
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _latest(db: SupabaseREST, company_id: str, capability: str, opportunity_id: str | None = None) -> dict[str, Any] | None:
    filters: dict[str, str] = {
        "company_id": f"eq.{company_id}",
        "capability": f"eq.{capability}",
        "status": "eq.COMPLETED",
        "select": "id,payload,evidence,confidence,input_hash,capability_version,policy_version,model_id,reasoning_effort,trace_id,created_at",
        "order": "created_at.desc",
        "limit": "1",
    }
    filters["opportunity_id"] = f"eq.{opportunity_id}" if opportunity_id else "is.null"
    rows = db.select("intelligence_records", filters)
    return rows[0] if rows else None


def _qualification(db: SupabaseREST, opportunity_id: str) -> dict[str, Any] | None:
    rows = db.select("screening_decisions", {
        "opportunity_id": f"eq.{opportunity_id}",
        "stage": "eq.DEEP_QUALIFICATION",
        "select": "id,outcome,reason_code,reason_text,confidence,evidence,policy_version,trace_id,created_at",
        "order": "created_at.desc",
        "limit": "1",
    })
    return rows[0] if rows else None


def _passed_record(db: SupabaseREST, company_id: str, capability: str, input_hash: str, opportunity_id: str | None) -> dict[str, Any] | None:
    filters: dict[str, str] = {
        "company_id": f"eq.{company_id}",
        "capability": f"eq.{capability}",
        "input_hash": f"eq.{input_hash}",
        "status": "eq.COMPLETED",
        "select": "id,payload,evidence,confidence,input_hash,trace_id,created_at",
        "limit": "1",
    }
    filters["opportunity_id"] = f"eq.{opportunity_id}" if opportunity_id else "is.null"
    rows = db.select("intelligence_records", filters)
    return rows[0] if rows else None


def _run_capability(
    db: SupabaseREST,
    ai: OpenAIResponses,
    capability: str,
    company_id: str,
    opportunity_id: str | None,
    context: dict[str, Any],
    instructions: str,
    schema_name: str,
    schema: dict[str, Any],
    use_web: bool,
) -> dict[str, Any]:
    version = CAPABILITY_VERSIONS[capability]
    input_hash = stable_hash({
        "capability": capability,
        "version": version,
        "policy": POLICY_VERSION,
        "context": context,
    })
    existing = _passed_record(db, company_id, capability, input_hash, opportunity_id)
    if existing:
        return existing

    route = ROUTES[capability]
    trace_id = str(uuid.uuid4())
    run = db.insert("model_runs", {
        "capability": capability,
        "opportunity_id": opportunity_id,
        "model_class": route.model_class,
        "model_id": route.model_id,
        "reasoning_effort": route.reasoning_effort,
        "status": "RUNNING",
        "input_hash": input_hash,
        "output_schema_version": version,
        "policy_version": POLICY_VERSION,
        "trace_id": trace_id,
        "started_at": utcnow(),
    })[0]
    try:
        if use_web:
            result, raw, actual_route, sources = ai.structured_with_web(
                capability, instructions, json.dumps(context, ensure_ascii=False), schema_name, schema,
                model_run_id=run["id"],
            )
        else:
            result, raw, actual_route = ai.structured(
                capability, instructions, json.dumps(context, ensure_ascii=False), schema_name, schema,
                model_run_id=run["id"],
            )
            sources = []

        usage = raw.get("usage") or {}
        web_calls = web_search_call_count(raw)
        tool_cost = estimated_tool_cost(raw)
        record = db.insert("intelligence_records", {
            "company_id": company_id,
            "opportunity_id": opportunity_id,
            "capability": capability,
            "capability_version": version,
            "status": "COMPLETED",
            "payload": result,
            "evidence": sources,
            "confidence": result.get("confidence"),
            "input_hash": input_hash,
            "policy_version": POLICY_VERSION,
            "model_class": actual_route.model_class,
            "model_id": actual_route.model_id,
            "reasoning_effort": actual_route.reasoning_effort,
            "trace_id": trace_id,
        })[0]
        db.patch("model_runs", {"id": f"eq.{run['id']}"}, {
            "status": "PASSED",
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "estimated_cost_usd": estimated_cost(actual_route.model_id, usage),
            "tool_calls": sources,
            "web_search_calls": web_calls,
            "tool_cost_usd": tool_cost,
            "finished_at": utcnow(),
        })
        return record
    except Exception as exc:
        db.patch("model_runs", {"id": f"eq.{run['id']}"}, {
            "status": "FAILED",
            "error_text": f"{type(exc).__name__}: {exc}"[:1500],
            "finished_at": utcnow(),
        })
        raise


def _company_context(company: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": company.get("display_name"),
        "domain": company.get("domain"),
        "website_url": company.get("website_url"),
        "industry": company.get("industry"),
        "research_requirement": "Current as of execution time; prioritize primary company/investor/regulatory sources.",
    }


def company_trajectory(db: SupabaseREST, ai: OpenAIResponses, company: dict[str, Any]) -> dict[str, Any]:
    return _run_capability(
        db, ai, "COMPANY_TRAJECTORY", company["id"], None, _company_context(company),
        COMPANY_INSTRUCTIONS, "company_trajectory", COMPANY_SCHEMA, True,
    )


def native_candidate(
    db: SupabaseREST, ai: OpenAIResponses, role: dict[str, Any], company: dict[str, Any], description: str,
    candidate: dict[str, Any], candidate_version: str, qualification: dict[str, Any] | None, trajectory: dict[str, Any],
) -> dict[str, Any]:
    context = {
        "opportunity": {"company": company.get("display_name"), "title": role.get("title"), "location": role.get("location"), "description": description[:18000]},
        "company_trajectory": trajectory.get("payload"),
        "qualification": qualification,
        "candidate_truth": candidate,
        "candidate_truth_version": candidate_version,
    }
    return _run_capability(
        db, ai, "NATIVE_CANDIDATE", company["id"], role["id"], context,
        NATIVE_INSTRUCTIONS, "native_candidate", NATIVE_SCHEMA, False,
    )


def commercial_pressure(
    db: SupabaseREST, ai: OpenAIResponses, role: dict[str, Any], company: dict[str, Any], description: str,
    qualification: dict[str, Any] | None, trajectory: dict[str, Any], native: dict[str, Any],
) -> dict[str, Any]:
    context = {
        "opportunity": {"company": company.get("display_name"), "title": role.get("title"), "location": role.get("location"), "description": description[:18000]},
        "company_trajectory": trajectory.get("payload"),
        "qualification": qualification,
        "native_candidate": native.get("payload"),
    }
    return _run_capability(
        db, ai, "COMMERCIAL_PRESSURE", company["id"], role["id"], context,
        COMMERCIAL_INSTRUCTIONS, "commercial_pressure", COMMERCIAL_SCHEMA, False,
    )


def stakeholder_context(
    db: SupabaseREST, ai: OpenAIResponses, role: dict[str, Any], company: dict[str, Any], description: str,
    trajectory: dict[str, Any], pressure: dict[str, Any], source_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    context = {
        "opportunity": {"company": company.get("display_name"), "title": role.get("title"), "location": role.get("location"), "description": description[:14000]},
        "official_job_sources": source_evidence,
        "company_trajectory": trajectory.get("payload"),
        "commercial_pressure": pressure.get("payload"),
        "research_requirement": "Current decision-system evidence. Do not infer a reporting line from title proximity.",
    }
    return _run_capability(
        db, ai, "STAKEHOLDER_CONTEXT", company["id"], role["id"], context,
        STAKEHOLDER_INSTRUCTIONS, "stakeholder_context", STAKEHOLDER_SCHEMA, True,
    )


def two_notch_up(
    db: SupabaseREST, ai: OpenAIResponses, role: dict[str, Any], company: dict[str, Any], description: str,
    candidate: dict[str, Any], qualification: dict[str, Any] | None, trajectory: dict[str, Any],
    native: dict[str, Any], pressure: dict[str, Any],
) -> dict[str, Any]:
    context = {
        "opportunity": {"company": company.get("display_name"), "title": role.get("title"), "description": description[:16000]},
        "company_trajectory": trajectory.get("payload"),
        "commercial_pressure": pressure.get("payload"),
        "native_candidate": native.get("payload"),
        "qualification": qualification,
        "candidate_truth": candidate,
    }
    return _run_capability(
        db, ai, "TWO_NOTCH_UP", company["id"], role["id"], context,
        TWO_NOTCH_INSTRUCTIONS, "two_notch_up", TWO_NOTCH_SCHEMA, False,
    )


def core_x(
    db: SupabaseREST, ai: OpenAIResponses, role: dict[str, Any], company: dict[str, Any], description: str,
    qualification: dict[str, Any] | None, trajectory: dict[str, Any], native: dict[str, Any], pressure: dict[str, Any],
    stakeholders: dict[str, Any], two_notch: dict[str, Any], source_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    context = {
        "opportunity": {"company": company.get("display_name"), "title": role.get("title"), "location": role.get("location"), "description": description[:18000]},
        "official_job_sources": source_evidence,
        "qualification": qualification,
        "company_trajectory": trajectory.get("payload"),
        "native_candidate": native.get("payload"),
        "commercial_pressure": pressure.get("payload"),
        "stakeholder_context": stakeholders.get("payload"),
        "two_notch_up": two_notch.get("payload"),
    }
    return _run_capability(
        db, ai, "CORE_X", company["id"], role["id"], context,
        CORE_X_INSTRUCTIONS, "core_x", CORE_X_SCHEMA, False,
    )


def _targets(db: SupabaseREST, limit: int) -> list[dict[str, Any]]:
    candidates = db.select("opportunities", {
        "lifecycle_state": "eq.ACTIVE",
        "visibility": "eq.SURFACED",
        "screening_stage": "eq.PRIORITIZED",
        "select": "id,title,location,description_text,posted_at,company_id,screening_stage,visibility,priority_class,metadata,updated_at",
        "order": "updated_at.desc",
        "limit": str(limit * 4),
    })
    return [role for role in candidates if deep_intelligence_allowed(role)][:limit]


def deep_intelligence_allowed(role: dict[str, Any]) -> bool:
    metadata = role.get("metadata") or {}
    active_pursuit = metadata.get("pursuit_status") == "ACTIVE"
    qualified = (
        role.get("screening_stage") == "PRIORITIZED"
        and role.get("visibility") == "SURFACED"
        and role.get("priority_class") in {"TIER_1", "TIER_2"}
    )
    return bool(active_pursuit or qualified)


def build_bundle(
    db: SupabaseREST,
    ai: OpenAIResponses,
    role: dict[str, Any],
    candidate: dict[str, Any],
    candidate_version: str,
) -> dict[str, Any]:
    if not deep_intelligence_allowed(role):
        raise RuntimeError("Deep intelligence requires a surfaced Tier 1/Tier 2 opportunity or explicit active pursuit.")
    company = _company(db, role["company_id"])
    description = _ensure_description(db, role)
    sources = _source_evidence(db, role["id"])
    qualification = _qualification(db, role["id"])
    trajectory = company_trajectory(db, ai, company)
    native = native_candidate(db, ai, role, company, description, candidate, candidate_version, qualification, trajectory)
    pressure = commercial_pressure(db, ai, role, company, description, qualification, trajectory, native)
    stakeholders = stakeholder_context(db, ai, role, company, description, trajectory, pressure, sources)
    two_notch = two_notch_up(db, ai, role, company, description, candidate, qualification, trajectory, native, pressure)
    core = core_x(db, ai, role, company, description, qualification, trajectory, native, pressure, stakeholders, two_notch, sources)
    return {
        "opportunity_id": role["id"],
        "company": company.get("display_name"),
        "title": role.get("title"),
        "company_trajectory": trajectory["id"],
        "native_candidate": native["id"],
        "commercial_pressure": pressure["id"],
        "stakeholder_context": stakeholders["id"],
        "two_notch_up": two_notch["id"],
        "core_x": core["id"],
    }


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required")
    db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
    ai = OpenAIResponses()
    candidate, _, candidate_version, _ = _private_context(db)
    limit = max(1, min(int(os.environ.get("INTELLIGENCE_LIMIT", "3")), 3))
    targets = _targets(db, limit)
    completed: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for role in targets:
        try:
            completed.append(build_bundle(db, ai, role, candidate, candidate_version))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:1200]
            failures.append({"opportunity_id": role["id"], "error": error})
            db.insert("activity_events", {
                "event_type": "OPPORTUNITY_INTELLIGENCE_FAILED",
                "entity_type": "opportunity",
                "entity_id": role["id"],
                "severity": "ATTENTION",
                "message": "Opportunity intelligence failed; prior screening and qualification remain intact.",
                "details": {"error": error},
            })
    db.insert("activity_events", {
        "event_type": "OPPORTUNITY_INTELLIGENCE_BATCH_COMPLETED",
        "severity": "INFO" if not failures else "ATTENTION",
        "message": f"Opportunity intelligence built for {len(completed)} of {len(targets)} selected pursuits.",
        "details": {"completed": completed, "failures": failures},
    })
    print(json.dumps({"targets": len(targets), "completed": completed, "failures": failures}, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(run())
