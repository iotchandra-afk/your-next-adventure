from __future__ import annotations

from typing import Any

import requests

from .intake import strip_html

USER_AGENT = "YourNextAdventure/0.1 (+executive-opportunity-intelligence)"


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        text = strip_html(value)
        return [text] if text else []
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


def fetch_job_detail(source_family: str, source_metadata: dict[str, Any], external_id: str, raw_payload: dict[str, Any]) -> str:
    """Fetch full role text only after the role has earned enrichment cost.

    Discovery intentionally avoids per-role detail calls. This adapter is invoked by
    relevance/intelligence capabilities for selected opportunities.
    """
    listing = raw_payload.get("listing") if isinstance(raw_payload, dict) else None
    listing = listing if isinstance(listing, dict) else raw_payload
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    if source_family == "WORKDAY":
        path = (listing or {}).get("externalPath") or external_id
        if not path.startswith("/"):
            path = "/" + path
        base = f"https://{source_metadata['host']}/wday/cxs/{source_metadata['tenant']}/{source_metadata['site']}"
        response = session.get(f"{base}{path}", timeout=30)
        response.raise_for_status()
        detail = response.json()
        info = detail.get("jobPostingInfo") or detail
        return strip_html(info.get("jobDescription") or info.get("description") or "")

    if source_family == "SMARTRECRUITERS":
        company = source_metadata["company_identifier"]
        response = session.get(
            f"https://api.smartrecruiters.com/v1/companies/{company}/postings/{external_id}",
            timeout=30,
        )
        response.raise_for_status()
        detail = response.json()
        sections = (detail.get("jobAd") or {}).get("sections") or {}
        return " ".join(x for x in _flatten_strings(sections) if x)

    return ""
