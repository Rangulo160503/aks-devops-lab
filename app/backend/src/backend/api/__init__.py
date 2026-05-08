"""HTTP API blueprints."""
from __future__ import annotations

from .health import health_bp
from .runs import runs_bp

__all__ = ["health_bp", "runs_bp"]
