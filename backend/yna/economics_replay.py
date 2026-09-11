from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from .screening import deterministic_screen

KNOWN_GOOD_OUTCOMES = {"RELEVANT", "POSSIBLE"}


def replay_roles(
    roles: Iterable[dict[str, Any]],
    *,
    historical_sol_cost_per_role: float,
    historical_astra_cost_per_role: float,
) -> dict[str, Any]:
    """Replay persisted labels without making provider calls or retaining raw rows."""
    rows = list(roles)
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    false_negatives: list[dict[str, str]] = []
    sol_count = 0
    astra_count = 0
    known_good = 0
    retained_good = 0

    for row in rows:
        stage, _visibility, reason, _confidence = deterministic_screen(str(row.get("title") or ""))
        gate = "SOL_AMBIGUITY" if stage == "ELIGIBLE" else "DETERMINISTIC_CLEAR_NO"
        label = str(row.get("label") or "UNLABELED")
        confusion[gate][label] += 1
        if gate == "SOL_AMBIGUITY":
            sol_count += 1
        if label in KNOWN_GOOD_OUTCOMES:
            known_good += 1
            if gate == "SOL_AMBIGUITY":
                retained_good += 1
            else:
                false_negatives.append({"title": str(row.get("title") or ""), "label": label, "gate_reason": reason})
        if label == "RELEVANT" and gate == "SOL_AMBIGUITY":
            astra_count += 1

    total = len(rows)
    per_thousand = 1000 / total if total else 0
    sol_cost = sol_count * per_thousand * historical_sol_cost_per_role
    astra_cost = astra_count * per_thousand * historical_astra_cost_per_role
    return {
        "representative_roles": total,
        "deterministic_elimination_count": total - sol_count,
        "deterministic_elimination_rate": round((total - sol_count) / total, 6) if total else 0,
        "known_good_count": known_good,
        "known_good_retained": retained_good,
        "known_good_recall": round(retained_good / known_good, 6) if known_good else None,
        "false_negatives": false_negatives,
        "confusion_matrix_by_gate": {gate: dict(counts) for gate, counts in sorted(confusion.items())},
        "projected_sol_count": sol_count,
        "projected_sol_fraction": round(sol_count / total, 6) if total else 0,
        "projected_astra_count": astra_count,
        "projected_astra_fraction": round(astra_count / total, 6) if total else 0,
        "historical_unit_costs": {
            "sol_triage_usd": historical_sol_cost_per_role,
            "astra_qualification_usd": historical_astra_cost_per_role,
        },
        "projected_cost_per_1000": {
            "paid_screening_sol_usd": round(sol_cost, 4),
            "downstream_astra_qualification_usd": round(astra_cost, 4),
            "full_route_usd": round(sol_cost + astra_cost, 4),
        },
    }
