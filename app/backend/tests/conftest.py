"""Test fixtures: each test gets a fresh in-memory SQLite + fresh Flask app."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def app():
    os.environ["APP_ENV"] = "test"
    os.environ["APP_COLOR"] = "blue"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

    from backend import db as db_mod
    from backend.app import create_app
    from backend.config import Settings

    db_mod._engine = None
    db_mod._SessionLocal = None
    application = create_app(Settings.from_env())
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()
