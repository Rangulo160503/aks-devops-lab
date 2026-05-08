"""`/api/v1/runs` — minimal CRUD over the `runs` table."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import delete, select

from ..db import session_scope
from ..models import Run
from ..pipeline import run_stub_pipeline
from ..schemas import CreateRunRequest, ValidationError

runs_bp = Blueprint("runs", __name__, url_prefix="/api/v1/runs")

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _is_safe_run_id(value: str) -> bool:
    return bool(_RUN_ID_RE.match(value))


def _default_nombre(run_id: str) -> str:
    return f"Ejecucion - {run_id[:8]}" if run_id else "Ejecucion"


@runs_bp.get("")
def list_runs():
    with session_scope() as s:
        rows = s.scalars(select(Run).order_by(Run.created_at.desc())).all()
        return jsonify({"ok": True, "runs": [r.to_dict() for r in rows]})


@runs_bp.post("")
def create_run():
    try:
        body = CreateRunRequest.from_json(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    result = run_stub_pipeline()
    rid = result["run_id"]
    nombre = body.nombre.strip() or _default_nombre(rid)

    with session_scope() as s:
        run = Run(
            run_id=rid,
            nombre=nombre,
            best_model=result["best_model"],
            wrmse=result["wrmse"],
            source_mode=body.source_mode,
            source_file=body.source_file,
            created_at=datetime.now(timezone.utc),
        )
        s.add(run)
        s.flush()
        return jsonify({"ok": True, "run": run.to_dict()}), 201


@runs_bp.get("/<run_id>")
def get_run(run_id: str):
    if not _is_safe_run_id(run_id):
        return jsonify({"ok": False, "error": "invalid run_id"}), 400
    with session_scope() as s:
        run = s.get(Run, run_id)
        if run is None:
            return jsonify({"ok": False, "error": "not found"}), 404
        return jsonify({"ok": True, "run": run.to_dict()})


@runs_bp.delete("/<run_id>")
def remove_run(run_id: str):
    if not _is_safe_run_id(run_id):
        return jsonify({"ok": False, "error": "invalid run_id"}), 400
    with session_scope() as s:
        result = s.execute(delete(Run).where(Run.run_id == run_id))
        if result.rowcount == 0:
            return jsonify({"ok": False, "error": "not found"}), 404
        return jsonify({"ok": True, "deleted": run_id})
