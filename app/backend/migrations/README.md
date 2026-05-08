# Alembic migrations

Alembic-ready directory. The lab uses `Base.metadata.create_all` for simplicity,
but the structure is in place to introduce real migrations:

```bash
cd app/backend
pip install -r requirements-dev.txt
alembic init -t generic migrations
alembic revision --autogenerate -m "create runs"
alembic upgrade head
```

In Kubernetes, run migrations as a **pre-deploy Job** (Helm hook
`helm.sh/hook: pre-install,pre-upgrade`) against the shared Postgres so blue
and green never run incompatible schemas. Always do **expand-only** changes
during a release, contract in the **next** release.
