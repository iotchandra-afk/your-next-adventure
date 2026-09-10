from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_delivery_assurance_and_product_invariants_are_bound() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    invariants = json.loads((ROOT / "contracts" / "product_invariants.v1.json").read_text(encoding="utf-8"))
    delivery = (ROOT / "docs" / "DELIVERY_ASSURANCE_CONTRACT.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")

    assert manifest["delivery_assurance_contract"] == "docs/DELIVERY_ASSURANCE_CONTRACT.md"
    assert manifest["product_invariants"] == "contracts/product_invariants.v1.json"
    assert "docs/DELIVERY_ASSURANCE_CONTRACT.md" in manifest["normative_sources"]
    assert "contracts/product_invariants.v1.json" in manifest["normative_sources"]
    assert manifest["acceptance_contracts"]["delivery_assurance"]["required_for_material_changes"] is True
    assert manifest["execution_surface_policy"]["persistent_runner_must_verify_affected_product_invariants"] is True

    assurance = policy["delivery_assurance_policy"]
    assert assurance["enabled_for_material_changes"] is True
    assert assurance["change_impact_map_required"] is True
    assert assurance["positive_assertions_required"] is True
    assert assurance["negative_assertions_required"] is True
    assert assurance["runtime_reconciliation_required_when_applicable"] is True
    assert assurance["deployed_verification_required_for_user_visible_changes"] is True
    assert assurance["semantic_truth"]["null_may_become_substantive_business_outcome"] is False
    assert assurance["semantic_truth"]["ui_may_invent_business_decision_for_display"] is False
    assert assurance["semantic_truth"]["incomplete_processing_may_be_presented_as_completed_zero"] is False
    assert assurance["runtime_backpressure"]["shared_per_model_capacity_required"] is True
    assert assurance["runtime_backpressure"]["stale_running_work_must_be_recoverable"] is True

    ids = {item["id"] for item in invariants["invariants"]}
    assert ids == {f"INV-{index:03d}" for index in range(1, 16)}
    assert all(item["severity"] == "P0" for item in invariants["invariants"])

    assert "The UI MUST NOT infer a substantive business state from absence of data." in delivery
    assert "Provider rate limits are a system constraint" in delivery
    assert "what MUST NOT happen" in delivery
    assert "SYSTEMIC DELIVERY ASSURANCE IS MANDATORY" in handoff


def test_release_completion_requires_invariants_and_live_reconciliation() -> None:
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    policy = json.loads((ROOT / "contracts" / "execution_policy.v1.json").read_text(encoding="utf-8"))
    invariants = json.loads((ROOT / "contracts" / "product_invariants.v1.json").read_text(encoding="utf-8"))

    merge = manifest["merge_deploy_policy"]
    assert merge["affected_product_invariants_must_pass_before_slice_completion"] is True
    assert merge["post_deploy_runtime_reconciliation_required_when_applicable"] is True

    completion = policy["completion_policy"]
    assert completion["done_requires_all_affected_product_invariants_pass"] is True
    assert policy["failure_behavior"]["invariant_failure"] == "REPAIR_OR_SAFE_ROLLBACK_AND_CONTINUE"
    assert policy["failure_behavior"]["post_deploy_reconciliation_failure"] == "REPAIR_OR_SAFE_ROLLBACK_AND_REVERIFY"

    release = invariants["release_rule"]
    assert release["affected_invariants_must_be_identified"] is True
    assert release["negative_assertions_required"] is True
    assert release["runtime_reconciliation_required_when_applicable"] is True
    assert release["deployed_verification_required_for_user_visible_changes"] is True
    assert release["autonomous_repair_or_rollback_before_escalation"] is True
