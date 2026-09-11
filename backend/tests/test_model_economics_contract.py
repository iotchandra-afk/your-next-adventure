from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_zero_paid_runtime_is_bound() -> None:
    economics = json.loads((ROOT / "contracts" / "model_economics.v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "SPEC_MANIFEST.json").read_text(encoding="utf-8"))
    handoff = (ROOT / "docs" / "WORK_HANDOFF.md").read_text(encoding="utf-8")

    assert economics["mode"] == "ZERO_PAID_RUNTIME"
    assert economics["paid_runtime_enabled"] is False
    assert economics["provider_credit_is_spend_authority"] is False
    assert economics["scheduled_paid_model_workflows_enabled"] is False
    assert economics["budget_policy"]["validation_cycle_budget_usd"] == 2.0
    assert economics["budget_policy"]["automatic_budget_increase_allowed"] is False
    assert economics["routing_economics"]["deterministic_first"] is True
    assert economics["routing_economics"]["target_max_sol_triage_fraction"] <= 0.10
    assert economics["routing_economics"]["target_max_astra_fraction"] <= 0.02
    assert economics["reuse_policy"]["recompute_on_workflow_rerun_only"] is False
    assert manifest["model_economics_contract"] == "contracts/model_economics.v1.json"
    assert "ZERO-PAID-RUNTIME ECONOMICS IS BINDING" in handoff


def test_paid_model_workflows_are_not_scheduled() -> None:
    for name in ["triage.yml", "audit.yml", "qualification.yml", "intelligence.yml", "discovery.yml"]:
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "schedule:" not in text
        assert "workflow_dispatch:" in text


def test_spend_gate_migration_defaults_closed() -> None:
    sql = (ROOT / "db" / "migrations" / "20260911123000_model_spend_governance.sql").read_text(encoding="utf-8")
    assert "ZERO_PAID_RUNTIME" in sql
    assert "paid_runtime_enabled = false" in sql
    assert "sol_enabled = false" in sql
    assert "astra_enabled = false" in sql
    assert "model_spend_allowed" in sql
    assert "grant execute on function public.model_spend_allowed(text) to service_role" in sql


def test_runtime_capacity_checks_spend_before_model_lease() -> None:
    runtime = (ROOT / "backend" / "yna" / "runtime_capacity.py").read_text(encoding="utf-8")
    spend_check = runtime.index("if not self.spend_allowed(model_id)")
    lease_call = runtime.index('self._rpc("acquire_model_lease"')
    assert spend_check < lease_call
    assert "work retained for retry" in runtime
    assert "without provider spend" in runtime
