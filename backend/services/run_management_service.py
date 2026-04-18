"""
Capa de servicios para el historial de ejecuciones (run management).

No importa Flask: recibe dicts / devuelve dicts. Usa ``backend.models.run_history``
y ``backend.services.pipeline_execution`` para lanzar el pipeline ML.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.models.run_history import (
    HISTORY_MAX,
    _default_run_nombre,
    _load_history_raw,
    _save_history_raw,
    add_to_history,
    history_file_lock,
    load_history,
    save_history,
)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACTS_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "artifacts"))


def is_safe_run_id(rid: Any) -> bool:
    """Valida ``run_id`` para rutas y artefactos en disco."""
    if not rid or not isinstance(rid, str) or len(rid) > 80:
        return False
    for c in rid:
        if not (c.isalnum() or c in "_-"):
            return False
    return True


def _fmt_run_datetime(iso_ts: Optional[str]) -> str:
    if not iso_ts:
        return ""
    return str(iso_ts).replace("T", " ")[:16]


def _dataset_subtitle(row: Dict[str, Any]) -> str:
    mode = (row.get("source_mode") or "").strip() or "auto"
    fn = (row.get("source_file") or "").strip()
    if fn:
        return f"{mode} · {fn}"
    if mode and mode != "auto":
        return mode
    return "Sin archivo de origen"


def list_runs(active_run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista de runs con artefactos en disco, más reciente primero."""
    aid = (active_run_id or "").strip()
    rows = load_history()
    rows.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    out: List[Dict[str, Any]] = []
    for row in rows:
        rid = (row.get("run_id") or "").strip()
        if not rid:
            continue
        if not os.path.isdir(os.path.join(ARTIFACTS_DIR, rid)):
            continue
        out.append(
            {
                "id": rid,
                "run_id": rid,
                "nombre": row.get("nombre")
                or _default_run_nombre(row.get("timestamp") or "", rid),
                "timestamp": row.get("timestamp") or "",
                "fecha": _fmt_run_datetime(row.get("timestamp")),
                "best_model": row.get("best_model"),
                "wrmse": row.get("wrmse"),
                "source_mode": row.get("source_mode") or "auto",
                "source_file": row.get("source_file") or "",
                "dataset": _dataset_subtitle(row),
                "is_active": bool(aid and aid == rid),
            }
        )
    return out


