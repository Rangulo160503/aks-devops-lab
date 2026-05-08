#!/usr/bin/env bash
# scripts/bluegreen-status.sh
#
# Show the current active color, the configured ConfigMap color, and replica
# counts per color. Useful before invoking bluegreen-switch.sh.

set -euo pipefail

NAMESPACE="${1:-proyecto-ml}"

echo "Namespace: ${NAMESPACE}"
echo

cm_color="$(kubectl -n "${NAMESPACE}" get cm proyecto-ml-active-color -o jsonpath='{.data.color}' 2>/dev/null || echo '<missing>')"
api_color="$(kubectl -n "${NAMESPACE}" get svc api -o jsonpath='{.spec.selector.color}')"
web_color="$(kubectl -n "${NAMESPACE}" get svc web -o jsonpath='{.spec.selector.color}')"

printf "ConfigMap active color : %s\n" "${cm_color}"
printf "Service api selector   : color=%s\n" "${api_color}"
printf "Service web selector   : color=%s\n" "${web_color}"
echo

echo "Deployments:"
kubectl -n "${NAMESPACE}" get deploy \
  -l app.kubernetes.io/part-of=proyecto-ml \
  -L color,app.kubernetes.io/component
