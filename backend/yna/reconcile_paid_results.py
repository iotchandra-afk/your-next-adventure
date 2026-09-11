from __future__ import annotations

import json
import os

from .intake import SupabaseREST
from .triage import (
    _company,
    _eligible_roles,
    _ensure_description,
    _passed_run,
    _private_context,
    _reconcile_durable_decision,
    _source_evidence,
    semantic_input_hash,
)


def run() -> int:
    """Restore exact paid decisions after state repair without calling a model."""
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
    _candidate, _policy, candidate_version, pursuit_policy_version = _private_context(db)
    roles = _eligible_roles(db, 1000)
    restored = 0
    cache_miss = 0
    for role in roles:
        company = _company(db, role["company_id"])
        description = _ensure_description(db, role)
        sources = _source_evidence(db, role["id"])
        input_hash = semantic_input_hash(
            role, company.get("display_name"), description, sources,
            candidate_version, pursuit_policy_version,
        )
        passed = _passed_run(db, role["id"], input_hash)
        if passed and _reconcile_durable_decision(db, role["id"], passed):
            restored += 1
        else:
            cache_miss += 1
    print(json.dumps({"eligible_checked": len(roles), "restored": restored, "cache_miss": cache_miss}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
