from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

import requests

POLICY_VERSION = "screening-v1"
USER_AGENT = "YourNextAdventure/0.1 (+executive-opportunity-intelligence)"
EXECUTIVE_PATTERNS = (
    r"\bvice president\b", r"\bvp\b", r"\bsvp\b", r"\bevp\b",
    r"\bsenior director\b", r"\bsr\.? director\b", r"\bdirector\b",
    r"\bhead of\b", r"\bglobal head\b", r"\bchief\b",
    r"\bmanaging director\b", r"\bexecutive director\b", r"\bgeneral manager\b",
)
CLEAR_NON_TARGET_PATTERNS = (
    r"\baccount executive\b", r"\bsales development representative\b",
    r"\bbusiness development representative\b", r"\badministrative assistant\b",
    r"\bexecutive assistant\b", r"\bintern(ship)?\b",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: str | None) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", value, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def content_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def canonical_key(company: str, title: str, location: str | None) -> str:
    raw = "|".join((normalize_text(company), normalize_text(title), normalize_text(location)))
    return hashlib.sha256(raw.encode()).hexdigest()


def deterministic_screen(title: str) -> tuple[str, str, str, float]:
    normalized = normalize_text(title)
    if any(re.search(pattern, normalized) for pattern in CLEAR_NON_TARGET_PATTERNS):
        return "TRIAGE_CLEAR_NO", "HIDDEN", "CLEAR_NON_TARGET_TITLE", 0.99
    if not any(re.search(pattern, normalized) for pattern in EXECUTIVE_PATTERNS):
        return "TRIAGE_CLEAR_NO", "HIDDEN", "BELOW_EXECUTIVE_SCOPE", 0.97
    return "ELIGIBLE", "HIDDEN", "EXECUTIVE_SCOPE_PLAUSIBLE", 0.90


@dataclass
class RawJob:
    external_id: str
    title: str
    location: str | None
    url: str | None
    description: str
    posted_at: str | None
    payload: dict[str, Any]


