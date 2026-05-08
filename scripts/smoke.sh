#!/usr/bin/env bash
# scripts/smoke.sh
#
# Minimal post-deploy smoke test. Hits /healthz and /readyz against the given
# base URL and exits non-zero on any failure. Used by the CD pipeline after
# every Helm/kubectl rollout.
#
# Usage:
#   scripts/smoke.sh https://app.dev.example.com
#   scripts/smoke.sh http://localhost:8000

set -euo pipefail

BASE="${1:?usage: $0 <base-url>}"
TIMEOUT="${SMOKE_TIMEOUT:-5}"

check() {
  local path="$1" expected="$2"
  local code
  code="$(curl -fsS -o /tmp/smoke-body --max-time "${TIMEOUT}" -w '%{http_code}' "${BASE}${path}" || true)"
  if [ "${code}" != "${expected}" ]; then
    echo "FAIL ${path}: expected ${expected}, got ${code}"
    cat /tmp/smoke-body 2>/dev/null || true
    return 1
  fi
  echo "OK   ${path} -> ${code}"
}

echo "Smoke against ${BASE}"
check /healthz 200
check /readyz  200
check /        200
echo "Smoke OK"
