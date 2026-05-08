"""
Historial de ejecuciones ML: persistencia en SQLite (tabla ``runs`` en ``data.db``).

Reemplaza ``web/run_history.json`` (migración histórica) manteniendo la API usada por ``backend/main.py``:
``load_history``, ``save_history``, ``add_to_history``, ``normalize_history_row``,
``run_id_in_history``, ``_load_history_raw``, ``_save_history_raw``.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from backend.infrastructure.db import get_connection

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

HISTORY_MAX = 25

history_file_lock = threading.Lock()

_history_nombre_backfill_done = False

_schema_ready = False


def _default_run_nombre(iso_ts: str, run_id: str) -> str:
    """Misma lógica que ``_default_run_nombre`` en el backend (``backend/main``)."""
    d = (iso_ts or "")[:10]
    if (not d) and run_id and len(str(run_id)) >= 8 and str(run_id)[:8].isdigit():
        rid = str(run_id)
        d = f"{rid[:4]}-{rid[4:6]}-{rid[6:8]}"
    if not d:
        d = datetime.now().strftime("%Y-%m-%d")
    return f"Ejecución - {d}"


def _ensure_runs_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            best_model TEXT,
            wrmse REAL,
            artifacts_dir TEXT NOT NULL,
            source_mode TEXT NOT NULL,
            source_file TEXT NOT NULL DEFAULT '',
            pipeline_session_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(timestamp);
        """
    )


def _row_from_db(row: sqlite3.Row) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "run_id": row["run_id"] or "",
        "nombre": row["nombre"] or "",
        "timestamp": row["timestamp"] or "",
        "best_model": row["best_model"],
        "wrmse": row["wrmse"],
        "artifacts_dir": row["artifacts_dir"] or "",
        "source_mode": row["source_mode"] or "auto",
        "source_file": row["source_file"] if row["source_file"] is not None else "",
    }
    ps = row["pipeline_session_id"]
    if ps:
        d["pipeline_session_id"] = str(ps).strip()
    return d


