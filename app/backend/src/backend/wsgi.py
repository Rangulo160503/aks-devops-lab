"""Gunicorn entrypoint: `gunicorn backend.wsgi:app`."""
from __future__ import annotations

from .app import create_app

app = create_app()
