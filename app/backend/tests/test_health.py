from __future__ import annotations


def test_root_metadata(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert body["service"] == "proyecto-ml-api"
    assert body["color"] == "blue"
    assert "/healthz" in body["endpoints"]["healthz"]


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_readyz_ok(client):
    res = client.get("/readyz")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ready"
