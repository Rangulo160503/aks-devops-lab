# syntax=docker/dockerfile:1.7

# ---------- Stage 1: build SPA ----------
FROM node:20-alpine AS builder

WORKDIR /build

ARG VITE_API_BASE=/api
ARG VITE_APP_VERSION=dev
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_APP_VERSION=${VITE_APP_VERSION}

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src

RUN npm run build

# ---------- Stage 2: nginx runtime ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

# nginx-unprivileged runs as uid 101 by default.
USER 101

WORKDIR /usr/share/nginx/html

COPY --chown=101:101 nginx.conf /etc/nginx/nginx.conf
COPY --from=builder --chown=101:101 /build/dist/ /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -q -O - http://127.0.0.1:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
