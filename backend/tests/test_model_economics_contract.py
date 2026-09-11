from __future__ import annotations

import json
from pathlib import Path

import pytest

from yna.model_router import OpenAIResponses


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


def test_atomic_reservation_is_global_idempotent_and_fail_safe() -> None:
    sql = (ROOT / "db" / "migrations" / "20260911162243_atomic_model_spend_reservations.sql").read_text(encoding="utf-8").lower()
    assert "select * into v_policy from public.model_spend_policy where id = 1 for update" in sql
    assert "model_runs_paid_identity_once_idx" in sql
    assert "status in ('running','passed')" in sql
    assert "request_key text not null unique" in sql
    assert "v_cycle_committed + p_reserved_usd > v_policy.validation_cycle_budget_usd" in sql
    assert "v_day_committed + p_reserved_usd > v_policy.validation_daily_budget_usd" in sql
    assert "when p_outcome = 'no_charge' then 0" in sql
    assert "when p_outcome = 'uncertain' then reserved_usd" in sql
    assert sql.count("security invoker") == 6
    assert "security definer" not in sql
    assert "from public, anon, authenticated" in sql
    assert "to service_role" in sql


def test_automatic_model_client_fails_closed_without_canonical_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="budget enforcement"):
        OpenAIResponses(api_key="test")


def test_every_paid_path_has_reuse_and_batch_checks_before_claim() -> None:
    files = {name: (ROOT / "backend" / "yna" / name).read_text(encoding="utf-8") for name in [
        "triage.py", "triage_parallel.py", "qualification.py", "audit.py", "intelligence.py", "discovery.py"
    ]}
    assert "reusable_model_run" in files["triage.py"]
    assert files["triage_parallel.py"].index("_passed_run(") < files["triage_parallel.py"].index('db.insert("model_runs"')
    assert "reusable_model_run" in files["qualification.py"]
    assert "reusable_model_run" in files["audit.py"]
    assert "_passed_record" in files["intelligence.py"]
    assert "discovery_pass_reusable" in files["discovery.py"]
    shared_client = (ROOT / "backend" / "yna" / "model_router.py").read_text(encoding="utf-8")
    assert shared_client.count("cached_response(request_hash)") == 2
    assert shared_client.index("cached_response(request_hash)") < shared_client.index("reserve_spend(")


def test_deep_intelligence_is_tier_or_active_pursuit_gated() -> None:
    from yna.intelligence import deep_intelligence_allowed

    assert deep_intelligence_allowed({"screening_stage": "PRIORITIZED", "visibility": "SURFACED", "priority_class": "TIER_1"})
    assert deep_intelligence_allowed({"metadata": {"pursuit_status": "ACTIVE"}})
    assert not deep_intelligence_allowed({"screening_stage": "TRIAGE_RELEVANT", "visibility": "SURFACED"})
    assert not deep_intelligence_allowed({"screening_stage": "PRIORITIZED", "visibility": "SURFACED", "priority_class": "MONITOR"})
