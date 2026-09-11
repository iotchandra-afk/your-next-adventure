from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib.parse import urlsplit

from .intake import SupabaseREST, canonical_key, content_hash, normalize_text, utcnow
from .model_router import OpenAIResponses, estimated_total_cost, web_search_call_count
from .paid_cache import reusable_model_run
from .screening import POLICY_VERSION, deterministic_screen

SOURCE_KEY = "market:web-search"
SOURCE_FAMILY = "DISCOVERY_SIGNAL"
DISCOVERY_POLICY = "market-discovery-v1"
MAX_SIGNALS = 16
MAX_PROBES = 8

ROLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["roles"],
    "properties": {
        "roles": {
            "type": "array",
            "maxItems": MAX_SIGNALS,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["company", "title", "location", "discovery_url", "official_url", "requisition_id", "posted_at", "source_family", "source_name", "snippet", "confidence"],
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "location": {"type": ["string", "null"]},
                    "discovery_url": {"type": "string"},
                    "official_url": {"type": ["string", "null"]},
                    "requisition_id": {"type": ["string", "null"]},
                    "posted_at": {"type": ["string", "null"]},
                    "source_family": {"type": "string"},
                    "source_name": {"type": "string"},
                    "snippet": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        }
    },
}


def valid_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value.strip())
        return value.strip() if parts.scheme in {"http", "https"} and parts.netloc else None
    except ValueError:
        return None


def role_key(role: dict[str, Any]) -> str:
    raw = "|".join((normalize_text(role.get("company")), normalize_text(role.get("title")), valid_url(role.get("discovery_url")) or ""))
    return hashlib.sha256(raw.encode()).hexdigest()


