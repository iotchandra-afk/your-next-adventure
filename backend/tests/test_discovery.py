from yna.discovery import clean_roles, prepare_records, role_key


def role(**overrides):
    value = {
        "company": "Example Holdings", "title": "Vice President, Enterprise Transformation",
        "location": "United States", "discovery_url": "https://jobs.example.net/listing/42",
        "official_url": "https://careers.example.com/jobs/42", "requisition_id": "42",
        "posted_at": "2026-09-09T12:00:00Z", "source_family": "JOB_BOARD",
        "source_name": "Example Jobs", "snippet": "Lead enterprise AI operating transformation.", "confidence": 0.92,
    }
    value.update(overrides)
    return value


def test_discovery_requires_real_http_source_and_deduplicates():
    valid = role()
    assert clean_roles([valid, valid, role(discovery_url="javascript:alert(1)")], 10) == [valid]


def test_discovery_preserves_official_and_discovery_urls():
    records = prepare_records([role()], "2026-09-10T00:00:00Z")
    assert len(records) == 2
    assert {item["raw_payload"]["url_kind"] for item in records} == {"official", "discovery"}
    assert next(item for item in records if item["is_primary"])["url"] == "https://careers.example.com/jobs/42"
    assert all(item["screening_stage"] == "ELIGIBLE" and item["visibility"] == "HIDDEN" for item in records)


def test_probe_key_is_stable_but_source_specific():
    assert role_key(role()) == role_key(role(company=" example holdings "))
    assert role_key(role()) != role_key(role(discovery_url="https://jobs.example.net/listing/43"))
