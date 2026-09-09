from yna.intake import canonical_key, normalize_text, strip_html
from yna.screening import deterministic_screen


def test_normalize_text_is_stable():
    assert normalize_text("  Vice-President, AI & Transformation ") == "vice president ai transformation"


def test_canonical_key_collapses_formatting_noise():
    assert canonical_key("ICONIQ", "VP - Technology Transformation", "New York, NY") == canonical_key(
        "iconiq", "VP Technology Transformation", "new york ny"
    )


def test_director_plus_is_eligible_not_surfaced():
    stage, visibility, reason, confidence = deterministic_screen("Vice President, Technology Transformation Lead")
    assert stage == "ELIGIBLE"
    assert visibility == "HIDDEN"
    assert reason == "EXECUTIVE_SCOPE_PLAUSIBLE"
    assert confidence >= 0.9


def test_ceo_acronym_is_never_false_negative():
    stage, visibility, reason, _ = deterministic_screen("CEO, AI Services - US-Based")
    assert stage == "ELIGIBLE"
    assert visibility == "HIDDEN"
    assert reason == "EXECUTIVE_SCOPE_PLAUSIBLE"


def test_ambiguous_title_is_retained_for_mandate_triage():
    stage, visibility, reason, confidence = deterministic_screen("Senior Product Manager")
    assert stage == "ELIGIBLE"
    assert visibility == "HIDDEN"
    assert reason == "MANDATE_REVIEW_REQUIRED"
    assert confidence < 0.7


def test_clear_non_target_title_is_hidden_reject():
    stage, visibility, reason, confidence = deterministic_screen("Sales Development Representative")
    assert stage == "TRIAGE_CLEAR_NO"
    assert visibility == "HIDDEN"
    assert reason == "CLEAR_NON_TARGET_TITLE"
    assert confidence >= 0.99


def test_revenue_ops_not_killed_by_sales_filter():
    stage, _, _, _ = deterministic_screen("VP, Revenue Operations")
    assert stage == "ELIGIBLE"


def test_html_cleanup():
    assert strip_html("<p>Build <strong>AI</strong> systems &amp; operating models.</p>") == "Build AI systems & operating models."
