# Kubernetes manifests

Plain YAML, no Helm. Deliberately simple so each object is reviewable in PRs
and easy to explain in interviews.

```
base/
  namespace.yaml             Namespace + Pod Security Admission labels
  configmap.yaml             App config + active-color tracker
  secret.example.yaml        Template for SECRET_KEY / DATABASE_URL (never commit real)
  serviceaccount.yaml        SAs for api / web (Workload Identity ready)
  backend-deployment.yaml    api-blue Deployment (probes, limits, non-root, RO root FS)
  backend-service.yaml       api (active), api-blue, api-green Services
  frontend-deployment.yaml   web-blue Deployment
  frontend-service.yaml      web (active), web-blue, web-green Services
  ingress.yaml               NGINX Ingress: /api -> api, / -> web
  hpa.yaml                   HPA on api-blue (CPU 70%)
  pdb.yaml                   PDBs for api / web
  kustomization.yaml         `kubectl apply -k infra/kubernetes/base`

overlays/
  blue-green/                Adds the green Deployments. See Phase 5.
```

## Quick install (kind / minikube / AKS)

```bash
# Pre-req: ingress-nginx installed in the cluster.
kubectl apply -k infra/kubernetes/base
kubectl -n proyecto-ml apply -f infra/kubernetes/base/secret.example.yaml   # dev only

kubectl -n proyecto-ml get pods,svc,ing
```

## Override images

The `image:` lines default to `proyecto-ml-{api,web}:local`. CI replaces them
via `kubectl set image deploy/api-<color> api=<acr>/proyecto-ml-api:<tag>`
(see `pipelines/templates/k8s-deploy.yml`).