class SupabaseREST:
    def __init__(self, url: str, secret: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def select(self, table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        response = self.session.get(f"{self.base}/{table}", params=params or {}, timeout=30)
        response.raise_for_status()
        return response.json()

    def insert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        headers = {"Prefer": "return=representation"}
        response = self.session.post(f"{self.base}/{table}", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def upsert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]], on_conflict: str) -> list[dict[str, Any]]:
        headers = {"Prefer": "resolution=merge-duplicates,return=representation"}
        response = self.session.post(
            f"{self.base}/{table}", params={"on_conflict": on_conflict}, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def patch(self, table: str, filters: dict[str, str], payload: dict[str, Any]) -> None:
        headers = {"Prefer": "return=minimal"}
        response = self.session.patch(f"{self.base}/{table}", params=filters, json=payload, headers=headers, timeout=30)
        response.raise_for_status()


class JobAdapter:
    def __init__(self, source: dict[str, Any]):
        self.source = source
        self.meta = source["metadata"]
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def fetch(self) -> list[RawJob]:
        raise NotImplementedError


class GreenhouseAdapter(JobAdapter):
    def fetch(self) -> list[RawJob]:
        token = self.meta["board_token"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
        response = self.http.get(url, params={"content": "true"}, timeout=45)
        response.raise_for_status()
        result: list[RawJob] = []
        for job in response.json().get("jobs", []):
            result.append(RawJob(
                external_id=str(job["id"]),
                title=job.get("title") or "Untitled",
                location=(job.get("location") or {}).get("name"),
                url=job.get("absolute_url"),
                description=strip_html(job.get("content")),
                posted_at=job.get("updated_at"),
                payload=job,
            ))
        return result


class LeverAdapter(JobAdapter):
    def fetch(self) -> list[RawJob]:
        site = self.meta["site"]
        response = self.http.get(f"https://api.lever.co/v0/postings/{site}", params={"mode": "json"}, timeout=45)
        response.raise_for_status()
        result: list[RawJob] = []
        for job in response.json():
            categories = job.get("categories") or {}
            description_parts = [job.get("descriptionPlain") or job.get("description") or ""]
            for section in job.get("lists") or []:
                description_parts.append(strip_html(section.get("content")))
            created = job.get("createdAt")
            posted = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat() if isinstance(created, (int, float)) else None
            result.append(RawJob(
                external_id=str(job["id"]),
                title=job.get("text") or "Untitled",
                location=categories.get("location"),
                url=job.get("hostedUrl") or job.get("applyUrl"),
                description=" ".join(filter(None, map(strip_html, description_parts))),
                posted_at=posted,
                payload=job,
            ))
        return result


class SmartRecruitersAdapter(JobAdapter):
    def fetch(self) -> list[RawJob]:
        company = self.meta["company_identifier"]
        base = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
        offset = 0
        result: list[RawJob] = []
        while offset < 1000:
            response = self.http.get(base, params={"limit": 100, "offset": offset}, timeout=45)
            response.raise_for_status()
            body = response.json()
            items = body.get("content", [])
            if not items:
                break
            for job in items:
                loc = job.get("location") or {}
                location = ", ".join(filter(None, [loc.get("city"), loc.get("region"), loc.get("country")])) or None
                result.append(RawJob(
                    external_id=str(job.get("id")),
                    title=job.get("name") or "Untitled",
                    location=location,
                    url=job.get("ref") or job.get("applyUrl"),
                    description="",
                    posted_at=job.get("releasedDate"),
                    payload=job,
                ))
            offset += len(items)
            if offset >= int(body.get("totalFound") or offset):
                break
        return result


class WorkdayAdapter(JobAdapter):
    def fetch(self) -> list[RawJob]:
        host, tenant, site = self.meta["host"], self.meta["tenant"], self.meta["site"]
        base = f"https://{host}/wday/cxs/{tenant}/{site}"
        offset = 0
        limit = 20
        result: list[RawJob] = []
        while offset < 1000:
            response = self.http.post(
                f"{base}/jobs",
                json={"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""},
                timeout=45,
            )
            response.raise_for_status()
            body = response.json()
            items = body.get("jobPostings", [])
            if not items:
                break
            for job in items:
                path = job.get("externalPath") or ""
                result.append(RawJob(
                    external_id=path or content_hash(job)[:24],
                    title=job.get("title") or "Untitled",
                    location=job.get("locationsText"),
                    url=urljoin(f"https://{host}/{site}/", path.lstrip("/")) if path else None,
                    description="",
                    posted_at=None,
                    payload=job,
                ))
            offset += len(items)
            total = int(body.get("total") or offset)
            if offset >= total:
                break
        return result


ADAPTERS = {
    "GREENHOUSE": GreenhouseAdapter,
    "LEVER": LeverAdapter,
    "SMARTRECRUITERS": SmartRecruitersAdapter,
    "WORKDAY": WorkdayAdapter,
}


def seed_sources(db: SupabaseREST, catalog_path: Path) -> list[dict[str, Any]]:
    catalog = json.loads(catalog_path.read_text())
    now = utcnow()
    owned_keys = {source["source_key"] for source in catalog}
    for source in catalog:
        payload = {**source, "enabled": True, "updated_at": now}
        db.upsert("source_registry", payload, "source_key")
    # The registry is shared by independent pipelines. Direct ATS intake owns only
    # catalogued adapter sources; it must never fetch or mutate discovery-channel
    # health simply because that source is enabled in the same canonical table.
    rows = db.select("source_registry", {"enabled": "eq.true", "order": "display_name.asc"})
    return [row for row in rows if row.get("source_key") in owned_keys and row.get("source_family") in ADAPTERS]


def get_or_create_company(db: SupabaseREST, company_name: str) -> str:
    normalized = normalize_text(company_name)
    rows = db.select("companies", {"normalized_name": f"eq.{normalized}", "limit": "1"})
    if rows:
        return rows[0]["id"]
    return db.insert("companies", {"normalized_name": normalized, "display_name": company_name})[0]["id"]


def upsert_canonical_role(db: SupabaseREST, source: dict[str, Any], source_record_id: str, job: RawJob) -> tuple[str, bool]:
    company_name = source["metadata"]["company_name"]
    company_id = get_or_create_company(db, company_name)
    key = canonical_key(company_name, job.title, job.location)
    existing = db.select("opportunities", {"canonical_key": f"eq.{key}", "limit": "1"})
    stage, visibility, reason_code, confidence = deterministic_screen(job.title)
    now = utcnow()
    payload = {
        "canonical_key": key,
        "company_id": company_id,
        "title": job.title,
        "normalized_title": normalize_text(job.title),
        "location": job.location,
        "description_text": job.description or None,
        "posted_at": job.posted_at,
        "last_seen_at": now,
        "lifecycle_state": "ACTIVE",
        "screening_stage": stage,
        "visibility": visibility,
        "current_reason_code": reason_code,
        "current_reason_text": "Plausible executive scope; retained for mandate triage." if stage == "ELIGIBLE" else "Deterministic title screen found no plausible Director+ executive mandate.",
        "current_confidence": confidence,
        "policy_version": POLICY_VERSION,
    }
    if not existing:
        payload["first_seen_at"] = now
    role = db.upsert("opportunities", payload, "canonical_key")[0]
    db.upsert("opportunity_sources", {
        "opportunity_id": role["id"], "source_record_id": source_record_id, "is_primary": not bool(existing)
    }, "opportunity_id,source_record_id")
    if not existing or existing[0].get("screening_stage") != stage or existing[0].get("current_reason_code") != reason_code:
        db.insert("screening_decisions", {
            "opportunity_id": role["id"],
            "stage": "DETERMINISTIC_ELIGIBILITY",
            "outcome": stage,
            "reason_code": reason_code,
            "reason_text": payload["current_reason_text"],
            "confidence": confidence,
            "evidence": [{"type": "TITLE", "value": job.title}],
            "policy_version": POLICY_VERSION,
            "evaluator_type": "DETERMINISTIC",
        })
    return role["id"], not bool(existing)


def sync_source(db: SupabaseREST, source: dict[str, Any]) -> dict[str, int]:
    source_id = source["id"]
    started = utcnow()
    run = db.insert("ingestion_runs", {"source_id": source_id, "started_at": started, "status": "RUNNING"})[0]
    counts = {"discovered": 0, "new": 0, "changed": 0, "duplicate": 0, "closed": 0, "errors": 0}
    try:
        adapter_cls = ADAPTERS[source["source_family"]]
        jobs = adapter_cls(source).fetch()
        counts["discovered"] = len(jobs)
        seen_external: set[str] = set()
        for job in jobs:
            if not job.external_id or job.external_id in seen_external:
                counts["duplicate"] += 1
                continue
            seen_external.add(job.external_id)
            digest = content_hash(job.payload)
            existing = db.select("source_records", {
                "source_id": f"eq.{source_id}", "external_id": f"eq.{job.external_id}", "limit": "1"
            })
            state = "ACTIVE"
            if not existing:
                counts["new"] += 1
            elif existing[0]["content_hash"] != digest:
                state = "CHANGED"
                counts["changed"] += 1
            else:
                counts["duplicate"] += 1
            record_payload = {
                "source_id": source_id,
                "external_id": job.external_id,
                "canonical_url": job.url,
                "raw_payload": job.payload,
                "content_hash": digest,
                "state": state,
                "last_seen_at": started,
                "closed_at": None,
                "updated_at": utcnow(),
            }
            if not existing:
                record_payload["first_seen_at"] = started
            record = db.upsert("source_records", record_payload, "source_id,external_id")[0]
            upsert_canonical_role(db, source, record["id"], job)

        stale = db.select("source_records", {
            "source_id": f"eq.{source_id}", "last_seen_at": f"lt.{started}", "state": "neq.CLOSED", "select": "id"
        })
        for row in stale:
            db.patch("source_records", {"id": f"eq.{row['id']}"}, {"state": "CLOSED", "closed_at": utcnow(), "updated_at": utcnow()})
            counts["closed"] += 1

        db.patch("source_registry", {"id": f"eq.{source_id}"}, {
            "health": "HEALTHY", "last_sync_at": utcnow(), "last_success_at": utcnow(), "last_error": None, "updated_at": utcnow()
        })
        db.patch("ingestion_runs", {"id": f"eq.{run['id']}"}, {
            "finished_at": utcnow(), "status": "PASSED", "discovered_count": counts["discovered"],
            "new_count": counts["new"], "changed_count": counts["changed"], "duplicate_count": counts["duplicate"],
            "closed_count": counts["closed"], "error_count": 0,
        })
        db.insert("activity_events", {
            "event_type": "SOURCE_SYNC_COMPLETED", "entity_type": "source", "entity_id": source_id,
            "severity": "INFO", "message": f"{source['display_name']} intake completed: {counts['discovered']} signals discovered.",
            "details": counts,
        })
    except Exception as exc:
        counts["errors"] += 1
        message = f"{type(exc).__name__}: {exc}"[:1000]
        db.patch("source_registry", {"id": f"eq.{source_id}"}, {
            "health": "FAILED", "last_sync_at": utcnow(), "last_error": message, "updated_at": utcnow()
        })
        db.patch("ingestion_runs", {"id": f"eq.{run['id']}"}, {
            "finished_at": utcnow(), "status": "FAILED", "error_count": 1, "error_text": message,
        })
        db.insert("activity_events", {
            "event_type": "SOURCE_SYNC_FAILED", "entity_type": "source", "entity_id": source_id,
            "severity": "ATTENTION", "message": f"{source['display_name']} intake failed.", "details": {"error": message},
        })
        print(f"SOURCE FAILED {source['source_key']}: {message}", file=sys.stderr)
    return counts


def run() -> int:
    supabase_url = os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co")
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    root = Path(__file__).resolve().parents[2]
    db = SupabaseREST(supabase_url, secret)
    sources = seed_sources(db, root / "config" / "sources.json")
    totals = {"discovered": 0, "new": 0, "changed": 0, "duplicate": 0, "closed": 0, "errors": 0}
    family_health: dict[str, bool] = {}
    for source in sources:
        counts = sync_source(db, source)
        for key in totals:
            totals[key] += counts[key]
        family_health[source["source_family"]] = family_health.get(source["source_family"], False) or counts["errors"] == 0
        time.sleep(0.15)
    healthy_families = sum(family_health.values())
    db.insert("activity_events", {
        "event_type": "INTAKE_CYCLE_COMPLETED",
        "severity": "INFO" if healthy_families >= 3 else "ATTENTION",
        "message": f"Intake cycle completed across {healthy_families} healthy source families.",
        "details": {**totals, "healthy_families": healthy_families},
    })
    print(json.dumps({**totals, "healthy_families": healthy_families}, sort_keys=True))
    return 0 if healthy_families >= 3 else 2


if __name__ == "__main__":
    raise SystemExit(run())