def clean_roles(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items[:limit]:
        discovery_url = valid_url(item.get("discovery_url"))
        company = str(item.get("company") or "").strip()
        title = str(item.get("title") or "").strip()
        if not company or not title or not discovery_url:
            continue
        role = {**item, "company": company, "title": title, "discovery_url": discovery_url, "official_url": valid_url(item.get("official_url"))}
        key = role_key(role)
        if key not in seen:
            seen.add(key)
            result.append(role)
    return result


def run_grounded_scan(client: OpenAIResponses, policy: dict[str, Any], *, probe: bool) -> tuple[list[dict[str, Any]], dict[str, Any], Any]:
    mode = "independent recall probe" if probe else "broad market discovery"
    instructions = (
        f"Run a current {mode} for US executive transformation mandates. Search broadly across companies, industries, job boards, recruiter signals, and official career sites; do not rely on any supplied employer list. "
        "Prefer active official postings, but retain a credible discovery URL when the official URL cannot be resolved. Never invent a role, URL, requisition, date, or source. Exclude obvious sales quota, recruiting, and assistant roles. Return concise structured facts only."
    )
    input_text = json.dumps({
        "objective": "Find Director+/VP/Head/MD/C-suite-adjacent mandates involving enterprise AI, operating transformation, platform modernization, technology-to-value, service/customer transformation, portfolio value, or risk/control outcomes.",
        "pursuit_policy": policy,
        "independence": "This pass has no access to the configured static employer registry or the other scan's results.",
        "freshness": "Prefer postings credibly active or found in the last 45 days; uncertainty must lower confidence.",
        "target_count": MAX_PROBES if probe else MAX_SIGNALS,
    }, sort_keys=True)
    parsed, body, route, _sources = client.structured_with_web("MARKET_DISCOVERY", instructions, input_text, "market_roles", ROLE_SCHEMA, max_tool_calls=5)
    return clean_roles(parsed.get("roles") or [], MAX_PROBES if probe else MAX_SIGNALS), body, route


def prepare_records(roles: list[dict[str, Any]], seen_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for role in roles:
        stage, visibility, reason_code, confidence = deterministic_screen(role["title"])
        reason_text = "High-confidence deterministic title exclusion; retained in the auditable hidden universe." if stage == "TRIAGE_CLEAR_NO" else "Discovery signal retained below the glass for mandate-aware relevance triage."
        common = {
            "company": role["company"],
            "normalized_company": normalize_text(role["company"]),
            "title": role["title"],
            "normalized_title": normalize_text(role["title"]),
            "location": role.get("location") or "",
            "description": role.get("snippet") or "",
            "posted_at": role.get("posted_at") or "",
            "canonical_key": canonical_key(role["company"], role["title"], role.get("location")),
            "screening_stage": stage,
            "visibility": visibility,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "confidence": confidence,
            "policy_version": POLICY_VERSION,
            "updated_at": seen_at,
            "opportunity_metadata": {"discovery_policy": DISCOVERY_POLICY, "requisition_id": role.get("requisition_id")},
        }
        urls = [("discovery", role["discovery_url"], False)]
        if role.get("official_url") and role["official_url"] != role["discovery_url"]:
            urls.append(("official", role["official_url"], True))
        elif role.get("official_url"):
            urls[0] = ("official", role["official_url"], True)
        for kind, url, primary in urls:
            raw = {**role, "url_kind": kind, "provenance": {"channel": "grounded_web_search", "policy": DISCOVERY_POLICY}}
            records.append({
                **common,
                "external_id": hashlib.sha256(f"{kind}|{url}".encode()).hexdigest(),
                "url": url,
                "raw_payload": raw,
                "content_hash": content_hash(raw),
                "is_primary": primary,
            })
    return records


def discovery_input_hash(pass_name: str, policy_version: str, day_bucket: str) -> str:
    return content_hash({"pass": pass_name, "policy": DISCOVERY_POLICY, "pursuit_policy": policy_version, "freshness_day": day_bucket})


def discovery_pass_reusable(db: SupabaseREST, input_hash: str) -> bool:
    return reusable_model_run(
        db,
        capability="MARKET_DISCOVERY",
        input_hash=input_hash,
        policy_version=DISCOVERY_POLICY,
        output_schema_version="market-roles-v1",
        opportunity_id=None,
    ) is not None


def upsert_model_run(db: SupabaseREST, body: dict[str, Any], route: Any, pass_name: str, input_hash: str) -> None:
    usage = body.get("usage") or {}
    db.insert("model_runs", {
        "capability": "MARKET_DISCOVERY", "model_class": route.model_class, "model_id": route.model_id,
        "reasoning_effort": route.reasoning_effort, "status": "PASSED",
        "input_hash": input_hash,
        "output_schema_version": "market-roles-v1", "policy_version": DISCOVERY_POLICY,
        "trace_id": body.get("id"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "estimated_cost_usd": estimated_total_cost(route.model_id, body), "finished_at": utcnow(),
        "web_search_calls": web_search_call_count(body), "tool_cost_usd": round(web_search_call_count(body) * 0.01, 6),
        "tool_calls": [{"type": "web_search", "count": web_search_call_count(body), "pass": pass_name}],
    })


def ensure_source(db: SupabaseREST) -> dict[str, Any]:
    payload = {
        "source_key": SOURCE_KEY, "source_family": SOURCE_FAMILY, "display_name": "Broad market discovery",
        "base_url": "https://www.google.com/search", "enabled": True, "health": "UNKNOWN",
        "metadata": {"channel": "OpenAI grounded web search", "scope": "market-wide", "policy_version": DISCOVERY_POLICY},
        "updated_at": utcnow(),
    }
    return db.upsert("source_registry", payload, "source_key")[0]


def ingest_records(db: SupabaseREST, source_id: str, seen_at: str, records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"discovered": len(records), "new_records": 0, "new_opportunities": 0, "linked": 0}
    opportunity_by_identity: dict[tuple[str, str], tuple[str, bool]] = {}
    for item in records:
        identity = (item["normalized_company"], item["normalized_title"])
        if identity not in opportunity_by_identity:
            companies = db.select("companies", {"normalized_name": f"eq.{item['normalized_company']}", "select": "id", "limit": "1"})
            company_id = companies[0]["id"] if companies else db.insert("companies", {"normalized_name": item["normalized_company"], "display_name": item["company"], "updated_at": seen_at})[0]["id"]
            existing = db.select("opportunities", {"company_id": f"eq.{company_id}", "normalized_title": f"eq.{item['normalized_title']}", "lifecycle_state": "eq.ACTIVE", "select": "id", "limit": "1"})
            is_new = not existing
            if existing:
                opportunity_id = existing[0]["id"]
                db.patch("opportunities", {"id": f"eq.{opportunity_id}"}, {"last_seen_at": seen_at, "updated_at": seen_at})
            else:
                role = db.upsert("opportunities", {
                    "canonical_key": item["canonical_key"], "company_id": company_id, "title": item["title"],
                    "normalized_title": item["normalized_title"], "location": item["location"] or None,
                    "description_text": item["description"] or None, "posted_at": item["posted_at"] or None,
                    "first_seen_at": seen_at, "last_seen_at": seen_at, "lifecycle_state": "ACTIVE",
                    "screening_stage": item["screening_stage"], "visibility": item["visibility"],
                    "current_reason_code": item["reason_code"], "current_reason_text": item["reason_text"],
                    "current_confidence": item["confidence"], "policy_version": item["policy_version"],
                    "metadata": item["opportunity_metadata"], "updated_at": seen_at,
                }, "canonical_key")[0]
                opportunity_id = role["id"]
                counts["new_opportunities"] += 1
                db.insert("screening_decisions", {
                    "opportunity_id": opportunity_id, "stage": "DETERMINISTIC_ELIGIBILITY",
                    "outcome": item["screening_stage"], "reason_code": item["reason_code"],
                    "reason_text": item["reason_text"], "confidence": item["confidence"],
                    "evidence": [{"type": "TITLE", "value": item["title"]}, {"type": "DISCOVERY_SIGNAL", "url": item["url"]}],
                    "policy_version": item["policy_version"], "evaluator_type": "DETERMINISTIC",
                })
            opportunity_by_identity[identity] = (opportunity_id, is_new)
        opportunity_id, _ = opportunity_by_identity[identity]
        existing_record = db.select("source_records", {"source_id": f"eq.{source_id}", "external_id": f"eq.{item['external_id']}", "select": "id", "limit": "1"})
        record = db.upsert("source_records", {
            "source_id": source_id, "external_id": item["external_id"], "canonical_url": item["url"],
            "raw_payload": item["raw_payload"], "content_hash": item["content_hash"], "state": "ACTIVE",
            "first_seen_at": seen_at, "last_seen_at": seen_at, "closed_at": None, "updated_at": seen_at,
        }, "source_id,external_id")[0]
        if not existing_record:
            counts["new_records"] += 1
        if item["is_primary"]:
            db.patch("opportunity_sources", {"opportunity_id": f"eq.{opportunity_id}"}, {"is_primary": False})
        db.upsert("opportunity_sources", {"opportunity_id": opportunity_id, "source_record_id": record["id"], "is_primary": item["is_primary"]}, "opportunity_id,source_record_id")
        counts["linked"] += 1
    return counts


def reconcile_probes(db: SupabaseREST, probes: list[dict[str, Any]], discovered: list[dict[str, Any]], checked_at: str) -> tuple[dict[str, int], list[dict[str, Any]]]:
    known_companies = {normalize_text(role["company"]) for role in discovered}
    counts: dict[str, int] = {}
    reconciled: list[dict[str, Any]] = []
    for probe in probes:
        company_name = normalize_text(probe["company"])
        title = normalize_text(probe["title"])
        companies = db.select("companies", {"normalized_name": f"eq.{company_name}", "select": "id", "limit": "1"})
        opportunities: list[dict[str, Any]] = []
        if companies:
            opportunities = db.select("opportunities", {"company_id": f"eq.{companies[0]['id']}", "normalized_title": f"eq.{title}", "select": "id,visibility,lifecycle_state,screening_stage,current_reason_text", "limit": "2"})
        if opportunities:
            role = opportunities[0]
            if role["lifecycle_state"] != "ACTIVE":
                classification, reason = "DISCOVERED_STALE_OR_CLOSED", "Canonical opportunity exists but is no longer active."
            elif role["visibility"] == "SURFACED":
                classification, reason = "DISCOVERED_AND_SURFACED", "Canonical opportunity is present in the primary cockpit."
            else:
                classification = "DISCOVERED_NOT_SURFACED"
                reason = role.get("current_reason_text") or f"Held below the glass at {role.get('screening_stage')}."
            opportunity_id = role["id"]
        else:
            opportunity_id = None
            if company_name in known_companies:
                classification, reason = "MISSED_QUERY_COVERAGE", "Company entered this market scan, but this independently found role did not."
            else:
                classification, reason = "MISSED_SOURCE_COVERAGE", "No direct or market-discovery path has yet captured this company and role."
        counts[classification] = counts.get(classification, 0) + 1
        reconciled.append({
            "probe_key": role_key(probe), "company_name": probe["company"], "title": probe["title"],
            "location": probe.get("location"), "discovery_url": probe["discovery_url"], "official_url": probe.get("official_url"),
            "requisition_id": probe.get("requisition_id"), "found_at": checked_at,
            "source_family": probe.get("source_family") or "WEB_SEARCH", "source_name": probe.get("source_name") or "Independent recall scan",
            "provenance": {"channel": "independent_grounded_web_scan", "snippet": probe.get("snippet")},
            "confidence": probe.get("confidence") or 0, "classification": classification,
            "classification_reason": reason, "canonical_opportunity_id": opportunity_id, "checked_at": checked_at,
        })
    return counts, reconciled


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
    policy_rows = db.select("pursuit_policy", {"id": "eq.1", "select": "version,policy", "limit": "1"})
    policy = policy_rows[0] if policy_rows else {"version": "unavailable", "policy": {}}
    day_bucket = utcnow()[:10]
    probe_hash = discovery_input_hash("independent_recall_probe", policy["version"], day_bucket)
    discovery_hash = discovery_input_hash("market_discovery", policy["version"], day_bucket)
    if discovery_pass_reusable(db, probe_hash) and discovery_pass_reusable(db, discovery_hash):
        print(json.dumps({"status": "SKIPPED_UNCHANGED", "freshness_day": day_bucket}, sort_keys=True))
        return 0
    client = OpenAIResponses()
    source = ensure_source(db)
    started = utcnow()
    ingestion_run = db.insert("ingestion_runs", {"source_id": source["id"], "started_at": started, "status": "RUNNING", "details": {"engine": DISCOVERY_POLICY}})[0]
    try:
        probes, probe_body, probe_route = run_grounded_scan(client, policy, probe=True)
        signals, discovery_body, discovery_route = run_grounded_scan(client, policy, probe=False)
        upsert_model_run(db, probe_body, probe_route, "independent_recall_probe", probe_hash)
        upsert_model_run(db, discovery_body, discovery_route, "market_discovery", discovery_hash)
        records = prepare_records(signals, started)
        counts = ingest_records(db, source["id"], started, records)
        probe_counts, reconciled = reconcile_probes(db, probes, signals, utcnow())
        finished = utcnow()
        db.patch("source_registry", {"id": f"eq.{source['id']}"}, {"health": "HEALTHY", "last_sync_at": finished, "last_success_at": finished, "last_error": None, "updated_at": finished})
        db.patch("ingestion_runs", {"id": f"eq.{ingestion_run['id']}"}, {"finished_at": finished, "status": "PASSED", "discovered_count": len(signals), "new_count": counts["new_opportunities"], "duplicate_count": max(0, counts["linked"] - counts["new_opportunities"]), "details": {**counts, "probe_classifications": probe_counts, "engine": DISCOVERY_POLICY}})
        db.insert("activity_events", {"event_type": "MARKET_DISCOVERY_COMPLETED", "entity_type": "source", "entity_id": source["id"], "severity": "ATTENTION" if any(k.startswith("MISSED_") for k in probe_counts) else "INFO", "message": f"Market discovery captured {len(signals)} signals outside the static employer registry; {len(probes)} independent recall probes reconciled.", "details": {**counts, "probe_classifications": probe_counts, "recall_probes": reconciled, "coverage_semantics": {"health": "connector execution", "coverage": "independent market reach"}}})
        print(json.dumps({**counts, "signals": len(signals), "probes": len(probes), "probe_classifications": probe_counts}, sort_keys=True))
        return 0
    except Exception as exc:
        finished = utcnow()
        message = f"{type(exc).__name__}: {exc}"[:1000]
        db.patch("source_registry", {"id": f"eq.{source['id']}"}, {"health": "FAILED", "last_sync_at": finished, "last_error": message, "updated_at": finished})
        db.patch("ingestion_runs", {"id": f"eq.{ingestion_run['id']}"}, {"finished_at": finished, "status": "FAILED", "error_count": 1, "error_text": message})
        db.insert("activity_events", {"event_type": "MARKET_DISCOVERY_FAILED", "entity_type": "source", "entity_id": source["id"], "severity": "ATTENTION", "message": "Broad market discovery failed.", "details": {"error": message}})
        raise


if __name__ == "__main__":
    raise SystemExit(run())
