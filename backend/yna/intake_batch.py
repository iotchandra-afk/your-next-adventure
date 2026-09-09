from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

from .intake import (
    ADAPTERS,
    POLICY_VERSION,
    RawJob,
    SupabaseREST,
    canonical_key,
    content_hash,
    deterministic_screen,
    normalize_text,
    seed_sources,
    strip_html,
    utcnow,
)


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [strip_html(value)] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_flatten_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for key, item in value.items():
            if key.lower() not in {"id", "ref", "url", "applyurl", "company"}:
                out.extend(_flatten_strings(item))
        return out
    return []


def enrich_if_needed(source: dict[str, Any], job: RawJob) -> RawJob:
    stage, _, _, _ = deterministic_screen(job.title)
    if stage != "ELIGIBLE" or job.description:
        return job

    family = source["source_family"]
    meta = source["metadata"]
    session = requests.Session()
    session.headers.update({"User-Agent": "YourNextAdventure/0.1", "Accept": "application/json"})

    try:
        if family == "WORKDAY":
            path = job.payload.get("externalPath") or job.external_id
            base = f"https://{meta['host']}/wday/cxs/{meta['tenant']}/{meta['site']}"
            response = session.get(f"{base}{path}", timeout=30)
            response.raise_for_status()
            detail = response.json()
            info = detail.get("jobPostingInfo") or detail
            description = strip_html(info.get("jobDescription") or info.get("description") or "")
            if description:
                job.description = description
                job.payload = {"listing": job.payload, "detail": detail}
        elif family == "SMARTRECRUITERS":
            company = meta["company_identifier"]
            response = session.get(
                f"https://api.smartrecruiters.com/v1/companies/{company}/postings/{job.external_id}", timeout=30
            )
            response.raise_for_status()
            detail = response.json()
            sections = (detail.get("jobAd") or {}).get("sections") or {}
            description = " ".join(x for x in _flatten_strings(sections) if x)
            if description:
                job.description = description
                job.payload = {"listing": job.payload, "detail": detail}
    except Exception as exc:
        # Enrichment failure does not invalidate a valid source listing. Triage can retain it as POSSIBLE.
        job.payload = {"listing": job.payload, "enrichment_error": f"{type(exc).__name__}: {exc}"[:500]}
    return job


def prepare_snapshot(source: dict[str, Any], jobs: list[RawJob]) -> tuple[list[dict[str, Any]], int]:
    company = source["metadata"]["company_name"]
    prepared: list[dict[str, Any]] = []
    seen: set[str] = set()
    repeated = 0
    for job in jobs:
        if not job.external_id or job.external_id in seen:
            repeated += 1
            continue
        seen.add(job.external_id)
        job = enrich_if_needed(source, job)
        stage, visibility, reason_code, confidence = deterministic_screen(job.title)
        reason_text = (
            "Plausible Director+ executive scope; retained for mandate-aware relevance triage."
            if stage == "ELIGIBLE"
            else "High-confidence deterministic title screen found no plausible Director+ executive mandate."
        )
        prepared.append({
            "external_id": job.external_id,
            "url": job.url or "",
            "payload": job.payload,
            "content_hash": content_hash(job.payload),
            "canonical_key": canonical_key(company, job.title, job.location),
            "title": job.title,
            "normalized_title": normalize_text(job.title),
            "location": job.location or "",
            "description": job.description or "",
            "posted_at": job.posted_at or "",
            "screening_stage": stage,
            "visibility": visibility,
            "reason_code": reason_code,
            "reason_text": reason_text,
            "confidence": confidence,
            "policy_version": POLICY_VERSION,
        })
    return prepared, repeated


