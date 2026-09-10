import json

from yna.intake import seed_sources


class DB:
    def __init__(self):
        self.upserts = []

    def upsert(self, table, payload, conflict):
        self.upserts.append((table, payload, conflict))
        return [payload]

    def select(self, table, params):
        assert table == "source_registry"
        assert params["enabled"] == "eq.true"
        return [
            {"source_key": "greenhouse:owned", "source_family": "GREENHOUSE", "display_name": "Owned"},
            {"source_key": "market:web-search", "source_family": "DISCOVERY_SIGNAL", "display_name": "Market"},
            {"source_key": "greenhouse:other", "source_family": "GREENHOUSE", "display_name": "Other"},
        ]


def test_direct_intake_returns_only_catalogued_adapter_sources(tmp_path):
    catalog = tmp_path / "sources.json"
    catalog.write_text(json.dumps([{
        "source_key": "greenhouse:owned",
        "source_family": "GREENHOUSE",
        "display_name": "Owned",
        "base_url": "https://example.test/jobs",
        "metadata": {"company_name": "Owned", "board_token": "owned"},
    }]), encoding="utf-8")

    rows = seed_sources(DB(), catalog)

    assert [row["source_key"] for row in rows] == ["greenhouse:owned"]
    assert all(row["source_family"] != "DISCOVERY_SIGNAL" for row in rows)
