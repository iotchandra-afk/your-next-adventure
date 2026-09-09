from __future__ import annotations

from .model_router import OpenAIResponses, ROUTES


def run() -> int:
    client = OpenAIResponses()
    checked: set[str] = set()
    for route in ROUTES.values():
        if route.model_id in checked:
            continue
        model = client.assert_model_available(route.model_id)
        print(f"AVAILABLE {model['id']}")
        checked.add(route.model_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
