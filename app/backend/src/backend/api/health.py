"""Liveness and readiness probes.

- `/healthz` is **cheap** and never touches the database. Kubernetes uses it as
  a livenessProbe to decide whether to restart the pod.
- `/readyz` performs a real `SELECT 1` against the database. Kubernetes uses it
  as a readinessProbe to decide whether to send traffic to the pod.

Keeping them split is deliberate: a flapping DB should drain a pod from the
Service, not bounce it.
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from .. import __version__
from ..db import ping

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
def healthz():
    return jsonify(
        {
            "status": "ok",
            "version": __version__,
            "color": current_app.config["APP_COLOR"],
        }
    )


@health_bp.get("/readyz")
def readyz():
    try:
        ping()
    except Exception as exc:
        return (
            jsonify({"status": "error", "component": "database", "detail": str(exc)}),
            503,
        )
    return jsonify({"status": "ready"})
