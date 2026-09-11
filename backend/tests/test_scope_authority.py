from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_current_scope_authority_outranks_historical_artifacts() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    scope = json.loads((ROOT / "contracts" / "scope_authority.v1.json").read_text(encoding="utf-8"))
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")
    scope_doc = (ROOT / "docs" / "SCOPE_AUTHORITY.md").read_text(encoding="utf-8")

    assert manifest["scope_authority_contract"] == "contracts/scope_authority.v1.json"
    assert manifest["scope_authority_document"] == "docs/SCOPE_AUTHORITY.md"
    assert "contracts/scope_authority.v1.json" in manifest["normative_sources"]
    assert "docs/SCOPE_AUTHORITY.md" in manifest["normative_sources"]

    assert scope["rules"]["historical_artifacts_are_scope_authority"] is False
    assert scope["rules"]["closed_or_merged_pr_may_override_current_main"] is False
    assert scope["rules"]["current_open_issue_may_supersede_prior_completion_statement"] is True
    assert scope["rules"]["stale_historical_conflict_requires_user_approval"] is False

    precedence = scope["precedence"]
    assert precedence.index("CURRENT_MAIN_NORMATIVE_CONTRACTS") < precedence.index("CLOSED_MERGED_PRS_CLOSED_ISSUES_AND_HISTORICAL_SUMMARIES")
    assert precedence.index("CURRENT_OPEN_P0_P1_ISSUES_AND_GO_LIVE_CONTROL_BOARD") < precedence.index("CLOSED_MERGED_PRS_CLOSED_ISSUES_AND_HISTORICAL_SUMMARIES")

    assert policy["scope_authority"]["historical_artifacts_are_scope_authority"] is False
    assert policy["scope_authority"]["stale_historical_conflict_requires_user_approval"] is False
    assert policy["failure_behavior"]["stale_historical_scope_conflict"] == "IGNORE_LOWER_PRECEDENCE_ARTIFACT_AND_CONTINUE"
    assert "STALE_HISTORICAL_SCOPE_CONFLICT" in policy["forbidden_unsolicited_interruptions"]

    assert "PR #8 is historical" in handoff
    assert "Issue #7" in handoff
    assert "additive/non-destructive Issue #7 circuit-breaker migration is explicitly authorized" in handoff
    assert "merged or closed PR/issue is implementation history, not future scope authority" in scope_doc


def test_issue_7_repair_actions_are_explicitly_autonomous() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    scope = json.loads((ROOT / "contracts" / "scope_authority.v1.json").read_text(encoding="utf-8"))

    assert manifest["scope_authority_policy"]["current_issue_7_explicitly_authorizes_additive_reversible_provider_diagnostics_circuit_breaker_migrations_and_commit_push"] is True
    assert manifest["control_plane_write_policy"]["commit_and_push_within_authorized_scope_requires_approval"] is False
    assert manifest["merge_deploy_policy"]["additive_non_destructive_supabase_migration_requires_approval"] is False

    authorized = set(scope["current_p0_authority"]["authorized_additive_reversible_actions"])
    for required in {
        "PROVIDER_DIAGNOSTICS_AND_TELEMETRY",
        "CIRCUIT_BREAKER_AND_BACKPRESSURE_LOGIC",
        "ADDITIVE_NON_DESTRUCTIVE_SUPABASE_MIGRATION",
        "COMMIT_AND_PUSH",
        "RUNTIME_RECONCILIATION",
    }:
        assert required in authorized

    routine = set(policy["routine_autonomous_actions"])
    for required in {
        "COMMIT_AND_PUSH_AUTHORIZED_IMPLEMENTATION",
        "ADDITIVE_NON_DESTRUCTIVE_SCHEMA_MIGRATION",
        "PROVIDER_DIAGNOSTICS_AND_TELEMETRY",
        "CIRCUIT_BREAKER_AND_BACKPRESSURE_LOGIC",
    }:
        assert required in routine
