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

from .runtime_capacity import RuntimeCapacity


MODEL_PRICES_PER_MILLION = {
    "gpt-5.6-sol": {"input": 4.0, "output": 20.0},
    "gpt-6-astra": {"input": 10.0, "output": 50.0},
}
WEB_SEARCH_COST_PER_CALL_USD = 0.01
WEB_SEARCH_MAX_CALLS = 5
MAX_RESPONSE_ATTEMPTS = 4
MAX_RETRY_DELAY_SECONDS = 300.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_CAPACITY_CODES = {"insufficient_quota", "billing_hard_limit_reached"}
ASTRA_WEB_FALLBACK_COOLDOWN_SECONDS = 180.0
_INLINE_CITATION = re.compile(r"\s*\(\[[^\]]+\]\(https?://[^)]+\)\)")
_BARE_MARKDOWN_CITATION = re.compile(r"\s*\[[^\]]+\]\(https?://[^)]+\)")
_DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m|h)", re.IGNORECASE)
_CAPACITY_AUTO = object()


class ProviderBackpressure(RuntimeError):
    """A classified provider-capacity failure safe to persist as telemetry."""


@dataclass(frozen=True)
class Route:
    model_class: str
    model_id: str
    reasoning_effort: str


ROUTES = {
    "MARKET_DISCOVERY": Route("STANDARD_REASONING", "gpt-5.6-sol", "high"),
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
    def __init__(self, api_key: str | None = None, capacity: RuntimeCapacity | None | object = _CAPACITY_AUTO):
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
        self._not_before_by_model: dict[str, float] = {}
        self.capacity = RuntimeCapacity.from_environment() if capacity is _CAPACITY_AUTO else capacity

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
            "tools": [{"type": "web_search", "search_context_size": "low"}],
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

        High-cost grounded Astra calls can consume most of a token-rate window even
        though the HTTP request itself completes normally. The client therefore honors
        provider reset headers across sequential calls and uses a conservative fallback
        cooldown after unusually large grounded Astra responses when those headers are
        absent. A 429 retries the exact same request/model; no quality downgrade occurs.
        """
        model_id = str(payload.get("model") or "")
        if self.capacity:
            self.capacity.acquire(model_id)
        succeeded = False
        last_network_error: Exception | None = None
        try:
            for attempt in range(MAX_RESPONSE_ATTEMPTS):
                self._wait_for_model(model_id)
                if self.capacity:
                    # Renew before every potentially long provider call. A request timeout
                    # is shorter than the lease, preventing concurrent budget ownership.
                    self.capacity.acquire(model_id)
                try:
                    response = self.http.post(f"{self.base}/responses", json=payload, timeout=timeout)
                except (requests.Timeout, requests.ConnectionError) as exc:
                    last_network_error = exc
                    if attempt >= MAX_RESPONSE_ATTEMPTS - 1:
                        raise
                    self._arm_model_delay(model_id, _fallback_retry_delay(attempt))
                    continue

                if response.status_code == 429:
                    delay = _response_retry_delay(response, attempt)
                    error = _provider_error(response, model_id, delay)
                    if self.capacity:
                        self.capacity.throttle(model_id, delay, error["type"], error["code"])
                    if error["code"] in NON_RETRYABLE_CAPACITY_CODES or attempt >= MAX_RESPONSE_ATTEMPTS - 1:
                        raise ProviderBackpressure(_provider_error_message(error))
                    self._arm_model_delay(model_id, delay)
                    continue

                if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RESPONSE_ATTEMPTS - 1:
                    self._arm_model_delay(model_id, _response_retry_delay(response, attempt))
                    continue

                response.raise_for_status()
                body = response.json()
                if body.get("status") != "completed":
                    raise RuntimeError(f"OpenAI response status: {body.get('status')} / {body.get('error')}")
                self._observe_success_rate_window(model_id, payload, response, body)
                succeeded = True
                return body

            if last_network_error:
                raise last_network_error
            raise RuntimeError("OpenAI response retry budget exhausted")
        finally:
            if self.capacity:
                try:
                    self.capacity.release(model_id, succeeded)
                except requests.RequestException:
                    # A lost release cannot corrupt business state; the durable TTL
                    # expires the lease and the next worker performs stale recovery.
                    pass

    def _arm_model_delay(self, model_id: str, seconds: float) -> None:
        if not model_id or seconds <= 0:
            return
        target = time.monotonic() + min(float(seconds), MAX_RETRY_DELAY_SECONDS)
        self._not_before_by_model[model_id] = max(self._not_before_by_model.get(model_id, 0.0), target)

    def _wait_for_model(self, model_id: str) -> None:
        if not model_id:
            return
        wait = self._not_before_by_model.get(model_id, 0.0) - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def _observe_success_rate_window(
        self,
        model_id: str,
        payload: dict[str, Any],
        response: requests.Response,
        body: dict[str, Any],
    ) -> None:
        headers = response.headers or {}
        remaining = _parse_int_header(headers.get("x-ratelimit-remaining-tokens"))
        limit = _parse_int_header(headers.get("x-ratelimit-limit-tokens"))
        reset = _parse_duration_seconds(headers.get("x-ratelimit-reset-tokens"))
        if remaining is not None and reset is not None:
            exhausted_fraction = limit is not None and limit > 0 and remaining / limit <= 0.20
            if remaining <= 10_000 or exhausted_fraction:
                self._arm_model_delay(model_id, reset + 0.25)
                return

        usage = body.get("usage") or {}
        total_tokens = int(usage.get("total_tokens") or 0)
        if not total_tokens:
            total_tokens = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
        if (
            model_id == "gpt-6-astra"
            and payload.get("tools")
            and total_tokens >= 30_000
            and reset is None
        ):
            self._arm_model_delay(model_id, ASTRA_WEB_FALLBACK_COOLDOWN_SECONDS)

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


def _parse_int_header(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


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


def _retry_after_ms_seconds(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    try:
        return max(0.0, float(text) / 1000.0)
    except ValueError:
        return _parse_duration_seconds(text)


def _fallback_retry_delay(attempt: int) -> float:
    base = min(5.0 * (2 ** attempt), 120.0)
    return min(base + random.uniform(0.0, min(1.0, base * 0.1)), MAX_RETRY_DELAY_SECONDS)


def _response_retry_delay(response: requests.Response, attempt: int) -> float:
    headers = response.headers or {}
    retry_after_ms = _retry_after_ms_seconds(headers.get("retry-after-ms"))
    retry_after = _parse_duration_seconds(headers.get("retry-after"))
    resets = [
        _parse_duration_seconds(headers.get("x-ratelimit-reset-tokens")),
        _parse_duration_seconds(headers.get("x-ratelimit-reset-requests")),
    ]
    hinted = [v for v in [retry_after_ms, retry_after, *resets] if v is not None]
    if hinted:
        return min(max(hinted) + random.uniform(0.0, 0.25), MAX_RETRY_DELAY_SECONDS)
    return _fallback_retry_delay(attempt)


def _provider_error(response: requests.Response, model_id: str, retry_delay: float) -> dict[str, Any]:
    try:
        body = response.json()
    except (ValueError, TypeError):
        body = {}
    raw = body.get("error") if isinstance(body, dict) else {}
    raw = raw if isinstance(raw, dict) else {}
    return {
        "status": response.status_code,
        "model": model_id,
        "type": str(raw.get("type") or "unknown")[:120],
        "code": str(raw.get("code") or "unknown")[:120],
        "retry_after_seconds": round(retry_delay, 3),
    }


def _provider_error_message(error: dict[str, Any]) -> str:
    return (
        "Provider backpressure: "
        f"status={error['status']} model={error['model']} type={error['type']} "
        f"code={error['code']} retry_after_seconds={error['retry_after_seconds']}"
    )


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
