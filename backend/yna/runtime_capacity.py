from __future__ import annotations

import os
import time
import uuid
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

    def acquire(self, model_id: str) -> None:
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
