from __future__ import annotations

import json
import os
from pathlib import Path

from .intake import SupabaseREST
from .model_router import OpenAIResponses
from .triage import INSTRUCTIONS, SCHEMA, _private_context


def run() -> int:
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if not secret:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    root = Path(__file__).resolve().parents[2]
    cases = json.loads((root / "evals" / "relevance_golden.json").read_text(encoding="utf-8"))
    db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
    candidate, pursuit_policy, candidate_version, pursuit_policy_version = _private_context(db)
    ai = OpenAIResponses()
    failures: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    for case in cases:
        context = {
            "opportunity": {
                "id": f"golden:{case['id']}",
                "company": case["company"],
                "title": case["title"],
                "location": case["location"],
                "description": case["description"],
                "source_evidence": [{"source_family": "GOLDEN_FIXTURE", "state": "ACTIVE"}],
            },
            "candidate_truth": candidate,
            "candidate_truth_version": candidate_version,
            "pursuit_policy": pursuit_policy,
            "pursuit_policy_version": pursuit_policy_version,
        }
        result, _, route = ai.structured(
            "RELEVANCE_TRIAGE",
            INSTRUCTIONS,
            json.dumps(context, ensure_ascii=False),
            "relevance_triage_golden",
            SCHEMA,
        )
        actual = result["outcome"]
        allowed = case["allowed_outcomes"]
        row = {"id": case["id"], "actual": actual, "allowed": allowed, "model": route.model_id, "effort": route.reasoning_effort}
        results.append(row)
        if actual not in allowed:
            failures.append(row)
    print(json.dumps({"cases": results, "failures": failures}, sort_keys=True))
    if failures:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
