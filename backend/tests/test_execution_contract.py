from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_execution_contract_is_bound_and_machine_readable() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert manifest["implementation_authorized"] is True
    assert manifest["execution_contract"] == "AGENTS.md"
    assert manifest["machine_execution_policy"] == "contracts/execution_policy.v1.json"
    assert manifest["persistent_execution_handoff"] == "docs/WORK_HANDOFF.md"
    assert manifest["default_execution_action"] == "CONTINUE"
    assert manifest["communication_default"] == "SILENT_UNLESS_STOP_CONDITION"
    assert manifest["checkpoint_requires_user_acknowledgement"] is False

    expected_stops = {
        "BLOCKED",
        "APPROVAL_REQUIRED",
        "HUMAN_ACTION_REQUIRED",
        "DONE",
    }
    assert set(policy["stop_conditions"]) == expected_stops
    assert set(manifest["allowed_unsolicited_stop_conditions"]) == expected_stops
    assert policy["default_action"] == "CONTINUE"
    assert policy["communication_default"] == "SILENT"
    assert policy["checkpoint_behavior"]["requires_user_acknowledgement"] is False
    assert policy["checkpoint_behavior"]["emit_status_message"] is False
    assert policy["failure_behavior"]["recoverable_failure"] == "REMEDIATE_AND_CONTINUE"
    assert policy["failure_behavior"]["escalate_only_if_stop_condition"] is True

    forbidden = set(policy["forbidden_unsolicited_interruptions"])
    for required in {
        "PROGRESS_UPDATE",
        "CHECKPOINT_PASS",
        "SUCCESSFUL_TEST",
        "SUCCESSFUL_DEPLOYMENT",
        "REQUEST_TO_PROCEED",
        "REQUEST_TO_RECONFIRM_EXISTING_AUTHORITY",
    }:
        assert required in forbidden

    assert "Silence is the default during autonomous execution." in agents
    assert "Checkpoint evidence MUST be persisted" in agents
    assert "No routine `STATUS`, `PROGRESS`, `CHECKPOINT PASS`, or `CONTINUING` messages are permitted." in agents


def test_persistent_execution_surface_truth_is_explicit() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    execution_model = (ROOT / "docs" / "EXECUTION_MODEL.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")

    surface = policy["execution_surface"]
    assert surface["ordinary_chat_role"] == "STEERING_AND_EXCEPTIONS_ONLY"
    assert surface["persistent_execution_required_for_cross_response_continuation"] is True
    assert surface["github_is_control_plane_not_execution_plane"] is True
    assert surface["repository_policy_does_not_create_chat_persistence"] is True
    assert surface["forbid_claiming_background_continuation_without_active_runner"] is True

    manifest_surface = manifest["execution_surface_policy"]
    assert manifest_surface["github_role"] == "CONTROL_PLANE_AND_SYSTEM_OF_RECORD"
    assert manifest_surface["ordinary_chat_role"] == "STEERING_AND_EXCEPTIONS_ONLY"
    assert manifest_surface["persistent_runner_required_for_cross_response_continuation"] is True
    assert manifest_surface["repository_instructions_create_persistence"] is False
    assert manifest_surface["preferred_persistent_surface"] == "CHATGPT_WORK"

    assert "This contract governs agent behavior **while an execution surface is active**." in agents
    assert "GitHub is the durable **control plane and system of record**; a persistent runner is the **execution plane**." in agents
    assert "A durable control plane does not create a persistent execution plane." in execution_model
    assert "No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active." in handoff


def test_reserved_approval_boundaries_do_not_drift() -> None:
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    assert set(policy["approval_boundaries"]) == {
        "NEW_MATERIAL_PAID_SERVICE",
        "DESTRUCTIVE_PRODUCTION_OPERATION",
        "SECURITY_BOUNDARY_CHANGE",
        "OUTBOUND_COMMUNICATION_SEND",
        "FINAL_JOB_APPLICATION_SUBMISSION",
    }


def test_authority_headers_do_not_drift() -> None:
    spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "ARCHITECTURE_REFERENCE.md").read_text(encoding="utf-8")

    assert "**Status:** ACTIVE BUILD" in spec
    assert "**Implementation authorization:** GRANTED" in spec
    assert "NOT GRANTED" not in spec
    assert "without authorizing implementation" not in architecture