def register_existing_run(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Registra un run ya presente en ``artifacts/``."""
    rid = (data.get("run_id") or data.get("id") or "").strip()
    if not rid:
        latest = _latest_run_from_artifacts_history()
        rid = latest or ""
    if not is_safe_run_id(rid):
        return {"ok": False, "error": "Identificador de ejecución inválido."}, 400

    run_path = os.path.join(ARTIFACTS_DIR, rid)
    if not os.path.isdir(run_path):
        return {"ok": False, "error": "No existe esa carpeta de artefactos."}, 404

    with history_file_lock:
        history = _load_history_raw()
        if any(
            isinstance(r, dict) and str(r.get("run_id")) == rid for r in history
        ):
            return {"ok": False, "error": "La ejecución ya está en el historial."}, 409

        ts = datetime.now().isoformat()
        nombre = (data.get("nombre") or "").strip() or _default_run_nombre(ts, rid)
        best_model, wrmse = _read_meta_best_model(run_path)

        history.append(
            {
                "run_id": rid,
                "nombre": nombre,
                "timestamp": ts,
                "best_model": best_model,
                "wrmse": wrmse,
                "artifacts_dir": rid,
                "source_mode": (data.get("source_mode") or "auto").strip(),
                "source_file": (data.get("source_file") or "").strip(),
            }
        )
        history = history[-HISTORY_MAX:]
        _save_history_raw(history)

    return {"ok": True, "run_id": rid}, 201


def rename_run(run_id: str, nombre: str) -> Tuple[Dict[str, Any], int]:
    if not is_safe_run_id(run_id):
        return {"ok": False, "error": "Identificador inválido."}, 400
    nombre = (nombre or "").strip()
    if not nombre or len(nombre) > 160:
        return {
            "ok": False,
            "error": "El nombre no puede estar vacío ni superar 160 caracteres.",
        }, 400
    with history_file_lock:
        history = _load_history_raw()
        found = False
        for row in history:
            if isinstance(row, dict) and str(row.get("run_id")) == run_id:
                row["nombre"] = nombre
                found = True
                break
        if not found:
            return {"ok": False, "error": "Ejecución no encontrada en el historial."}, 404
        _save_history_raw(history)
    return {"ok": True}, 200


def delete_run(run_id: str) -> Tuple[Dict[str, Any], int]:
    if not is_safe_run_id(run_id):
        return {"ok": False, "error": "Identificador inválido."}, 400

    with history_file_lock:
        history = _load_history_raw()
        n_before = len(history)
        history = [
            r
            for r in history
            if not (isinstance(r, dict) and str(r.get("run_id")) == run_id)
        ]
        if len(history) == n_before:
            return {"ok": False, "error": "Ejecución no encontrada."}, 404
        _save_history_raw(history)

    run_dir = os.path.join(ARTIFACTS_DIR, run_id)
    if os.path.isdir(run_dir):
        try:
            shutil.rmtree(run_dir)
        except OSError as exc:
            return {
                "ok": False,
                "error": f"Se quitó del historial pero no se pudo borrar la carpeta: {exc}",
            }, 500
    return {"ok": True}, 200


def clear_history() -> Tuple[Dict[str, Any], int]:
    """Vacía la tabla ``runs`` (no elimina carpetas en ``artifacts/``)."""
    try:
        save_history([])
    except (OSError, TypeError, ValueError) as exc:
        return {"ok": False, "error": f"No se pudo limpiar el historial: {exc}"}, 500
    return {"ok": True, "message": "Historial limpiado correctamente"}, 200


def execute_pipeline(
    dataset: Optional[str] = None,
    merge_all: bool = False,
    nombre: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """Ejecuta el pipeline ML vía ``backend.services.pipeline_execution``."""
    from backend.services import pipeline_execution as pe  # noqa: WPS433

    if merge_all:
        csv_files = [
            f for f in pe.list_csv_files() if f != pe.MERGED_DATASET_BASENAME
        ]
        if not csv_files:
            return {"ok": False, "error": "No hay CSV en data/."}, 400
        try:
            merged_path, used = pe.merge_csv_datasets(csv_files)
        except (OSError, ValueError) as exc:
            return {"ok": False, "error": f"No se pudo fusionar los CSV: {exc}"}, 500
        if not merged_path:
            return {"ok": False, "error": "No se pudo fusionar los CSV."}, 500
        merged_label = (
            f"{pe.MERGED_DATASET_BASENAME} ({len(used)} CSV: {', '.join(used)})"
        )
        out = pe.execute_ml1_for_csv_dataset(
            pe.MERGED_DATASET_BASENAME,
            history_source_mode="csv",
            history_source_file=merged_label,
        )
    else:
        ds = (dataset or "").strip()
        if not ds:
            return {"ok": False, "error": "Falta 'dataset' o 'merge_all'."}, 400
        basename = pe.csv_basename_on_disk(ds)
        if not basename:
            return {"ok": False, "error": f"Dataset inválido: {ds!r}"}, 400
        out = pe.execute_ml1_for_csv_dataset(basename)

    if not out.get("ok"):
        return {"ok": False, "error": out.get("error") or "Pipeline falló."}, 500

    pe.register_history_from_execute_output(out)

    history = out.get("history") or {}
    if nombre:
        rename_run(history.get("run_id", ""), nombre)

    return {
        "ok": True,
        "run_id": history.get("run_id"),
        "best_model": history.get("best_model"),
        "wrmse": history.get("wrmse"),
        "source_mode": history.get("source_mode"),
        "source_file": history.get("source_file"),
        "pipeline_session_id": history.get("pipeline_session_id"),
    }, 201


def _read_meta_best_model(run_path: str) -> Tuple[str, Optional[float]]:
    """Lee ``meta.json`` + ``errores_modelos.csv`` sin lanzar errores."""
    best_model = "Unknown"
    wrmse: Optional[float] = None
    meta_path = os.path.join(run_path, "meta.json")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            best_model = meta.get("best_model") or best_model
        except (json.JSONDecodeError, OSError):
            pass

    errp = os.path.join(run_path, "errores_modelos.csv")
    if os.path.isfile(errp) and best_model and best_model != "Unknown":
        try:
            import pandas as pd  # lazy para no imponer pandas en servicios sin ML

            edf = pd.read_csv(errp, index_col=0)
            if best_model in edf.index and "WRMSE" in edf.columns:
                wrmse = float(edf.loc[best_model, "WRMSE"])
        except Exception:
            pass
    return best_model, wrmse


def _latest_run_from_artifacts_history() -> Optional[str]:
    """Último ``run_id`` del historial cuya carpeta exista bajo ``artifacts/``."""
    rows = load_history()
    rows.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    for row in rows:
        rid = (row.get("run_id") or "").strip()
        if rid and os.path.isdir(os.path.join(ARTIFACTS_DIR, rid)):
            return rid
    return None
