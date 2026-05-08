# Operator scripts

| Script                    | Purpose                                          |
|---------------------------|--------------------------------------------------|
| `bluegreen-switch.sh`     | Atomically swap the active color (api + web).    |
| `bluegreen-status.sh`     | Print current color + per-color replica counts.  |
| `smoke.sh`                | Hit `/`, `/healthz`, `/readyz` and exit non-zero on failure. |
| `tf-bootstrap.sh`         | az-CLI fallback for bootstrapping the Terraform remote-state backend. |
| `tf-bootstrap.ps1`        | PowerShell variant of `tf-bootstrap.sh`.         |
| `tf-destroy-main.sh`      | Destroy the MAIN Terraform stack only; refuses to touch the bootstrap stack. |

All scripts are POSIX-ish bash with `set -euo pipefail`. The `bluegreen-*` /
`smoke.sh` scripts assume `kubectl` is configured against the target cluster
(`KUBECONFIG`); the `tf-*` scripts assume an authenticated `az` session
(`az login`).

## Terraform bootstrap

The `tf-bootstrap.{sh,ps1}` scripts are an az-CLI-only equivalent of running
`terraform apply` in `infra/bootstrap/`. Use whichever fits your shell. Both
are idempotent and write `infra/terraform/envs/{dev,prod}.backend.hcl`. See
[`docs/terraform-bootstrap.md`](../docs/terraform-bootstrap.md).

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
