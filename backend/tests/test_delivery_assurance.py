from pathlib import Path

import pytest

from yna import triage_parallel
from yna.runtime_capacity import CapacityUnavailable, RuntimeCapacity
from yna.triage_parallel import validate_batch_decisions


ROOT = Path(__file__).resolve().parents[2]


class Response:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class Session:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append((url.rsplit("/", 1)[-1], json))
        return Response(self.bodies.pop(0))


class DB:
    base = "https://example.test/rest/v1"

    def __init__(self, bodies):
        self.session = Session(bodies)


def test_capacity_lease_acquire_throttle_release_positive_path():
    db = DB([True, True, True])
    capacity = RuntimeCapacity(db, wait_seconds=0)
    capacity.acquire("gpt-5.6-sol")
    capacity.throttle("gpt-5.6-sol", 12, "rate_limit_error", "rate_limit_exceeded")
    capacity.release("gpt-5.6-sol", True)
    assert [name for name, _ in db.session.calls] == ["acquire_model_lease", "throttle_model_capacity_v2", "release_model_lease"]
    assert db.session.calls[1][1]["p_error_type"] == "rate_limit_error"
    assert db.session.calls[1][1]["p_error_code"] == "rate_limit_exceeded"
    assert db.session.calls[-1][1]["p_succeeded"] is True


def test_capacity_denial_never_calls_provider_or_claims_success():
    capacity = RuntimeCapacity(DB([False]), wait_seconds=0)
    with pytest.raises(CapacityUnavailable, match="work retained for retry"):
        capacity.acquire("gpt-6-astra")


def test_batch_triage_requires_one_and_only_one_decision_per_claim():
    decisions = validate_batch_decisions({"decisions": [{"opportunity_id": "a"}, {"opportunity_id": "b"}]}, {"a", "b"})
    assert [item["opportunity_id"] for item in decisions] == ["a", "b"]
    with pytest.raises(RuntimeError, match="exactly one decision"):
        validate_batch_decisions({"decisions": [{"opportunity_id": "a"}, {"opportunity_id": "a"}]}, {"a", "b"})
    with pytest.raises(RuntimeError, match="exactly one decision"):
        validate_batch_decisions({"decisions": [{"opportunity_id": "a"}, {"opportunity_id": "outside"}]}, {"a", "b"})


def test_model_workflows_use_per_model_scheduler_lanes_without_push_fanout():
    lanes = {
        "discovery.yml": "sol-runtime",
        "triage.yml": "sol-runtime",
        "relevance-eval.yml": "sol-runtime",
        "qualification.yml": "astra-runtime",
        "audit.yml": "astra-runtime",
        "intelligence.yml": "astra-runtime",
        "model-smoke.yml": "model-runtime-smoke",
    }
    for name, lane in lanes.items():
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert f"group: {lane}" in text
        assert "cancel-in-progress: false" in text
        assert "  push:" not in text
    triage = (ROOT / ".github" / "workflows" / "triage.yml").read_text(encoding="utf-8")
    assert "TRIAGE_WORKERS: '1'" in triage
    assert "TRIAGE_LIMIT: '96'" in triage
    assert "TRIAGE_BATCH_SIZE: '8'" in triage


def test_capacity_migration_is_caller_scoped_and_recovers_stale_runs():
    sql = (ROOT / "db" / "migrations" / "20260910224500_delivery_assurance.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists public.model_capacity" in sql
    assert sql.count("security invoker") == 4
    assert "security definer" not in sql
    assert "status = 'failed'" in sql
    assert "stale_running_recovered" in sql
    assert "from public, anon, authenticated" in sql
    assert "grant execute" in sql and "to service_role" in sql


def test_sustained_throttle_migration_opens_and_resets_circuit_safely():
    sql = (ROOT / "db" / "migrations" / "20260911104755_sustained_model_circuit_breaker.sql").read_text(encoding="utf-8").lower()
    assert "add column if not exists consecutive_throttles" in sql
    assert "create or replace function public.throttle_model_capacity_v2" in sql
    assert "insufficient_quota" in sql and "billing_hard_limit_reached" in sql
    assert "interval '6 hours'" in sql
    assert "consecutive_throttles = case when p_succeeded then 0" in sql
    assert "blocked_until = case when p_succeeded then null" in sql
    assert "security invoker" in sql
    assert "security definer" not in sql
    assert "from public, anon, authenticated" in sql
    assert "to service_role" in sql
    assert "delete from public.model_capacity" not in sql
    assert "drop table" not in sql


def test_triage_stops_claiming_backlog_after_first_failed_batch(monkeypatch):
    class EventDB:
        def __init__(self, *_args):
            self.events = []

        def insert(self, table, payload):
            assert table == "activity_events"
            self.events.append(payload)
            return [payload]

    db = EventDB()
    calls = []
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(triage_parallel, "SupabaseREST", lambda *_args: db)
    monkeypatch.setattr(triage_parallel, "OpenAIResponses", lambda: object())
    monkeypatch.setattr(triage_parallel, "_private_context", lambda _db: ({}, {}, "candidate-v1", "policy-v1"))
    monkeypatch.setattr(triage_parallel, "_eligible_roles", lambda _db, _limit: [{"id": str(i)} for i in range(16)])

    def fail_first(_db, _ai, roles, *_args):
        calls.append([role["id"] for role in roles])
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(triage_parallel, "triage_batch", fail_first)

    assert triage_parallel.run() == 2
    assert calls == [[str(i) for i in range(8)]]
    assert db.events[-1]["details"]["FAILED"] == 8
    assert db.events[-1]["details"]["evaluated"] == 0
    assert db.events[-1]["details"]["unclaimed"] == 8
    assert db.events[-1]["message"] == "Mandate relevance triage evaluated 0 of 8 attempted roles; 8 selected roles remained unclaimed."
