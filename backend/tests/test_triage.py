from yna.model_router import ROUTES
from yna.triage import CAPABILITY, SCHEMA, _eligible_roles


def test_relevance_triage_uses_sol_high():
    route = ROUTES[CAPABILITY]
    assert route.model_id == "gpt-5.6-sol"
    assert route.reasoning_effort == "high"


def test_relevance_triage_has_gray_zone():
    outcomes = SCHEMA["properties"]["outcome"]["enum"]
    assert outcomes == ["RELEVANT", "POSSIBLE", "CLEAR_NO"]


def test_relevance_triage_requires_material_unknowns():
    assert "material_unknowns" in SCHEMA["required"]
    assert SCHEMA["additionalProperties"] is False


def test_eligible_query_uses_canonical_stage_not_retired_reason_code():
    class DB:
        def select(self, table, filters):
            assert table == "opportunities"
            assert filters["screening_stage"] == "eq.ELIGIBLE"
            assert "current_reason_code" not in filters
            return [{"id": "residual-ambiguity"}]

    assert _eligible_roles(DB(), 10) == [{"id": "residual-ambiguity"}]
