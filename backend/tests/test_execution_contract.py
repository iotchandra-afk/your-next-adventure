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