def _insert_run(conn: sqlite3.Connection, item: Dict[str, Any]) -> None:
    rid = (item.get("run_id") or "").strip()
    if not rid:
        return
    ts = item.get("timestamp") or datetime.now().isoformat()
    nombre = (item.get("nombre") or "").strip() or _default_run_nombre(ts, rid)
    ps = item.get("pipeline_session_id")
    conn.execute(
        """
        INSERT OR REPLACE INTO runs (
            run_id, nombre, timestamp, best_model, wrmse,
            artifacts_dir, source_mode, source_file, pipeline_session_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rid,
            nombre,
            ts,
            item.get("best_model"),
            item.get("wrmse"),
            (item.get("artifacts_dir") or rid),
            item.get("source_mode") or "auto",
            item.get("source_file") if item.get("source_file") is not None else "",
            str(ps).strip() if ps else None,
        ),
    )


def _maybe_migrate_from_json() -> None:
    """Importa ``web/run_history.json`` una vez si la tabla está vacía."""
    json_path = os.path.join(_ROOT, "web", "run_history.json")
    if not os.path.isfile(json_path):
        return
    conn = get_connection()
    try:
        _ensure_runs_table(conn)
        n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        if n > 0:
            return
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, list):
            return
        for raw in data:
            if isinstance(raw, dict):
                _insert_run(conn, raw)
        conn.commit()
        try:
            os.rename(json_path, json_path + ".migrated.bak")
        except OSError:
            pass
    finally:
        conn.close()


def ensure_schema() -> None:
    """Crea la tabla ``runs`` y migra JSON si aplica."""
    global _schema_ready
    if _schema_ready:
        return
    conn = get_connection()
    try:
        _ensure_runs_table(conn)
        conn.commit()
    finally:
        conn.close()
    _maybe_migrate_from_json()
    _schema_ready = True


def _load_history_raw() -> List[Dict[str, Any]]:
    """Lista en orden de inserción (``id`` ASC), equivalente al orden del JSON."""
    ensure_schema()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        _ensure_runs_table(conn)
        cur = conn.execute(
            """
            SELECT run_id, nombre, timestamp, best_model, wrmse,
                   artifacts_dir, source_mode, source_file, pipeline_session_id
            FROM runs ORDER BY id ASC
            """
        )
        rows = cur.fetchall()
        return [_row_from_db(r) for r in rows]
    finally:
        conn.close()


def _save_history_raw(history: List[Any]) -> None:
    """Sustituye todo el historial por la lista dada (mismo contrato que JSON)."""
    ensure_schema()
    conn = get_connection()
    try:
        _ensure_runs_table(conn)
        conn.execute("DELETE FROM runs")
        for item in history:
            if isinstance(item, dict):
                _insert_run(conn, item)
        conn.commit()
    finally:
        conn.close()


def load_history() -> List[Dict[str, Any]]:
    """Lista persistente de ejecuciones (con bloqueo y relleno único de ``nombre``)."""
    global _history_nombre_backfill_done
    with history_file_lock:
        data = _load_history_raw()
        if not _history_nombre_backfill_done:
            changed = False
            for row in data:
                if not isinstance(row, dict):
                    continue
                if not str(row.get("nombre") or "").strip():
                    row["nombre"] = _default_run_nombre(
                        row.get("timestamp") or "", row.get("run_id") or ""
                    )
                    changed = True
            if changed:
                _save_history_raw(data)
            _history_nombre_backfill_done = True
        return data


def save_history(history: List[Any]) -> None:
    with history_file_lock:
        _save_history_raw(history)


def normalize_history_row(row: Dict[str, Any]) -> Dict[str, Any]:
    rid = (row.get("run_id") or "").strip()
    ts = row.get("timestamp") or ""
    nombre = (row.get("nombre") or "").strip()
    if not nombre:
        nombre = _default_run_nombre(ts, rid)
    return {
        "run_id": rid,
        "nombre": nombre,
        "timestamp": ts,
        "best_model": row.get("best_model"),
        "wrmse": row.get("wrmse"),
        "artifacts_dir": row.get("artifacts_dir") or rid,
        "source_mode": row.get("source_mode") or "auto",
        "source_file": row.get("source_file") or "",
    }


def run_id_in_history(run_id: Any) -> bool:
    rid = str(run_id or "").strip()
    if not rid:
        return False
    for row in load_history():
        if isinstance(row, dict) and str(row.get("run_id")) == rid:
            return True
    return False


def add_to_history(
    run_id: Any,
    best_model: Any,
    wrmse: Any,
    source_mode: str = "auto",
    source_file: str = "",
    nombre: Optional[str] = None,
    *,
    pipeline_session_id: Optional[str] = None,
    skip_if_duplicate: bool = True,
) -> bool:
    rid = str(run_id or "").strip()
    if skip_if_duplicate and rid and run_id_in_history(rid):
        logger.info("omitido: run_id ya registrado (%r)", rid)
        return False
    ts = datetime.now().isoformat()
    entry: Dict[str, Any] = {
        "run_id": run_id,
        "nombre": (nombre or "").strip() or _default_run_nombre(ts, str(run_id)),
        "timestamp": ts,
        "best_model": best_model,
        "wrmse": wrmse,
        "artifacts_dir": run_id,
        "source_mode": source_mode,
        "source_file": source_file or "",
    }
    if pipeline_session_id:
        entry["pipeline_session_id"] = str(pipeline_session_id).strip()
    history = load_history()
    history.append(entry)
    history = history[-HISTORY_MAX:]
    save_history(history)
    return True


def get_runs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Últimas ejecuciones en el mismo orden de lista que ``load_history``."""
    h = load_history()
    if limit is None or limit >= len(h):
        return h
    return h[-limit:] if limit > 0 else []


def save_run(row: Dict[str, Any]) -> None:
    """Inserta o reemplaza una fila por ``run_id`` y recorta a ``HISTORY_MAX``."""
    if not isinstance(row, dict):
        return
    rid = (row.get("run_id") or "").strip()
    if not rid:
        return
    ensure_schema()
    with history_file_lock:
        conn = get_connection()
        try:
            _ensure_runs_table(conn)
            _insert_run(conn, row)
            conn.commit()
        finally:
            conn.close()
        data = _load_history_raw()
        if len(data) > HISTORY_MAX:
            data = data[-HISTORY_MAX:]
            _save_history_raw(data)
