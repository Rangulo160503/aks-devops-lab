# Pipelines

Multi-stage Azure DevOps YAML. The pipeline is opinionated and written for
**clarity** — each stage maps to a clearly named template.

## Stages

```mermaid
flowchart LR
  v[validate] --> t[test]
  t --> b[build_images]
  b --> dev[deploy_dev\n(main only)]
  b --> idle[deploy_prod_idle\n(tag v* only,\nmanual approval)]
  idle --> swap[bluegreen_switch\n(manual approval)]
```

| Stage              | Trigger                  | What it does                                     |
|--------------------|--------------------------|--------------------------------------------------|
| `validate`         | Every PR + main + tag    | Ruff, tsc, kubeconform, terraform fmt/validate.  |
| `test`             | Every PR + main + tag    | pytest with sidecar Postgres, vite build.        |
| `build_images`     | main + tag               | Docker build/push of api + web to ACR.           |
| `deploy_dev`       | main                     | Rolling update of `blue` Deployments in dev.     |
| `deploy_prod_idle` | tag `v*`                 | Update IDLE color in prod (no traffic shift).    |
| `bluegreen_switch` | After `deploy_prod_idle` | Smoke idle, atomic Service patch, drain old.     |

Approvals live on the AzDO **Environment** `proyecto-ml-prod` (per
[Microsoft docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)),
not in YAML.

## Branching strategy

- Trunk-based.
- `main` is always deployable.
- Feature branches -> PR -> squash merge.
- Cut a release by tagging `vYYYY.MM.DD-N` from `main`.

## Image tagging

- Immutable: `<git-short-sha>-<build-id>`.
- Rolling pointer: `latest` (documentation only, never deployed).

## Variable groups (Library)

| Group        | Required keys                                                              |
|--------------|----------------------------------------------------------------------------|
| `pml-common` | `acrLoginServer`, `acrServiceConnection`                                   |
| `pml-dev`    | `aksServiceConnection`, `aksClusterName`, `ingressHost`                    |
| `pml-prod`   | `aksServiceConnection`, `aksClusterName`, `ingressHost`, `currentColor`, `idleColor` |

After every successful release, **swap** `currentColor` and `idleColor` in
`pml-prod` so the next pipeline targets the now-idle colour.

## Naming conventions

- Pipelines: `proyecto-ml-ci`, `proyecto-ml-cd`, `proyecto-ml-infra`.
- Environments: `proyecto-ml-dev`, `proyecto-ml-prod`.
- Service connections: `acrServiceConnection`, `aks{Env}ServiceConnection`.

## References

- [MS Learn – Pipeline approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)
- [MS Learn – Environments](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)
