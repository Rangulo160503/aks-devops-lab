# Backend (Flask + Postgres, stateless)

Stateless JSON API. No filesystem state, no SQLite, no subprocess ML.
Persistence is **PostgreSQL** only.

## Layout

```
src/backend/
  __init__.py
  app.py        Flask app factory (create_app)
  wsgi.py       Gunicorn entrypoint (`backend.wsgi:app`)
  config.py     12-factor environment config
  db.py         SQLAlchemy engine/session
  models.py     ORM models (Run)
  schemas.py    Pydantic input/output schemas
  pipeline.py   ML stub (lab-only; deterministic)
  api/
    health.py   /healthz, /readyz
    runs.py     /api/v1/runs
migrations/     Alembic-ready directory
tests/          pytest suite (uses sqlite in-memory by default)
```

## Endpoints

| Method | Path                  | Notes                                    |
|--------|-----------------------|------------------------------------------|
| GET    | `/`                   | Service metadata (name, version, color). |
| GET    | `/healthz`            | Liveness — never touches the DB.         |
| GET    | `/readyz`             | Readiness — pings the DB.                |
| GET    | `/api/v1/runs`        | List runs (newest first).                |
| POST   | `/api/v1/runs`        | Create a run via the ML stub.            |
| GET    | `/api/v1/runs/<id>`   | Fetch a single run.                      |
| DELETE | `/api/v1/runs/<id>`   | Delete a run.                            |

## Local dev

```bash
cd app/backend
python -m venv .venv && . .venv/Scripts/activate    # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
export DATABASE_URL="sqlite+pysqlite:///:memory:"   # PowerShell: $env:DATABASE_URL=...
export SECRET_KEY="dev-secret"
export APP_COLOR="blue"
python -m gunicorn -c gunicorn.conf.py backend.wsgi:app
```

For Postgres locally use `compose/docker-compose.yml` (see Phase 3).
