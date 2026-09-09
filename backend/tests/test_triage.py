from yna.model_router import ROUTES
from yna.triage import CAPABILITY, SCHEMA


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
