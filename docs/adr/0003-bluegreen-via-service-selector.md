# ADR 0003 — Blue/Green via Service selector swap

- **Status:** Accepted
- **Date:** 2026-05-07

## Context

We want zero-downtime releases with instant rollback. The two common patterns
on Kubernetes are:

1. **Service selector swap** — one stable Service, two Deployments tagged
   `color=blue|green`, traffic switches by patching the Service selector.
2. **Ingress backend swap** — one stable Service per colour, the Ingress
   `backend.service.name` is repointed.

## Decision

Use pattern (1). It is simpler, atomic at the kube-apiserver level, requires
no Ingress controller-specific annotations, and lets `kubectl port-forward
svc/api-green` smoke a colour without touching real traffic.

## Consequences

- The pipeline is portable across Ingress controllers (NGINX, Traefik,
  AzureApplicationGateway).
- Rollback is one `kubectl patch svc` call.
- Traffic shaping (canary, weighted) is *not* possible with this pattern; if
  needed, switch to NGINX `nginx.ingress.kubernetes.io/canary-*` annotations
  or to Argo Rollouts in a future iteration.

## References

- [oneuptime: native K8s blue/green](https://oneuptime.com/blog/post/2026-02-09-blue-green-deployments-native-kubernetes/view)
