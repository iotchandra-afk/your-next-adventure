from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .intake import SupabaseREST


class CapacityUnavailable(RuntimeError):
    """Durable capacity is unavailable; callers must retain work for retry."""


class RuntimeCapacity:
    def __init__(self, db: SupabaseREST, wait_seconds: int = 120, ttl_seconds: int = 420):
        self.db = db
        self.holder = str(uuid.uuid4())
        self.wait_seconds = max(0, min(wait_seconds, 300))
        self.ttl_seconds = max(30, min(ttl_seconds, 900))

    @classmethod
    def from_environment(cls) -> RuntimeCapacity | None:
        secret = os.environ.get("SUPABASE_SECRET_KEY")
        if not secret:
            return None
        db = SupabaseREST(os.environ.get("SUPABASE_URL", "https://rpgaxevgnzyasysyvnqz.supabase.co"), secret)
        manager = cls(db, int(os.environ.get("MODEL_LEASE_WAIT_SECONDS", "120")), int(os.environ.get("MODEL_LEASE_TTL_SECONDS", "420")))
        manager.recover_stale_runs()
        return manager

    def _rpc(self, name: str, payload: dict[str, Any]) -> Any:
        response = self.db.session.post(f"{self.db.base}/rpc/{name}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def recover_stale_runs(self) -> int:
        return int(self._rpc("recover_stale_model_runs", {"p_timeout_minutes": 35}) or 0)

    def spend_allowed(self, model_id: str) -> bool:
        """Return canonical spend authority before any paid provider request.

        Provider credit is not spend authority. The database kill switch and
        bounded budget must both permit the model before a lease can be claimed.
        """
        return self._rpc("model_spend_allowed", {"p_model_id": model_id}) is True

    def reserve_spend(
        self,
        model_id: str,
        capability: str,
        reserved_usd: float,
        request_key: str,
        model_run_id: str | None = None,
    ) -> str:
        result = self._rpc("reserve_model_spend", {
            "p_request_key": request_key,
            "p_capability": capability,
            "p_model_id": model_id,
            "p_reserved_usd": round(max(0.0001, reserved_usd), 4),
            "p_model_run_id": model_run_id,
            "p_ttl_seconds": self.ttl_seconds,
        })
        if not isinstance(result, dict) or result.get("allowed") is not True or not result.get("reservation_id"):
            reason = result.get("reason") if isinstance(result, dict) else "RESERVATION_UNAVAILABLE"
            raise CapacityUnavailable(
                f"Paid request blocked before provider call for {model_id}: {reason}; work retained for retry."
            )
        return str(result["reservation_id"])

    def reconcile_spend(self, reservation_id: str, actual_usd: float, outcome: str) -> None:
        reconciled = self._rpc("reconcile_model_spend", {
            "p_reservation_id": reservation_id,
            "p_actual_usd": round(max(0.0, actual_usd), 4),
            "p_outcome": outcome,
        })
        if reconciled is not True:
            raise CapacityUnavailable("Model spend reservation could not be reconciled safely.")

    def cached_response(self, request_hash: str) -> dict[str, Any] | None:
        rows = self.db.select("model_response_cache", {
            "request_hash": f"eq.{request_hash}", "select": "response_body", "limit": "1",
        })
        if not rows:
            return None
        self.db.patch("model_response_cache", {"request_hash": f"eq.{request_hash}"}, {
            "last_reused_at": datetime.now(timezone.utc).isoformat(),
            "reuse_count": self._reuse_count(request_hash) + 1,
        })
        return rows[0].get("response_body")

    def _reuse_count(self, request_hash: str) -> int:
        rows = self.db.select("model_response_cache", {
            "request_hash": f"eq.{request_hash}", "select": "reuse_count", "limit": "1",
        })
        return int(rows[0].get("reuse_count") or 0) if rows else 0

    def store_response(
        self,
        request_hash: str,
        capability: str,
        model_id: str,
        response_body: dict[str, Any],
        actual_cost_usd: float,
        model_run_id: str | None,
    ) -> None:
        self.db.upsert("model_response_cache", {
            "request_hash": request_hash, "capability": capability, "model_id": model_id,
            "model_run_id": model_run_id, "response_body": response_body,
            "actual_cost_usd": round(max(0.0, actual_cost_usd), 4),
        }, "request_hash")

    def acquire(self, model_id: str) -> None:
        if not self.spend_allowed(model_id):
            raise CapacityUnavailable(
                f"Paid model runtime disabled or budget unavailable for {model_id}; work retained for retry without provider spend."
            )

        deadline = time.monotonic() + self.wait_seconds
        while True:
            acquired = self._rpc("acquire_model_lease", {"p_model_id": model_id, "p_holder": self.holder, "p_ttl_seconds": self.ttl_seconds})
            if acquired is True:
                return
            if time.monotonic() >= deadline:
                raise CapacityUnavailable(f"Shared capacity unavailable for {model_id}; work retained for retry.")
            time.sleep(5)

    def throttle(self, model_id: str, delay_seconds: float, error_type: str = "unknown", error_code: str = "unknown") -> None:
        self._rpc("throttle_model_capacity_v2", {
            "p_model_id": model_id,
            "p_holder": self.holder,
            "p_delay_seconds": max(5, min(int(delay_seconds + 1), 900)),
            "p_error_type": error_type[:120],
            "p_error_code": error_code[:120],
        })

    def release(self, model_id: str, succeeded: bool) -> None:
        self._rpc("release_model_lease", {"p_model_id": model_id, "p_holder": self.holder, "p_succeeded": succeeded})
