# syntax=docker/dockerfile:1.7
# Monorepo entrypoint: build from the repository ROOT (`.`).
#
# The canonical, copy-paste-friendly builds remain:
#   app/backend/Dockerfile   with context app/backend
#   app/frontend/Dockerfile  with context app/frontend
#
# This file duplicates those recipes with path prefixes so CI or local scripts
# can use a single context (the whole repo) if desired.
#
#   docker build --target web -t pmldevacr.azurecr.io/proyecto-ml:frontend \
#     --build-arg VITE_API_BASE=/api --build-arg VITE_APP_VERSION=dev .
#
#   docker build --target api -t pmldevacr.azurecr.io/proyecto-ml:backend .
#
# When --target is omitted, the final stage is `api` (Flask API).

# ======================== Frontend (SPA + nginx) ========================
FROM node:20-alpine AS web-builder

WORKDIR /build

ARG VITE_API_BASE=/api
ARG VITE_APP_VERSION=dev
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_APP_VERSION=${VITE_APP_VERSION}

COPY app/frontend/package.json app/frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

COPY app/frontend/tsconfig.json app/frontend/vite.config.ts app/frontend/index.html ./
COPY app/frontend/src ./src

RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS web

USER 101
WORKDIR /usr/share/nginx/html

COPY --chown=101:101 app/frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=web-builder --chown=101:101 /build/dist/ /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -q -O - http://127.0.0.1:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]

# ======================== Backend (Flask + Gunicorn) ========================
FROM python:3.12-slim AS api-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY app/backend/requirements.txt ./
RUN python -m pip install --upgrade pip \
 && pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    GUNICORN_BIND=0.0.0.0:8000

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home /app --shell /usr/sbin/nologin app

COPY --from=api-builder /wheels /wheels
COPY app/backend/requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY app/backend/src ./src
COPY app/backend/gunicorn.conf.py ./

USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "backend.wsgi:app"]
