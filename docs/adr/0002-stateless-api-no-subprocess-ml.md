# ADR 0002 — Stateless API, no in-process ML subprocess

- **Status:** Accepted
- **Date:** 2026-05-07

## Context

The legacy `POST /api/v1/runs` shelled out to `python ml_pipeline.py` via
`subprocess.run`, then wrote files to a local `artifacts/` directory. In
Kubernetes this fails:

- a Pod restart kills the subprocess mid-run with no signal handling;
- artifacts written to ephemeral storage vanish when the Pod recycles;
- Gunicorn workers are blocked for minutes (the `--timeout 600` in the legacy
  Dockerfile was a giveaway);
- horizontal scaling fights for the same disk.

## Decision

For the lab, replace the heavy ML pipeline with a **deterministic stub**
(`backend.pipeline.run_stub_pipeline`) that returns a synthetic result in
microseconds. The function lives in-process, never touches disk, and uses
no environment outside the request.

A future iteration may externalise real ML to a Kubernetes `Job` triggered
from the API, with results persisted to Postgres + Blob.

## Consequences

- API requests stay short (≤30 s timeout, default Gunicorn defaults).
- The image no longer needs XGBoost / statsmodels / sklearn — image size and
  build time drop dramatically.
- Demos can showcase HPA, blue/green, and quick rollouts without the noise of
  a real ML pipeline.
- Real ML is explicitly out of scope; the README says so.
