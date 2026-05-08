from __future__ import annotations


def test_list_empty(client):
    res = client.get("/api/v1/runs")
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert body["runs"] == []


def test_create_then_get_then_delete(client):
    res = client.post("/api/v1/runs", json={"nombre": "lab-run", "source_mode": "stub"})
    assert res.status_code == 201
    run = res.get_json()["run"]
    assert run["nombre"] == "lab-run"
    assert run["best_model"] in {"SARIMA", "HoltWinters", "MLP", "XGBoost"}
    assert isinstance(run["wrmse"], float)

    rid = run["run_id"]

    fetched = client.get(f"/api/v1/runs/{rid}").get_json()
    assert fetched["run"]["run_id"] == rid

    listed = client.get("/api/v1/runs").get_json()
    assert any(r["run_id"] == rid for r in listed["runs"])

    deleted = client.delete(f"/api/v1/runs/{rid}")
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/runs/{rid}").status_code == 404


def test_invalid_run_id(client):
    assert client.get("/api/v1/runs/!!!bad").status_code == 400
    assert client.delete("/api/v1/runs/!!!bad").status_code == 400


def test_create_default_nombre(client):
    res = client.post("/api/v1/runs", json={})
    assert res.status_code == 201
    assert res.get_json()["run"]["nombre"].startswith("Ejecucion")
