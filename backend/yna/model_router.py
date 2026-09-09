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


@dataclass(frozen=True)
class Route:
    model_class: str
    model_id: str
    reasoning_effort: str


ROUTES = {
    "RELEVANCE_TRIAGE": Route("STANDARD_REASONING", "gpt-5.6-sol", "high"),
    "FALSE_NEGATIVE_AUDIT": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
    "DEEP_QUALIFICATION": Route("HIGH_CONSEQUENCE_REASONING", "gpt-6-astra", "high"),
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
        payload = {
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
        response = self.http.post(f"{self.base}/responses", json=payload, timeout=240)
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "completed":
            raise RuntimeError(f"OpenAI response status: {body.get('status')} / {body.get('error')}")
        text = self._extract_output_text(body)
        parsed = json.loads(text)
        return parsed, body, route

    @staticmethod
    def _extract_output_text(body: dict[str, Any]) -> str:
        for item in body.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content["text"]
        raise RuntimeError("No output_text found in completed response")


def estimated_cost(model_id: str, usage: dict[str, Any] | None) -> float:
    usage = usage or {}
    prices = MODEL_PRICES_PER_MILLION.get(model_id)
    if not prices:
        return 0.0
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return round(input_tokens / 1_000_000 * prices["input"] + output_tokens / 1_000_000 * prices["output"], 6)
