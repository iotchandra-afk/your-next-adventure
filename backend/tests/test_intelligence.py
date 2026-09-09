from __future__ import annotations

from yna.intelligence import (
    COMPANY_SCHEMA,
    CORE_X_SCHEMA,
    NATIVE_SCHEMA,
    STAKEHOLDER_SCHEMA,
    TWO_NOTCH_SCHEMA,
    stable_hash,
)
from yna.model_router import OpenAIResponses, estimated_tool_cost, web_search_call_count


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


def test_web_provenance_is_deduplicated_and_costed() -> None:
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
                        {"type": "url_citation", "url": "https://example.com/a", "title": "A"},
                        {"type": "url_citation", "url": "https://example.com/c", "title": "C"},
                    ],
                }],
            },
        ]
    }
    sources = OpenAIResponses.web_sources(body)
    assert [s["url"] for s in sources] == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    assert web_search_call_count(body) == 1
    assert estimated_tool_cost(body) == 0.01
