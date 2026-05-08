"""Flask application factory.

The factory pattern is what lets tests build an isolated app per test (with a
temporary SQLite DB) while production uses Gunicorn to import a single shared
`app` from `backend.wsgi`.
"""
from __future__ import annotations

import logging

import flask as fl

from . import __version__
from .api import health_bp, runs_bp
from .config import Settings, fail_closed_if_unsafe
from .db import create_all, init_engine


def create_app(settings: Settings | None = None) -> fl.Flask:
    settings = settings or Settings.from_env()
    fail_closed_if_unsafe(settings)

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = fl.Flask(settings.app_name)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["APP_ENV"] = settings.app_env
    app.config["APP_COLOR"] = settings.app_color

    init_engine(settings)
    create_all()

    app.register_blueprint(health_bp)
    app.register_blueprint(runs_bp)

    @app.get("/")
    def root():
        return fl.jsonify(
            {
                "ok": True,
                "service": settings.app_name,
                "version": __version__,
                "env": settings.app_env,
                "color": settings.app_color,
                "endpoints": {
                    "healthz": "/healthz",
                    "readyz": "/readyz",
                    "runs": "/api/v1/runs",
                },
            }
        )

    return app
