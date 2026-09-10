from pathlib import Path

import pytest

from yna.runtime_capacity import CapacityUnavailable, RuntimeCapacity
from yna.triage_parallel import validate_batch_decisions
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
    capacity.throttle("gpt-5.6-sol", 12)
    capacity.release("gpt-5.6-sol", True)
    assert [name for name, _ in db.session.calls] == ["acquire_model_lease", "throttle_model_capacity", "release_model_lease"]
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


def test_all_model_workflows_share_conservative_coarse_group():
    names = ["discovery.yml", "triage.yml", "qualification.yml", "audit.yml", "intelligence.yml", "relevance-eval.yml", "model-smoke.yml"]
    for name in names:
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "group: model-runtime" in text
        assert "cancel-in-progress: false" in text
    assert "TRIAGE_WORKERS: '1'" in (ROOT / ".github" / "workflows" / "triage.yml").read_text(encoding="utf-8")


def test_capacity_migration_is_caller_scoped_and_recovers_stale_runs():
    sql = (ROOT / "db" / "migrations" / "20260910224500_delivery_assurance.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists public.model_capacity" in sql
    assert sql.count("security invoker") == 4
    assert "security definer" not in sql
    assert "status = 'failed'" in sql
    assert "stale_running_recovered" in sql
    assert "from public, anon, authenticated" in sql
    assert "grant execute" in sql and "to service_role" in sql


def test_batch_triage_requires_one_and_only_one_decision_per_claim():
    decisions = [{"opportunity_id": "a"}, {"opportunity_id": "b"}]
    assert validate_batch_decisions({"decisions": decisions}, {"a", "b"}) == decisions
    with pytest.raises(RuntimeError, match="exactly one decision"):
        validate_batch_decisions({"decisions": [{"opportunity_id": "a"}, {"opportunity_id": "a"}]}, {"a", "b"})
    with pytest.raises(RuntimeError, match="exactly one decision"):
        validate_batch_decisions({"decisions": [{"opportunity_id": "a"}, {"opportunity_id": "foreign"}]}, {"a", "b"})
