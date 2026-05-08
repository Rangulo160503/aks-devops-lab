# ADR 0001 — PostgreSQL over SQLite

- **Status:** Accepted
- **Date:** 2026-05-07

## Context

The legacy backend used a SQLite file (`data.db`) bind-mounted into the
container. This works for a single-process app but breaks every property the
DevOps lab needs:

- multiple replicas can't share a SQLite writer safely;
- blue/green requires both colors to share state;
- restarts lose data unless a PVC is attached;
- backups are ad-hoc.

## Decision

Replace SQLite with **PostgreSQL** (Azure Database for Flexible Server in
production, `postgres:16-alpine` locally). The application talks to it via
SQLAlchemy + `psycopg`.

## Consequences

- Backend Pods become trivially horizontally scalable (HPA on CPU).
- Blue/green is safe because both colours read/write the same DB.
- Schema changes must follow expand-only / contract-later discipline.
- One more managed service to provision via Terraform.
