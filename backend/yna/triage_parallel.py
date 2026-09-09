from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .intake import SupabaseREST
from .model_router import OpenAIResponses
from .triage import _eligible_roles, _private_context, triage_one


DEFAULT_LIMIT = 64
MAX_LIMIT = 96
DEFAULT_WORKERS = 6
MAX_WORKERS = 8


def _db(secret: str, url: str) -> SupabaseREST:
    # Each worker gets its own requests.Session via SupabaseREST. Sharing one Session
    # across threads is deliberately avoided.
    return SupabaseREST(url, secret)


def _evaluate(
    secret: str,
    url: str,
    role: dict[str, Any],
    candidate: dict[str, Any],
    pursuit_policy: dict[str, Any],
    candidate_version: str,
    pursuit_policy_version: str,
) -> tuple[str, str]:
    db = _db(secret, url)
    ai = OpenAIResponses()
    outcome = triage_one(
        db,
        ai,
        role,
        candidate,
        pursuit_policy,
        candidate_version,
        pursuit_policy_version,
    )
    return role["id"], outcome


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required")

    url = os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co")
    limit = max(1, min(int(os.environ.get("TRIAGE_LIMIT", str(DEFAULT_LIMIT))), MAX_LIMIT))
    workers = max(1, min(int(os.environ.get("TRIAGE_WORKERS", str(DEFAULT_WORKERS))), MAX_WORKERS))

    controller = _db(secret, url)
    candidate, pursuit_policy, candidate_version, pursuit_policy_version = _private_context(controller)
    roles = _eligible_roles(controller, limit)

    results = {"RELEVANT": 0, "POSSIBLE": 0, "CLEAR_NO": 0, "SKIPPED_UNCHANGED": 0, "FAILED": 0}
    failures: list[dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="triage") as pool:
        futures = {
            pool.submit(
                _evaluate,
                secret,
                url,
                role,
                candidate,
                pursuit_policy,
                candidate_version,
                pursuit_policy_version,
            ): role
            for role in roles
        }
        for future in as_completed(futures):
            role = futures[future]
            try:
                _, outcome = future.result()
                results[outcome] += 1
            except Exception as exc:
                results["FAILED"] += 1
                error = f"{type(exc).__name__}: {exc}"[:1000]
                failures.append({"opportunity_id": role["id"], "error": error})
                controller.insert("activity_events", {
                    "event_type": "RELEVANCE_TRIAGE_FAILED",
                    "entity_type": "opportunity",
                    "entity_id": role["id"],
                    "severity": "ATTENTION",
                    "message": "Mandate relevance triage failed; opportunity remains retained and unsurfaced.",
                    "details": {"error": error},
                })

    controller.insert("activity_events", {
        "event_type": "RELEVANCE_TRIAGE_BATCH_COMPLETED",
        "severity": "INFO" if results["FAILED"] == 0 else "ATTENTION",
        "message": f"Mandate relevance triage evaluated {len(roles)} retained executive opportunities with bounded concurrency.",
        "details": {**results, "workers": workers, "limit": limit, "failures": failures[:10]},
    })
    print(json.dumps({**results, "workers": workers, "limit": limit}, sort_keys=True))
    return 0 if results["FAILED"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
