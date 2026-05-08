"""12-factor configuration for the backend.

All runtime settings come from environment variables. Defaults are intentionally
safe-for-local only; production overrides arrive via Kubernetes ConfigMap and
Secrets (see `infra/kubernetes/base/configmap.yaml` and `secret.yaml`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_color: str
    secret_key: str
    database_url: str
    log_level: str
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.environ.get("APP_NAME", "proyecto-ml-api"),
            app_env=os.environ.get("APP_ENV", "local"),
            app_color=os.environ.get("APP_COLOR", "blue"),
            secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
            database_url=os.environ.get(
                "DATABASE_URL",
                "sqlite+pysqlite:///:memory:",
            ),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            cors_origins=tuple(
                o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
            ),
        )


def is_production(settings: Settings) -> bool:
    return settings.app_env.lower() in {"prod", "production"}


def fail_closed_if_unsafe(settings: Settings) -> None:
    """Refuse to boot in production with the dev defaults."""
    if is_production(settings) and settings.secret_key == "dev-secret-change-me":
        raise RuntimeError("SECRET_KEY must be set in production")
    if is_production(settings) and settings.database_url.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL must be Postgres in production")
