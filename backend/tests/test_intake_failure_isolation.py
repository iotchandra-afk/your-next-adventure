from yna import intake_batch


class FakeDB:
    def __init__(self):
        self.patches = []
        self.events = []

    def insert(self, table, payload):
        if table == "ingestion_runs":
            return [{"id": "run-1"}]
        if table == "activity_events":
            self.events.append(payload)
        return [{"id": "row-1"}]

    def patch(self, table, filters, payload):
        self.patches.append((table, filters, payload))


class BrokenAdapter:
    def __init__(self, source):
        self.source = source

    def fetch(self):
        raise RuntimeError("synthetic source outage")


def test_one_source_failure_is_captured_not_raised(monkeypatch):
    db = FakeDB()
    monkeypatch.setitem(intake_batch.ADAPTERS, "BROKEN_TEST", BrokenAdapter)
    source = {
        "id": "source-1",
        "source_key": "synthetic-broken",
        "display_name": "Synthetic Broken Source",
        "source_family": "BROKEN_TEST",
        "metadata": {"company_name": "Synthetic"},
    }

    counts = intake_batch.sync_source(db, source)

    assert counts["errors"] == 1
    assert any(table == "source_registry" and payload["health"] == "FAILED" for table, _, payload in db.patches)
    assert any(event["event_type"] == "SOURCE_SYNC_FAILED" for event in db.events)
