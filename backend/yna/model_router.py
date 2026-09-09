from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


MODEL_PRICES_PER_MILLION = {
    "gpt-5.6-sol": {"input": 4.0, "output": 20.0},
    "gpt-6-astra": {"input": 10.0, "output": 50.0},
}
WEB_SEARCH_COST_PER_CALL_USD = 0.01


@dataclass(frozen=True)
class Route:
    model_class: str
    model_id: str
    reasoning_effort: str


ROUTES = {
    "RELEVANCE_TRIAGE": Route("STANDARD_REASONING", "gpt-5.6-sol", "high"),
    "FALSE_NEGATIVE_AUDIT": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "DEEP_QUALIFICATION": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "COMPANY_TRAJECTORY": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "NATIVE_CANDIDATE": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "COMMERCIAL_PRESSURE": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "STAKEHOLDER_CONTEXT": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "ROLE_READINESS": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "CORE_X": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "xhigh"),
    "TWO_NOTCH_UP": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "xhigh"),
    "POSITIONING_LOCK": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "xhigh"),
    "FINAL_RED_TEAM": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "xhigh"),
}


class OpenAIResponses:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self.base = "https://api.openai.com/v1"
        self.http = requests.Session()
        self.http.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def assert_model_available(self, model_id: str) -> dict[str, Any]:
        response = self.http.get(f"{self.base}/models/{model_id}", timeout=30)
        response.raise_for_status()
        body = response.json()
        if body.get("id") != model_id:
            raise RuntimeError(f"Requested {model_id}; API returned {body.get('id')}")
        return body

    def structured(
        self,
        capability: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], Route]:
        route = ROUTES[capability]
        payload = self._base_payload(route, instructions, input_text, schema_name, schema)
        body = self._post(payload)
        parsed = json.loads(self._extract_output_text(body))
        return parsed, body, route

    def structured_with_web(
        self,
        capability: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], Route, list[dict[str, str]]]:
        """Run a typed capability with required current-web grounding.

        The model may make multiple web-search calls. Source URLs/titles are extracted
        from both web-search actions and output citations so downstream conclusions can
        retain provenance without depending on prose citations.
        """
        route = ROUTES[capability]
        payload = self._base_payload(route, instructions, input_text, schema_name, schema)
        payload.update({
            "tools": [{"type": "web_search"}],
            "tool_choice": "required",
            "include": ["web_search_call.action.sources"],
        })
        body = self._post(payload, timeout=360)
        parsed = json.loads(self._extract_output_text(body))
        return parsed, body, route, self.web_sources(body)

    def _base_payload(
        self,
        route: Route,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "model": route.model_id,
            "instructions": instructions,
            "input": input_text,
            "reasoning": {"effort": route.reasoning_effort},
            "text": {
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            "store": False,
        }

    def _post(self, payload: dict[str, Any], timeout: int = 240) -> dict[str, Any]:
        response = self.http.post(f"{self.base}/responses", json=payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "completed":
            raise RuntimeError(f"OpenAI response status: {body.get('status')} / {body.get('error')}")
        return body

    @staticmethod
    def _extract_output_text(body: dict[str, Any]) -> str:
        for item in body.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content["text"]
        raise RuntimeError("No output_text found in completed response")

    @staticmethod
    def web_sources(body: dict[str, Any]) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        seen: set[str] = set()

        def add(url: Any, title: Any = None, source_type: Any = None) -> None:
            if not isinstance(url, str) or not url.startswith(("https://", "http://")) or url in seen:
                return
            seen.add(url)
            item = {"url": url}
            if isinstance(title, str) and title.strip():
                item["title"] = title.strip()
            if isinstance(source_type, str) and source_type.strip():
                item["type"] = source_type.strip()
            sources.append(item)

        for item in body.get("output", []):
            if item.get("type") == "web_search_call":
                action = item.get("action") or {}
                for source in action.get("sources") or []:
                    if isinstance(source, dict):
                        add(source.get("url"), source.get("title"), source.get("type"))
            if item.get("type") == "message":
                for content in item.get("content") or []:
                    for annotation in content.get("annotations") or []:
                        if not isinstance(annotation, dict):
                            continue
                        citation = annotation.get("url_citation") if isinstance(annotation.get("url_citation"), dict) else annotation
                        add(citation.get("url"), citation.get("title"), annotation.get("type"))
        return sources


def estimated_cost(model_id: str, usage: dict[str, Any] | None) -> float:
    usage = usage or {}
    prices = MODEL_PRICES_PER_MILLION.get(model_id)
    if not prices:
        return 0.0
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return round(input_tokens / 1_000_000 * prices["input"] + output_tokens / 1_000_000 * prices["output"], 6)


def web_search_call_count(body: dict[str, Any]) -> int:
    return sum(1 for item in body.get("output", []) if item.get("type") == "web_search_call")


def estimated_tool_cost(body: dict[str, Any]) -> float:
    return round(web_search_call_count(body) * WEB_SEARCH_COST_PER_CALL_USD, 6)


def estimated_total_cost(model_id: str, body: dict[str, Any]) -> float:
    return round(estimated_cost(model_id, body.get("usage") or {}) + estimated_tool_cost(body), 6)
