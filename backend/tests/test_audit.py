from yna.audit import CAPABILITY, SCHEMA
from yna.model_router import ROUTES


def test_false_negative_audit_does_not_bypass_astra_qualification_gate():
    route = ROUTES[CAPABILITY]
    assert route.model_id == "gpt-5.6-sol"
    assert route.reasoning_effort == "high"


def test_false_negative_audit_has_reopen_safety_outcomes():
    outcomes = SCHEMA["properties"]["audit_outcome"]["enum"]
    assert outcomes == ["REJECT_CONFIRMED", "FALSE_NEGATIVE_RISK", "NEEDS_MORE_DATA"]


def test_false_negative_audit_requires_unknowns():
    assert "material_unknowns" in SCHEMA["required"]
    assert SCHEMA["additionalProperties"] is False
