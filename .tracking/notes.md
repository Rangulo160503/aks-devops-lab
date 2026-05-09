# Decision / work log

## 2026-05-09
- Added `k8s/` manifests for a minimal-cost AKS lab (1× API, 1× web, NGINX Ingress, ConfigMap + Secret example).
- Added root `Dockerfile` with `--target api` / `--target web` for repo-root builds; component Dockerfiles under `app/` remain canonical for compose.
- Added `app/backend/.dockerignore` and `app/frontend/.dockerignore`; extended repo `.dockerignore` for Terraform state and `k8s/`.
- AKS pod hardening aligned with Microsoft guidance on non-root and Pod Security Standards ([Pod security in AKS](https://learn.microsoft.com/en-us/azure/aks/developer-best-practices-pod-security)).
