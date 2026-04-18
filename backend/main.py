"""
Entrypoint Flask: API REST JSON (blueprints en ``backend/api``).
La UI vive en ``frontend/`` (React + Vite).
"""
from __future__ import annotations

import os
import sys

import flask as fl

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_APP_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.models.run_history import ensure_schema  # noqa: E402
from backend.api.run_routes import run_bp  # noqa: E402

ensure_schema()

app = fl.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.register_blueprint(run_bp)

app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024

ARTIFACTS_DIR = os.path.join(_PROJECT_ROOT, "artifacts")


@app.errorhandler(413)
def request_entity_too_large(_error):
    return fl.jsonify(
        {
            "ok": False,
            "error": (
                "El archivo o conjunto de archivos excede el tamaño permitido "
                "(300 MB en total)."
            ),
        }
    ), 413


@app.get("/")
def api_root():
    return fl.jsonify(
        {
            "ok": True,
            "service": "Proyecto_ML",
            "api": "/api/v1/runs",
        }
    )
