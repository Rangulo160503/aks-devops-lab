"""
Ejecución del pipeline ML desde la API: fusión de CSV en ``data/`` y subprocess a
``backend/pipeline/ml_pipeline.py``. Sin dependencias de Flask (sesiones/UI).
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from backend.models.run_history import add_to_history
from backend.services import run_management_service as rms

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MERGED_DATASET_BASENAME = "merged_dataset.csv"


def _data_dir() -> str:
    return os.path.join(_PROJECT_ROOT, "data")


def list_csv_files() -> List[str]:
    d = _data_dir()
    if not os.path.exists(d):
        return []
    return [f for f in os.listdir(d) if f.endswith(".csv")]


def csv_basename_on_disk(name: Any) -> Optional[str]:
    if not name or not isinstance(name, str):
        return None
    n = name.strip()
    if not n or n != os.path.basename(n):
        return None
    if os.sep in n or (os.altsep and os.altsep in n):
        return None
    if n not in list_csv_files():
        return None
    return n


def _read_csv_for_merge(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(
            path,
            encoding="utf-8",
            encoding_errors="replace",
            low_memory=False,
            on_bad_lines="skip",
        )
    except TypeError:
        try:
            return pd.read_csv(path, encoding="utf-8", low_memory=False)
        except Exception:
            return pd.read_csv(path, encoding="latin-1", low_memory=False)
    except Exception:
        try:
            return pd.read_csv(path, encoding="latin-1", low_memory=False)
        except Exception as e2:
            logger.warning("merge: lectura fallida %r: %s", path, e2)
            raise


def merge_csv_datasets(file_names: List[str]) -> Tuple[str, List[str]]:
    """
    Une CSV en ``data/`` en ``MERGED_DATASET_BASENAME``.

    Returns:
        (basename del CSV fusionado, lista de nombres de archivo usados en orden).
    """
    ordered: List[str] = []
    for raw in file_names or []:
        if not raw or not isinstance(raw, str):
            continue
        fn = csv_basename_on_disk(raw.strip())
        if not fn:
            continue
        if fn.lower() == MERGED_DATASET_BASENAME.lower():
            continue
        if fn not in ordered:
            ordered.append(fn)
    if not ordered:
        raise ValueError(
            "No hay CSV válidos para unir (excluyendo el consolidado previo)."
        )

    dfs = []
    for fn in ordered:
        path = os.path.join(_data_dir(), fn)
        try:
            dfs.append(_read_csv_for_merge(path))
        except Exception as e:
            logger.warning("merge: error leyendo %r: %s", path, e)
            raise

    df_all = pd.concat(dfs, ignore_index=True)

    date_keys = ("fecha", "date", "timestamp")
    for col in df_all.columns:
        key = str(col).strip().lower()
        if key in date_keys:
            try:
                df_all = df_all.copy()
                df_all[col] = pd.to_datetime(df_all[col], errors="coerce")
                df_all = df_all.sort_values(col, na_position="last")
                break
            except Exception:
                pass

    merged_path = os.path.join(_data_dir(), MERGED_DATASET_BASENAME)
    os.makedirs(_data_dir(), exist_ok=True)
    df_all.to_csv(merged_path, index=False)
    logger.info(
        "merge: dataset unificado %s (%s filas, %s archivo(s))",
        MERGED_DATASET_BASENAME,
        len(df_all),
        len(ordered),
    )
    return MERGED_DATASET_BASENAME, ordered


def _snapshot_artifact_run_ids() -> set:
    ad = rms.ARTIFACTS_DIR
    if not os.path.isdir(ad):
        return set()
    out = set()
    try:
        for name in os.listdir(ad):
            if rms.is_safe_run_id(name) and os.path.isdir(os.path.join(ad, name)):
                out.add(name)
    except OSError:
        pass
    return out


def _newest_artifact_dir_mtime() -> Optional[str]:
    ad = rms.ARTIFACTS_DIR
    if not os.path.isdir(ad):
        return None
    paths = []
    try:
        for name in os.listdir(ad):
            full = os.path.join(ad, name)
            if os.path.isdir(full) and rms.is_safe_run_id(name):
                paths.append(full)
    except OSError:
        return None
    if not paths:
        return None
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths[0]


def _resolve_run_dir_after_ml1(before_ids: set) -> Optional[str]:
    after = _snapshot_artifact_run_ids()
    new = after - before_ids
    ad = rms.ARTIFACTS_DIR
    if len(new) == 1:
        rid = next(iter(new))
        return os.path.join(ad, rid)
    if len(new) > 1:
        paths = [os.path.join(ad, n) for n in new]
        paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return paths[0]
    return _newest_artifact_dir_mtime()


def register_history_from_execute_output(
    out: Dict[str, Any], *, skip_if_duplicate: bool = True
) -> bool:
    if not out.get("ok") or not isinstance(out.get("history"), dict):
        return False
    h = out["history"]
    return bool(
        add_to_history(
            h["run_id"],
            h["best_model"],
            h["wrmse"],
            source_mode=h.get("source_mode") or "auto",
            source_file=h.get("source_file") or "",
            pipeline_session_id=h.get("pipeline_session_id"),
            skip_if_duplicate=skip_if_duplicate,
        )
    )


def execute_ml1_for_csv_dataset(
    csv_basename: str,
    *,
    history_source_mode: Optional[str] = None,
    history_source_file: Optional[str] = None,
    pipeline_session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ejecuta ``ml_pipeline.py csv <archivo>`` para un CSV en ``data/``.

    No escribe en el historial; el llamador debe usar ``_register_history_from_execute_output``.
    """
    fn = csv_basename_on_disk(csv_basename)
    if not fn:
        return {
            "ok": False,
            "run_id": None,
            "dataset": None,
            "error": "Dataset no encontrado.",
        }
    source_mode = "csv"
    selected_file = fn
    ml_script = os.path.join(_PROJECT_ROOT, "backend", "pipeline", "ml_pipeline.py")
    before_ids = _snapshot_artifact_run_ids()
    cmd = [sys.executable, ml_script, source_mode, selected_file]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except Exception as exc:
        return {"ok": False, "run_id": None, "dataset": fn, "error": str(exc)}
    if result.returncode != 0:
        err = (result.stderr or "").strip() or (result.stdout or "").strip()
        return {
            "ok": False,
            "run_id": None,
            "dataset": fn,
            "error": err or "Error de ejecución.",
        }
    latest_run = _resolve_run_dir_after_ml1(before_ids)
    if not latest_run:
        return {
            "ok": False,
            "run_id": None,
            "dataset": fn,
            "error": "No se detectó carpeta de artefactos.",
        }
    rid_new = os.path.basename(latest_run)
    meta_path = os.path.join(latest_run, "meta.json")
    best_model = "Unknown"
    wrmse = None
    meta_rid = rid_new
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)
        best_model = meta.get("best_model", "Unknown")
        meta_rid = meta.get("run_id") or rid_new
        errors_path = os.path.join(latest_run, "errores_modelos.csv")
        if os.path.exists(errors_path):
            errors_df = pd.read_csv(errors_path, index_col=0)
            if best_model in errors_df.index:
                wrmse = errors_df.loc[best_model, "WRMSE"]
    hist_id = meta_rid if rms.is_safe_run_id(str(meta_rid)) else rid_new
    hist_mode = (
        history_source_mode if history_source_mode is not None else source_mode
    )
    hist_file = (
        history_source_file if history_source_file is not None else selected_file
    )
    out_rid = hist_id if rms.is_safe_run_id(str(hist_id)) else rid_new
    return {
        "ok": True,
        "run_id": str(out_rid),
        "dataset": fn,
        "error": None,
        "history": {
            "run_id": hist_id,
            "best_model": best_model,
            "wrmse": wrmse,
            "source_mode": hist_mode,
            "source_file": hist_file,
            "pipeline_session_id": pipeline_session_id,
        },
    }
