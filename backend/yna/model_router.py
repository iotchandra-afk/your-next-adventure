from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests


MODEL_PRICES_PER_MILLION = {
    "gpt-5.6-sol": {"input": 4.0, "output": 20.0},
    "gpt-6-astra": {"input": 10.0, "output": 50.0},
}
WEB_SEARCH_COST_PER_CALL_USD = 0.01
WEB_SEARCH_MAX_CALLS = 6
MAX_RESPONSE_ATTEMPTS = 6
MAX_RETRY_DELAY_SECONDS = 120.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_INLINE_CITATION = re.compile(r"\s*\(\[[^\]]+\]\(https?://[^)]+\)\)")
_BARE_MARKDOWN_CITATION = re.compile(r"\s*\[[^\]]+\]\(https?://[^)]+\)")
_DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m|h)", re.IGNORECASE)


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
        parsed = clean_structured_result(json.loads(self._extract_output_text(body)))
        return parsed, body, route

    def structured_with_web(
        self,
        capability: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
        max_tool_calls: int = WEB_SEARCH_MAX_CALLS,
    ) -> tuple[dict[str, Any], dict[str, Any], Route, list[dict[str, str]]]:
        """Run a typed capability with current-web grounding and bounded research.

        `max_tool_calls` is a Responses API control, not a prompt request. We retain
        citation-grade sources when output annotations exist; the broader search-result
        universe is only a fallback. This keeps the evidence trail useful rather than
        storing every exploratory result returned to the model.
        """
        route = ROUTES[capability]
        payload = self._base_payload(route, instructions, input_text, schema_name, schema)
        payload.update({
            "tools": [{"type": "web_search", "search_context_size": "medium"}],
            "tool_choice": "required",
            "max_tool_calls": max(1, min(int(max_tool_calls), WEB_SEARCH_MAX_CALLS)),
            "include": ["web_search_call.action.sources"],
        })
        body = self._post(payload, timeout=360)
        parsed = clean_structured_result(json.loads(self._extract_output_text(body)))
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
        """POST without silently downgrading quality; retry only transient failures.

        Large grounded Astra calls can legitimately consume most of a token-rate window.
        OpenAI exposes reset hints on 429 responses, so honor them before retrying the
        exact same request. Non-transient 4xx responses fail immediately.
        """
        last_network_error: Exception | None = None
        for attempt in range(MAX_RESPONSE_ATTEMPTS):
            try:
                response = self.http.post(f"{self.base}/responses", json=payload, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_network_error = exc
                if attempt >= MAX_RESPONSE_ATTEMPTS - 1:
                    raise
                time.sleep(_fallback_retry_delay(attempt))
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RESPONSE_ATTEMPTS - 1:
                time.sleep(_response_retry_delay(response, attempt))
                continue

            response.raise_for_status()
            body = response.json()
            if body.get("status") != "completed":
                raise RuntimeError(f"OpenAI response status: {body.get('status')} / {body.get('error')}")
            return body

        if last_network_error:
            raise last_network_error
        raise RuntimeError("OpenAI response retry budget exhausted")

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
        cited: list[dict[str, str]] = []
        discovered: list[dict[str, str]] = []

        def add(target: list[dict[str, str]], seen: set[str], url: Any, title: Any = None, source_type: Any = None) -> None:
            normalized = normalize_source_url(url)
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            item = {"url": normalized}
            if isinstance(title, str) and title.strip():
                item["title"] = title.strip()
            if isinstance(source_type, str) and source_type.strip():
                item["type"] = source_type.strip()
            target.append(item)

        cited_seen: set[str] = set()
        discovered_seen: set[str] = set()
        for item in body.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content") or []:
                    for annotation in content.get("annotations") or []:
                        if not isinstance(annotation, dict):
                            continue
                        citation = annotation.get("url_citation") if isinstance(annotation.get("url_citation"), dict) else annotation
                        add(cited, cited_seen, citation.get("url"), citation.get("title"), annotation.get("type"))
            if item.get("type") == "web_search_call":
                action = item.get("action") or {}
                for source in action.get("sources") or []:
                    if isinstance(source, dict):
                        add(discovered, discovered_seen, source.get("url"), source.get("title"), source.get("type"))
        return cited if cited else discovered[:20]


def _parse_duration_seconds(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    try:
        return max(0.0, float(text))
    except ValueError:
        pass
    parts = _DURATION_PART.findall(text)
    if not parts:
        return None
    consumed = "".join(f"{amount}{unit}" for amount, unit in parts).lower()
    if consumed != re.sub(r"\s+", "", text):
        return None
    multipliers = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}
    return sum(float(amount) * multipliers[unit.lower()] for amount, unit in parts)


def _fallback_retry_delay(attempt: int) -> float:
    base = min(5.0 * (2 ** attempt), 60.0)
    return min(base + random.uniform(0.0, min(1.0, base * 0.1)), MAX_RETRY_DELAY_SECONDS)


def _response_retry_delay(response: requests.Response, attempt: int) -> float:
    headers = response.headers or {}
    retry_after_ms = _parse_duration_seconds(headers.get("retry-after-ms"))
    if retry_after_ms is not None:
        retry_after_ms /= 1000.0
    retry_after = _parse_duration_seconds(headers.get("retry-after"))
    resets = [
        _parse_duration_seconds(headers.get("x-ratelimit-reset-tokens")),
        _parse_duration_seconds(headers.get("x-ratelimit-reset-requests")),
    ]
    hinted = [v for v in [retry_after_ms, retry_after, *resets] if v is not None]
    if hinted:
        return min(max(hinted) + random.uniform(0.0, 0.25), MAX_RETRY_DELAY_SECONDS)
    return _fallback_retry_delay(attempt)


def normalize_source_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value.startswith(("https://", "http://")):
        return None
    try:
        parts = urlsplit(value)
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not (k == "utm_source" and v == "openai")]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    except ValueError:
        return value


def strip_inline_citations(value: str) -> str:
    cleaned = _INLINE_CITATION.sub("", value)
    cleaned = _BARE_MARKDOWN_CITATION.sub("", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def clean_structured_result(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: clean_structured_result(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_structured_result(item, key) for item in value]
    if isinstance(value, str) and key not in {"url", "urls", "evidence_url", "evidence_urls"}:
        return strip_inline_citations(value)
    return value


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
