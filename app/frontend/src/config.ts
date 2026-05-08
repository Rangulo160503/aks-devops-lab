// Runtime configuration for the SPA.
//
// Same-origin by default (`/api`) so the same image works in dev (Vite proxy),
// docker-compose (Ingress-less), and Kubernetes (NGINX Ingress path rules).
// Override at build time with `VITE_API_BASE=https://other.example/api`.

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "/api";
export const APP_VERSION: string = import.meta.env.VITE_APP_VERSION ?? "dev";
