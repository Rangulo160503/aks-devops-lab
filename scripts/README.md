# Operator scripts

| Script                    | Purpose                                          |
|---------------------------|--------------------------------------------------|
| `bluegreen-switch.sh`     | Atomically swap the active color (api + web).    |
| `bluegreen-status.sh`     | Print current color + per-color replica counts.  |
| `smoke.sh`                | Hit `/`, `/healthz`, `/readyz` and exit non-zero on failure. |

All scripts are POSIX-ish bash with `set -euo pipefail`. They assume `kubectl`
is configured against the target cluster (`KUBECONFIG`) and use no temporary
state on disk beyond `/tmp`.

## Typical release flow

```bash
# 1. New version is deployed to the IDLE color (CI does this).
kubectl -n proyecto-ml set image deploy/api-green api=acr.azurecr.io/proyecto-ml-api:abc123
kubectl -n proyecto-ml set image deploy/web-green web=acr.azurecr.io/proyecto-ml-web:abc123
kubectl -n proyecto-ml scale deploy/api-green --replicas=2
kubectl -n proyecto-ml scale deploy/web-green --replicas=2

# 2. Smoke the idle color via its dedicated Service.
kubectl -n proyecto-ml port-forward svc/api-green 8001:80 &
scripts/smoke.sh http://localhost:8001

# 3. Swap.
scripts/bluegreen-switch.sh proyecto-ml green

# 4. Soak. Then scale the old color down.
kubectl -n proyecto-ml scale deploy/api-blue --replicas=0
kubectl -n proyecto-ml scale deploy/web-blue --replicas=0

# Rollback if needed:
scripts/bluegreen-switch.sh proyecto-ml blue
```
