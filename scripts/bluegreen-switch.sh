#!/usr/bin/env bash
# scripts/bluegreen-switch.sh
#
# Atomically switch the `api` and `web` Service selectors to the target color,
# then update the `proyecto-ml-active-color` ConfigMap.
#
# Pre-conditions (verified before patching):
#   - Target color Deployments exist.
#   - Target color Pods are Available.
#
# Rollback: rerun the script with the old color.
#
# Usage:
#   scripts/bluegreen-switch.sh <namespace> <target-color>
#   scripts/bluegreen-switch.sh proyecto-ml green

set -euo pipefail

NAMESPACE="${1:?usage: $0 <namespace> <target-color>}"
TARGET="${2:?usage: $0 <namespace> <target-color>}"

case "${TARGET}" in
  blue|green) ;;
  *) echo "ERROR: target color must be 'blue' or 'green' (got: ${TARGET})" >&2; exit 2 ;;
esac

echo "==> Verifying Deployments exist in namespace '${NAMESPACE}'..."
kubectl -n "${NAMESPACE}" get deploy "api-${TARGET}" "web-${TARGET}" >/dev/null

echo "==> Waiting for Deployments to become Available..."
kubectl -n "${NAMESPACE}" rollout status "deploy/api-${TARGET}" --timeout=180s
kubectl -n "${NAMESPACE}" rollout status "deploy/web-${TARGET}" --timeout=180s

current="$(kubectl -n "${NAMESPACE}" get svc api -o jsonpath='{.spec.selector.color}')"
echo "==> Current active color: ${current}"
echo "==> Target color:         ${TARGET}"

if [ "${current}" = "${TARGET}" ]; then
  echo "==> Already on ${TARGET}; nothing to do."
  exit 0
fi

patch=$(printf '{"spec":{"selector":{"app.kubernetes.io/name":"%s","color":"%s"}}}' "PLACEHOLDER" "${TARGET}")

echo "==> Patching Service/api selector -> color=${TARGET}"
kubectl -n "${NAMESPACE}" patch svc api --type merge \
  -p "$(printf '{"spec":{"selector":{"app.kubernetes.io/name":"api","color":"%s"}}}' "${TARGET}")"

echo "==> Patching Service/web selector -> color=${TARGET}"
kubectl -n "${NAMESPACE}" patch svc web --type merge \
  -p "$(printf '{"spec":{"selector":{"app.kubernetes.io/name":"web","color":"%s"}}}' "${TARGET}")"

echo "==> Updating ConfigMap proyecto-ml-active-color"
kubectl -n "${NAMESPACE}" patch cm proyecto-ml-active-color --type merge \
  -p "$(printf '{"data":{"color":"%s"}}' "${TARGET}")"

echo "==> Switch complete. Old color (${current}) Pods are still running for fast rollback."
echo "    Scale them to 0 once the new color has soaked:"
echo "      kubectl -n ${NAMESPACE} scale deploy/api-${current} --replicas=0"
echo "      kubectl -n ${NAMESPACE} scale deploy/web-${current} --replicas=0"
