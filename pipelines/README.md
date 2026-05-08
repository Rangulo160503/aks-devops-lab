# Azure DevOps pipelines

Multi-stage YAML for Proyecto_ML.

```
pipelines/
  azure-pipelines.yml             entry point (stages = pipeline outline)
  templates/
    validate.yml                  ruff, tsc, kubeconform, terraform fmt/validate
    test-backend.yml              pytest with a sidecar postgres
    test-frontend.yml             tsc + vite build, publishes dist as artifact
    docker-build-push.yml         BuildKit build + ACR push (per image)
    k8s-deploy.yml                set image + scale + rollout status (per color)
    bluegreen-swap.yml            smoke + Service patch + drain old color
  variables/
    common.yml                    namespace, ACR connection (variable group)
    dev.yml                       dev cluster + ingress + active color
    prod.yml                      prod cluster + ingress + current/idle colors
```

## One-time AzDO setup

1. **Service connections**
   - `acrServiceConnection` (Docker registry, type ACR).
   - `aksDevServiceConnection`, `aksProdServiceConnection` (Kubernetes,
     type Azure Subscription, namespace `proyecto-ml`).

2. **Variable groups (Library)**
   - `pml-common`: `acrLoginServer`, `acrServiceConnection`.
   - `pml-dev`:    `aksServiceConnection`, `aksClusterName`, `ingressHost`.
   - `pml-prod`:   `aksServiceConnection`, `aksClusterName`, `ingressHost`,
     `currentColor`, `idleColor`. After every successful release, swap the
     two color values so the next pipeline targets the now-idle color.

3. **Environments** (Pipelines -> Environments)
   - `proyecto-ml-dev`  : no approvals.
   - `proyecto-ml-prod` : add a manual **approval check** before
     `deploy_prod_idle` and another before `bluegreen_switch`.

## Branching / triggers

- `main` -> CI + dev deploy (single color, rolling update).
- Tag `v*` -> CI + prod idle-color deploy + manual approval -> swap.
- PRs -> validate + test only, no image push.

## Naming convention

- Image tag: `<git-short-sha>-<build-id>` (immutable).
- Floating tag `latest` is pushed for documentation only; deployments always
  use the immutable tag.
