"""Persistencia del historial de runs (`backend.models.run_history`, SQLite)."""
from __future__ import annotations

import pytest


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Aísla la tabla runs en una BD temporal para evitar tocar data.db real."""
    from backend.infrastructure import db

    tmp_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", str(tmp_db))

    # Reimportar run_history para que apunte al parche.
    import importlib

    from backend.models import run_history as rh

    rh._schema_ready = False
    rh._history_nombre_backfill_done = False
    importlib.reload(rh)
    rh.ensure_schema()
    yield rh


def test_add_to_history_and_load(isolated_db):
    rh = isolated_db
    ok = rh.add_to_history(
        "20260101_120000",
        "SARIMA",
        123.45,
        source_mode="csv",
        source_file="demo.csv",
    )
    assert ok is True

    rows = rh.load_history()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "20260101_120000"
    assert rows[0]["best_model"] == "SARIMA"
    assert rows[0]["source_mode"] == "csv"
    assert rows[0]["nombre"].startswith("Ejecución -")


def test_skip_duplicate_run_id(isolated_db):
    rh = isolated_db
    rh.add_to_history("20260101_120000", "A", 1.0)
    dup = rh.add_to_history("20260101_120000", "B", 2.0)
    assert dup is False
    rows = rh.load_history()
    assert len(rows) == 1


def test_history_max_truncates(isolated_db):
    rh = isolated_db
    for i in range(rh.HISTORY_MAX + 5):
        rh.add_to_history(f"2026010{i:02d}_000000", "M", float(i))
    rows = rh.load_history()
    assert len(rows) == rh.HISTORY_MAX


def test_run_id_in_history(isolated_db):
    rh = isolated_db
    rh.add_to_history("20260101_120000", "A", 1.0)
    assert rh.run_id_in_history("20260101_120000") is True
    assert rh.run_id_in_history("nonexistent") is False


def test_normalize_history_row_fills_nombre(isolated_db):
    rh = isolated_db
    row = rh.normalize_history_row(
        {"run_id": "20260315_101010", "timestamp": "2026-03-15T10:10:10"}
    )
    assert row["nombre"] == "Ejecución - 2026-03-15"
    assert row["artifacts_dir"] == "20260315_101010"
    assert row["source_mode"] == "auto"