def ingest_snapshot(db: SupabaseREST, source: dict[str, Any], prepared: list[dict[str, Any]], seen_at: str) -> dict[str, int]:
    response = db.session.post(
        f"{db.base}/rpc/ingest_source_snapshot",
        json={
            "p_source_id": source["id"],
            "p_company_name": source["metadata"]["company_name"],
            "p_seen_at": seen_at,
            "p_jobs": prepared,
        },
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    if isinstance(body, list) and body:
        body = body[0]
    return {k: int(body.get(k, 0)) for k in ("discovered", "new", "changed", "unchanged", "closed")}


def sync_source(db: SupabaseREST, source: dict[str, Any]) -> dict[str, int]:
    source_id = source["id"]
    started = utcnow()
    run = db.insert("ingestion_runs", {"source_id": source_id, "started_at": started, "status": "RUNNING"})[0]
    counts = {"discovered": 0, "new": 0, "changed": 0, "duplicate": 0, "closed": 0, "errors": 0}
    try:
        jobs = ADAPTERS[source["source_family"]](source).fetch()
        prepared, repeated = prepare_snapshot(source, jobs)
        batch = ingest_snapshot(db, source, prepared, started)
        counts.update({
            "discovered": batch["discovered"],
            "new": batch["new"],
            "changed": batch["changed"],
            "duplicate": repeated,
            "closed": batch["closed"],
        })
        finished = utcnow()
        db.patch("source_registry", {"id": f"eq.{source_id}"}, {
            "health": "HEALTHY", "last_sync_at": finished, "last_success_at": finished,
            "last_error": None, "updated_at": finished,
        })
        db.patch("ingestion_runs", {"id": f"eq.{run['id']}"}, {
            "finished_at": finished, "status": "PASSED",
            "discovered_count": counts["discovered"], "new_count": counts["new"],
            "changed_count": counts["changed"], "duplicate_count": counts["duplicate"],
            "closed_count": counts["closed"], "error_count": 0,
            "details": {"unchanged": batch["unchanged"], "engine": "batch_rpc_v1"},
        })
        db.insert("activity_events", {
            "event_type": "SOURCE_SYNC_COMPLETED", "entity_type": "source", "entity_id": source_id,
            "severity": "INFO",
            "message": f"{source['display_name']} intake completed: {counts['discovered']} signals below the glass.",
            "details": counts,
        })
    except Exception as exc:
        counts["errors"] = 1
        message = f"{type(exc).__name__}: {exc}"[:1000]
        finished = utcnow()
        db.patch("source_registry", {"id": f"eq.{source_id}"}, {
            "health": "FAILED", "last_sync_at": finished, "last_error": message, "updated_at": finished,
        })
        db.patch("ingestion_runs", {"id": f"eq.{run['id']}"}, {
            "finished_at": finished, "status": "FAILED", "error_count": 1, "error_text": message,
        })
        db.insert("activity_events", {
            "event_type": "SOURCE_SYNC_FAILED", "entity_type": "source", "entity_id": source_id,
            "severity": "ATTENTION", "message": f"{source['display_name']} intake failed.",
            "details": {"error": message},
        })
        print(f"SOURCE FAILED {source['source_key']}: {message}", file=sys.stderr)
    return counts


def run() -> int:
    url = os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co")
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    root = Path(__file__).resolve().parents[2]
    db = SupabaseREST(url, secret)
    sources = seed_sources(db, root / "config" / "sources.json")
    totals = {"discovered": 0, "new": 0, "changed": 0, "duplicate": 0, "closed": 0, "errors": 0}
    family_health: dict[str, bool] = {}
    for source in sources:
        counts = sync_source(db, source)
        for key in totals:
            totals[key] += counts[key]
        family = source["source_family"]
        family_health[family] = family_health.get(family, False) or counts["errors"] == 0
        time.sleep(0.1)
    healthy = sum(family_health.values())
    db.insert("activity_events", {
        "event_type": "INTAKE_CYCLE_COMPLETED",
        "severity": "INFO" if healthy >= 3 else "ATTENTION",
        "message": f"Intake cycle completed across {healthy} healthy ATS/source families.",
        "details": {**totals, "healthy_families": healthy},
    })
    print(json.dumps({**totals, "healthy_families": healthy}, sort_keys=True))
    return 0 if healthy >= 3 else 2


if __name__ == "__main__":
    raise SystemExit(run())
