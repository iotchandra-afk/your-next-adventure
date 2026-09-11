from yna.economics_replay import replay_roles
from yna.screening import deterministic_screen


KNOWN_GOOD_TITLES = [
    "Director / Sr. Director, Digital Strategy (Consumer)",
    "Director, Portfolio Lead",
    "Executive Director, Business Transformation",
    "Senior Product Director - Aladdin Studio Developer",
    "Technical Product Manager – AI & Enterprise Platforms, Vice President",
    "Vice President, Technology Transformation Lead",
    "VP, AI & Software Engineering",
    "VP, Digital Strategy",
    "VP, Product",
    "Applied AI & Data Science, Vice President",
    "Client Partner (Consumer)",
    "Core Risk Governance – Technology & Risk, RQA, Vice President",
    "Data Quality & Governance, Private Markets, Vice President",
    "DevOps Engineer | Engineering Team Manager, Vice President",
    "Director, Application Engineer",
    "Application Engineering Director",
    "Implementation Consultant, Director",
    "Senior Engineering Team Director - Aladdin Engineering ETF Systems Engineering",
    "Sr Director Application Reliability Engineering & Support",
    "Sr Director, Network Strategy & Planning",
    "Vice President, Private Markets Data Management",
    "VP, Business Transformation & Automation Lead",
    "VP, Revenue Operations",
]


def test_known_good_and_ambiguous_mandates_are_retained() -> None:
    for title in KNOWN_GOOD_TITLES:
        assert deterministic_screen(title)[0] == "ELIGIBLE", title


def test_title_inflation_and_obvious_non_targets_never_reach_paid_triage() -> None:
    examples = [
        "Data Engineer, Vice President",
        "Artificial Intelligence & Machine Learning Engineer, Vice President - AI Labs",
        "Account Executive, Preqin Sales, Vice President",
        "Director & Actuary",
        "Receptionist",
        "Bindery Operator 2",
        "Sales Development Representative",
    ]
    for title in examples:
        stage, visibility, _reason, _confidence = deterministic_screen(title)
        assert (stage, visibility) == ("TRIAGE_CLEAR_NO", "HIDDEN"), title


def test_offline_replay_proves_1000_role_gate_without_provider_calls() -> None:
    obvious = [{"title": f"Office Services Associate {i}", "label": "CLEAR_NO"} for i in range(920)]
    good = [{"title": KNOWN_GOOD_TITLES[i % len(KNOWN_GOOD_TITLES)], "label": "RELEVANT" if i < 20 else "POSSIBLE"} for i in range(40)]
    ambiguous_no = [{"title": f"Director, Product Operations {i}", "label": "CLEAR_NO"} for i in range(40)]
    report = replay_roles(obvious + good + ambiguous_no, historical_sol_cost_per_role=0.02291, historical_astra_cost_per_role=0.08)
    assert report["representative_roles"] == 1000
    assert report["known_good_recall"] == 1.0
    assert report["projected_sol_fraction"] <= 0.10
    assert report["projected_astra_fraction"] <= 0.02
    assert report["projected_cost_per_1000"]["paid_screening_sol_usd"] <= 2.0
    assert report["false_negatives"] == []
