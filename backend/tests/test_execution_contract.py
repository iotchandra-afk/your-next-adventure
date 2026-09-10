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
        "HUMAN ACTION REQUIRED",
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
        "PR_READY_FOR_MERGE",
        "ROUTINE_MERGE_APPROVAL_REQUEST",
        "ROUTINE_DEPLOYMENT_APPROVAL_REQUEST",
        "REQUEST_TO_PROCEED",
        "REQUEST_TO_RECONFIRM_EXISTING_AUTHORITY",
    }:
        assert required in forbidden

    assert "Silence is the default during autonomous execution." in agents
    assert "Checkpoint evidence MUST be persisted" in agents
    assert "No routine `STATUS`, `PROGRESS`, `CHECKPOINT PASS`, `PR READY`, `DEPLOYMENT READY`, or `CONTINUING` messages are permitted." in agents


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
    assert surface["persistent_runner_must_continue_across_internal_engineering_units"] is True

    manifest_surface = manifest["execution_surface_policy"]
    assert manifest_surface["github_role"] == "CONTROL_PLANE_AND_SYSTEM_OF_RECORD"
    assert manifest_surface["ordinary_chat_role"] == "STEERING_AND_EXCEPTIONS_ONLY"
    assert manifest_surface["persistent_runner_required_for_cross_response_continuation"] is True
    assert manifest_surface["repository_instructions_create_persistence"] is False
    assert manifest_surface["preferred_persistent_surface"] == "CHATGPT_WORK"
    assert manifest_surface["persistent_runner_must_continue_across_internal_engineering_units"] is True

    assert "This contract governs agent behavior **while an execution surface is active**." in agents
    assert "GitHub is the durable **control plane and system of record**; a persistent runner is the **execution plane**." in agents
    assert "A durable control plane does not create a persistent execution plane." in execution_model
    assert "No agent may claim that work will continue after a synchronous chat response unless a persistent execution runner is actually active." in handoff


def test_routine_merge_and_deploy_do_not_require_user_approval() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    execution_model = (ROOT / "docs" / "EXECUTION_MODEL.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")

    merge = policy["merge_deploy_policy"]
    assert merge["production_label_alone_requires_approval"] is False
    assert merge["routine_reversible_merge_to_main_requires_approval"] is False
    assert merge["routine_reversible_deployment_requires_approval"] is False
    assert merge["github_pages_deployment_requires_approval"] is False
    assert merge["additive_non_destructive_migration_requires_approval"] is False
    assert merge["pr_ready_is_completion"] is False
    assert merge["ci_passed_is_completion"] is False
    assert merge["deployment_ready_is_completion"] is False

    manifest_merge = manifest["merge_deploy_policy"]
    assert manifest_merge["routine_reversible_merge_to_main_requires_approval"] is False
    assert manifest_merge["routine_reversible_production_deployment_requires_approval"] is False
    assert manifest_merge["github_pages_deployment_requires_approval"] is False
    assert manifest_merge["production_label_alone_is_approval_boundary"] is False
    assert manifest_merge["destructive_or_materially_irreversible_production_operation_requires_approval"] is True
    assert manifest_merge["pr_ready_is_done"] is False
    assert manifest_merge["ci_passed_is_done"] is False
    assert manifest_merge["deployment_ready_is_done"] is False

    routine = set(policy["routine_autonomous_actions"])
    for required in {
        "UPDATE_OR_REBASE_IMPLEMENTATION_BRANCH",
        "MERGE_IMPLEMENTATION_PR_TO_MAIN",
        "SQUASH_MERGE_IMPLEMENTATION_PR_TO_MAIN",
        "GITHUB_PAGES_DEPLOYMENT_FROM_MAIN",
        "VERIFY_ROUTINE_DEPLOYMENT",
    }:
        assert required in routine

    assert "**Production is not synonymous with destructive.**" in agents
    assert "A PR is an internal unit of work, not the project deliverable." in agents
    assert "The word **production** does not automatically imply an approval boundary." in execution_model
    assert 'production is not by itself an approval boundary' in handoff


def test_reserved_approval_boundaries_do_not_drift() -> None:
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    assert set(policy["approval_boundaries"]) == {
        "NEW_MATERIAL_PAID_SERVICE",
        "DESTRUCTIVE_PRODUCTION_OPERATION",
        "SECURITY_BOUNDARY_CHANGE",
        "OUTBOUND_COMMUNICATION_SEND",
        "FINAL_JOB_APPLICATION_SUBMISSION",
    }


def test_completion_is_task_level_not_pr_level() -> None:
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    completion = policy["completion_policy"]
    assert completion["code_written_is_done"] is False
    assert completion["pr_opened_is_done"] is False
    assert completion["pr_ready_is_done"] is False
    assert completion["ci_passed_is_done"] is False
    assert completion["deployment_ready_is_done"] is False
    assert completion["checkpoint_reached_is_done"] is False
    assert completion["done_requires_active_task_acceptance_criteria_satisfied"] is True


def test_authority_headers_do_not_drift() -> None:
    spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "ARCHITECTURE_REFERENCE.md").read_text(encoding="utf-8")

    assert "**Status:** ACTIVE BUILD" in spec
    assert "**Implementation authorization:** GRANTED" in spec
    assert "NOT GRANTED" not in spec
    assert "without authorizing implementation" not in architecture


def test_persistent_runs_reiterate_without_weakening_product_objective() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")
    iteration = (ROOT / "docs" / "ITERATION_CONTRACT.md").read_text(encoding="utf-8")

    assert manifest["iteration_contract"] == "docs/ITERATION_CONTRACT.md"
    assert "docs/ITERATION_CONTRACT.md" in manifest["normative_sources"]
    assert manifest["internal_post_slice_action"] == "REITERATE"
    assert manifest["execution_surface_policy"]["persistent_runner_must_reiterate_across_material_slices"] is True
    assert manifest["acceptance_contracts"]["potency_preserving_iteration"]["required_for_persistent_build_runs"] is True

    reiteration = policy["iteration_policy"]
    assert reiteration["enabled_for_persistent_runs"] is True
    assert reiteration["after_material_slice"] == "REITERATE"
    assert reiteration["reiterate_is_user_facing_message"] is False
    assert reiteration["scope_for_next_iteration"] == "ENTIRE_AUTHORIZED_PRODUCT_SCOPE"
    assert reiteration["prior_passes_are_falsifiable"] is True
    assert reiteration["whole_system_red_team_required"] is True
    assert reiteration["forbid_weakening_requirements_to_reach_done"] is True
    assert reiteration["forbid_proxy_metric_substitution_for_required_outcome"] is True
    assert reiteration["forbid_local_optimization_at_product_objective_expense"] is True

    assert "POTENCY-PRESERVING REITERATION IS MANDATORY" in handoff
    assert "completing one defect, PR, deployment, or P0 is not the end of the run" in handoff
    assert "The runner MUST NOT make progress look better by weakening the product." in iteration
    assert "All prior PASS decisions are falsifiable." in iteration
    assert "TASK INCOMPLETE" in iteration and "=> REITERATE" in iteration
