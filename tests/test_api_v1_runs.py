"""API REST v1 (`/api/v1/runs`) y entrypoint Flask (`backend.main`)."""
from __future__ import annotations

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente Flask con BD SQLite y `artifacts/` aislados (tmp_path)."""
    from backend.infrastructure import db

    tmp_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", str(tmp_db))

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    import importlib

    from backend.models import run_history as rh

    rh._schema_ready = False
    rh._history_nombre_backfill_done = False
    importlib.reload(rh)
    rh.ensure_schema()

    from backend.services import run_management_service

    monkeypatch.setattr(run_management_service, "ARTIFACTS_DIR", str(artifacts_dir))

    from backend import main as backend_main

    monkeypatch.setattr(backend_main, "ARTIFACTS_DIR", str(artifacts_dir))
    backend_main.app.testing = True
    return backend_main.app.test_client()


def test_list_runs_empty(client):
    res = client.get("/api/v1/runs")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["ok"] is True
    assert payload["runs"] == []


def test_delete_invalid_id(client):
    res = client.delete("/api/v1/runs/!!!")
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_rename_missing_run(client):
    res = client.patch("/api/v1/runs/20260101_000000", json={"nombre": "Nuevo"})
    assert res.status_code == 404
    assert res.get_json()["ok"] is False


def test_get_root_json(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("ok") is True
    assert data.get("api") == "/api/v1/runs"


def test_clear_history_empty(client):
    res = client.delete("/api/v1/runs")
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["ok"] is True


def test_register_invalid_run_id(client):
    res = client.post("/api/v1/runs/register", json={"run_id": "!!!"})
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_register_artifacts_dir_missing(client):
    res = client.post("/api/v1/runs/register", json={"run_id": "validrun20260101"})
    assert res.status_code == 404
    assert res.get_json()["ok"] is False
