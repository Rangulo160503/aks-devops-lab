"""API REST v1 de runs (``/api/v1/runs``), delegada a ``backend.services.run_management_service``."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.services import run_management_service

run_bp = Blueprint("runs_v1", __name__, url_prefix="/api/v1/runs")


@run_bp.get("")
def list_runs():
    active = (request.args.get("active") or "").strip()
    if active and not run_management_service.is_safe_run_id(active):
        active = ""
    return jsonify({"ok": True, "runs": run_management_service.list_runs(active)})


@run_bp.post("")
def create_run():
    """Dispara el pipeline ML.

    Body (JSON):
        {"merge_all": true}
        ó
        {"dataset": "archivo.csv"}
        (opcional: {"nombre": "Mi ejecución"})
    """
    body = request.get_json(silent=True) or {}
    payload, status = run_management_service.execute_pipeline(
        dataset=body.get("dataset"),
        merge_all=bool(body.get("merge_all", False)),
        nombre=body.get("nombre"),
    )
    return jsonify(payload), status


@run_bp.post("/register")
def register_run():
    """Registra un run ya existente en ``artifacts/``."""
    body = request.get_json(silent=True) or {}
    payload, status = run_management_service.register_existing_run(body)
    return jsonify(payload), status


@run_bp.patch("/<run_id>")
def rename_run(run_id: str):
    body = request.get_json(silent=True) or {}
    payload, status = run_management_service.rename_run(run_id, body.get("nombre", ""))
    return jsonify(payload), status


@run_bp.delete("/<run_id>")
def delete_run(run_id: str):
    payload, status = run_management_service.delete_run(run_id)
    return jsonify(payload), status


@run_bp.delete("")
def clear_history():
    payload, status = run_management_service.clear_history()
    return jsonify(payload), status
