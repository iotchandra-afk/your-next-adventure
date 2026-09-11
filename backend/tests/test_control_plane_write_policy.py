from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_github_control_plane_writes_are_not_outbound_candidate_communication() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")

    outbound = policy["outbound_communication_policy"]
    assert outbound["requires_approval"] is True
    assert outbound["definition"] == "HUMAN_FACING_COMMUNICATION_TO_PERSON_OR_EXTERNAL_AUDIENCE_OUTSIDE_PROJECT_CONTROL_PLANE"
    assert outbound["project_control_plane_writes_are_outbound_communication"] is False

    autonomous = set(outbound["autonomous_control_plane_examples"])
    for required in {
        "CREATE_GITHUB_PULL_REQUEST",
        "UPDATE_GITHUB_PULL_REQUEST_TITLE_OR_BODY",
        "CREATE_OR_UPDATE_GITHUB_ISSUE",
        "POST_GITHUB_ISSUE_OR_PR_CONTROL_PLANE_COMMENT",
        "PERSIST_CHECKPOINT_OR_VERIFICATION_EVIDENCE",
        "UPDATE_GO_LIVE_CONTROL_BOARD",
    }:
        assert required in autonomous

    routine = set(policy["routine_autonomous_actions"])
    for required in {
        "CREATE_GITHUB_PULL_REQUEST",
        "UPDATE_GITHUB_PULL_REQUEST_TITLE_OR_BODY",
        "CREATE_OR_UPDATE_GITHUB_ISSUE",
        "POST_GITHUB_CONTROL_PLANE_COMMENT",
    }:
        assert required in routine

    forbidden = set(policy["forbidden_unsolicited_interruptions"])
    for required in {
        "PR_CREATION_APPROVAL_REQUEST",
        "PR_BODY_UPDATE_APPROVAL_REQUEST",
        "CONTROL_PLANE_COMMENT_APPROVAL_REQUEST",
    }:
        assert required in forbidden

    control = manifest["control_plane_write_policy"]
    assert control["github_repository_native_writes_require_outbound_communication_approval"] is False
    assert control["pr_creation_requires_approval"] is False
    assert control["pr_title_or_body_update_requires_approval"] is False
    assert control["issue_creation_or_update_requires_approval"] is False
    assert control["issue_or_pr_control_plane_comment_requires_approval"] is False
    assert control["checkpoint_evidence_write_requires_approval"] is False

    assert "These are **internal control-plane mutations**, not outbound candidate communication." in agents
    assert "do not ask the user to approve creating/updating a PR, issue, control-plane comment, checkpoint evidence, merge, or routine reversible deployment to the already-authorized runtime" in handoff
    assert "GitHub Pages is forbidden" in handoff
    assert "authorized runtime is REPLIT" in handoff


def test_reserved_external_communication_boundary_remains_intact() -> None:
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    assert "OUTBOUND_COMMUNICATION_SEND" in policy["approval_boundaries"]
    approval_examples = set(policy["outbound_communication_policy"]["approval_required_examples"])
    for required in {
        "EMAIL_TO_EXTERNAL_PERSON",
        "LINKEDIN_OR_SOCIAL_MESSAGE_TO_EXTERNAL_PERSON",
        "EMPLOYER_APPLICATION_FREE_TEXT_SEND",
        "OTHER_EXTERNAL_CANDIDATE_REPRESENTATION",
    }:
        assert required in approval_examples
