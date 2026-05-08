# Legacy codebase

This directory contains the **original** Proyecto_ML application before its
DevOps refactor. It is preserved for historical reference and demo purposes
(showing the *before* state during interviews).

Contents:

- `backend/`            — Flask app with subprocess-based ML execution.
- `frontend/`           — React + Vite SPA (Vite dev proxy).
- `tests/`              — pytest suite for the legacy API.
- `Dockerfile`          — single-stage Python image.
- `docker-compose.yml`  — single-service compose with bind-mounted SQLite.
- `requirements.txt`    — heavy ML stack (XGBoost, statsmodels, sklearn, ...).
- `pytest.ini`          — legacy pytest configuration.

**Rules:**

- Do **not** modify anything under `legacy/`.
- It is excluded from images via `.dockerignore`.
- It is excluded from CI/CD pipelines.
- It does not contribute to the new architecture.

The active codebase lives at the repository root: `app/`, `infra/`,
`pipelines/`, `scripts/`, `docs/`.
