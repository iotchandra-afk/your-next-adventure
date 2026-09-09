from yna.model_router import ROUTES
from yna.qualification import CAPABILITY, SCHEMA


def test_deep_qualification_uses_astra_high():
    route = ROUTES[CAPABILITY]
    assert route.model_id == "gpt-6-astra"
    assert route.reasoning_effort == "high"


def test_deep_qualification_has_required_decision_classes():
    assert SCHEMA["properties"]["decision_class"]["enum"] == [
        "TIER_1_DEEP_QUALIFY",
        "TIER_2_WORTH_EXPLORING",
        "TIER_3_MONITOR",
        "NEEDS_DATA",
        "REJECT",
    ]


def test_deep_qualification_uses_native_classes_without_fit_score():
    assert "native_class" in SCHEMA["required"]
    assert "material_unknowns" in SCHEMA["required"]
    assert "fit_score" not in SCHEMA["properties"]
