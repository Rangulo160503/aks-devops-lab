"""ML pipeline stub (lab-only).

The original project ran SARIMAX / Holt-Winters / MLP / XGBoost in a subprocess
that wrote artifacts to disk. That is incompatible with stateless containers
and blue/green deploys, so the lab edition replaces it with a deterministic,
sub-millisecond function that returns plausible numbers.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import TypedDict

_MODELS = ("SARIMA", "HoltWinters", "MLP", "XGBoost")


class StubResult(TypedDict):
    run_id: str
    best_model: str
    wrmse: float


def _hash_int(seed: str) -> int:
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16)


def run_stub_pipeline(seed: str | None = None) -> StubResult:
    """Return a deterministic fake training result.

    `run_id` is `YYYYMMDD_HHMMSS_<6-char-suffix>` — short, sortable, safe for URLs.
    """
    now = datetime.now(timezone.utc)
    seed_str = seed or now.isoformat()
    h = _hash_int(seed_str)
    suffix = format(h, "x")[:6]
    run_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{suffix}"
    best_model = _MODELS[h % len(_MODELS)]
    wrmse = round(50.0 + (h % 5000) / 100.0, 2)
    return {"run_id": run_id, "best_model": best_model, "wrmse": wrmse}
