from __future__ import annotations

import requests
import pytest

from yna.intelligence import (
    COMPANY_SCHEMA,
    CORE_X_SCHEMA,
    NATIVE_SCHEMA,
    STAKEHOLDER_SCHEMA,
    TWO_NOTCH_SCHEMA,
    stable_hash,
)
from yna.model_router import (
    OpenAIResponses,
    _parse_duration_seconds,
    _retry_after_ms_seconds,
    clean_structured_result,
    estimated_tool_cost,
    normalize_source_url,
    web_search_call_count,
)


def _assert_strict(schema: dict) -> None:
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


def test_intelligence_output_contracts_are_strict() -> None:
    for schema in [COMPANY_SCHEMA, NATIVE_SCHEMA, STAKEHOLDER_SCHEMA, TWO_NOTCH_SCHEMA, CORE_X_SCHEMA]:
        _assert_strict(schema)


def test_stakeholder_verification_cannot_claim_arbitrary_certainty() -> None:
    item = STAKEHOLDER_SCHEMA["properties"]["stakeholders"]["items"]
    verification = item["properties"]["verification_status"]["enum"]
    assert verification == ["VERIFIED", "HIGH_CONFIDENCE", "PROBABLE", "UNKNOWN"]


def test_semantic_hash_is_order_stable() -> None:
    assert stable_hash({"a": 1, "b": [2, 3]}) == stable_hash({"b": [2, 3], "a": 1})


def test_web_provenance_prefers_citations_and_is_costed() -> None:
    body = {
        "output": [
            {
                "type": "web_search_call",
                "action": {"sources": [
                    {"url": "https://example.com/a", "title": "A", "type": "url"},
                    {"url": "https://example.com/b", "title": "B", "type": "url"},
                ]},
            },
            {
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": "{}",
                    "annotations": [
                        {"type": "url_citation", "url": "https://example.com/a?utm_source=openai", "title": "A"},
                        {"type": "url_citation", "url": "https://example.com/c", "title": "C"},
                    ],
                }],
            },
        ]
    }
    sources = OpenAIResponses.web_sources(body)
    assert [s["url"] for s in sources] == [
        "https://example.com/a",
        "https://example.com/c",
    ]
    assert web_search_call_count(body) == 1
    assert estimated_tool_cost(body) == 0.01


def test_web_provenance_falls_back_to_bounded_discovery_sources() -> None:
    body = {"output": [{"type": "web_search_call", "action": {"sources": [
        {"url": f"https://example.com/{i}", "title": str(i), "type": "url"} for i in range(25)
    ]}}]}
    assert len(OpenAIResponses.web_sources(body)) == 20


def test_inline_model_citations_are_removed_but_evidence_urls_survive() -> None:
    raw = {
        "statement": "Revenue declined. ([Example](https://example.com/a?utm_source=openai))",
        "evidence_urls": ["https://example.com/a?utm_source=openai"],
        "nested": ["Another fact [Example](https://example.com/b)."],
    }
    cleaned = clean_structured_result(raw)
    assert cleaned["statement"] == "Revenue declined."
    assert cleaned["evidence_urls"] == ["https://example.com/a?utm_source=openai"]
    assert cleaned["nested"] == ["Another fact."]
    assert normalize_source_url("https://example.com/a?x=1&utm_source=openai#fragment") == "https://example.com/a?x=1"


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None, headers: dict | None = None):
        self.status_code = status_code
        self._body = body or {}
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} response")

    def json(self) -> dict:
        return self._body


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse]):
        self.responses = list(responses)
        self.calls = 0

    def post(self, *_args, **_kwargs) -> _FakeResponse:
        self.calls += 1
        return self.responses.pop(0)


def _fake_clock(monkeypatch: pytest.MonkeyPatch) -> tuple[list[float], dict[str, float]]:
    sleeps: list[float] = []
    clock = {"now": 100.0}

    def monotonic() -> float:
        return clock["now"]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock["now"] += seconds

    monkeypatch.setattr("yna.model_router.time.monotonic", monotonic)
    monkeypatch.setattr("yna.model_router.time.sleep", sleep)
    monkeypatch.setattr("yna.model_router.random.uniform", lambda _a, _b: 0.0)
    return sleeps, clock


def test_rate_limit_retries_same_request_using_reset_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIResponses(api_key="test")
    fake = _FakeSession([
        _FakeResponse(429, headers={"x-ratelimit-reset-tokens": "0.01s"}),
        _FakeResponse(200, body={"status": "completed"}),
    ])
    client.http = fake  # type: ignore[assignment]
    sleeps, _ = _fake_clock(monkeypatch)

    result = client._post({"model": "gpt-6-astra"})

    assert result["status"] == "completed"
    assert fake.calls == 2
    assert sleeps == [0.01]


def test_non_transient_400_fails_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIResponses(api_key="test")
    fake = _FakeSession([_FakeResponse(400)])
    client.http = fake  # type: ignore[assignment]
    sleeps, _ = _fake_clock(monkeypatch)

    with pytest.raises(requests.HTTPError):
        client._post({"model": "gpt-6-astra"})

    assert fake.calls == 1
    assert sleeps == []


def test_rate_limit_duration_parser_handles_compound_reset_headers() -> None:
    assert _parse_duration_seconds("1m30s") == 90.0
    assert _parse_duration_seconds("250ms") == 0.25
    assert _retry_after_ms_seconds("1000") == 1.0
    assert _retry_after_ms_seconds("250ms") == 0.25


def test_successful_low_remaining_window_paces_next_astra_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIResponses(api_key="test")
    fake = _FakeSession([
        _FakeResponse(
            200,
            body={"status": "completed", "usage": {"input_tokens": 1000, "output_tokens": 100}},
            headers={
                "x-ratelimit-limit-tokens": "100000",
                "x-ratelimit-remaining-tokens": "5000",
                "x-ratelimit-reset-tokens": "2s",
            },
        ),
        _FakeResponse(200, body={"status": "completed"}),
    ])
    client.http = fake  # type: ignore[assignment]
    sleeps, _ = _fake_clock(monkeypatch)

    client._post({"model": "gpt-6-astra"})
    client._post({"model": "gpt-6-astra"})

    assert fake.calls == 2
    assert sleeps == [2.25]


def test_large_grounded_astra_response_arms_fallback_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIResponses(api_key="test")
    fake = _FakeSession([
        _FakeResponse(200, body={"status": "completed", "usage": {"input_tokens": 40000, "output_tokens": 2000}}),
        _FakeResponse(200, body={"status": "completed"}),
    ])
    client.http = fake  # type: ignore[assignment]
    sleeps, _ = _fake_clock(monkeypatch)

    client._post({"model": "gpt-6-astra", "tools": [{"type": "web_search"}]})
    client._post({"model": "gpt-6-astra"})

    assert fake.calls == 2
    assert sleeps == [180.0]
