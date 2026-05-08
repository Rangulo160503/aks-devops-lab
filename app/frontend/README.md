# Frontend (React + Vite, nginx-served)

Static SPA. In production it is built into `dist/`, copied into an `nginx:alpine`
image, and served behind the same Ingress as the backend (`/api` -> backend Service,
`/` -> this container).

## Local dev

```bash
cd app/frontend
npm install
npm run dev    # http://localhost:5173, /api proxied to http://127.0.0.1:8000
```

To point at a different backend during dev:

```bash
VITE_DEV_API_TARGET=http://localhost:8001 npm run dev
```

## Build

```bash
npm run typecheck
npm run build           # outputs to dist/
```

## Build-time configuration

| Variable          | Default | Purpose                                       |
|-------------------|---------|-----------------------------------------------|
| `VITE_API_BASE`   | `/api`  | Base URL the SPA calls. `/api` is same-origin behind Ingress. |
| `VITE_APP_VERSION`| `dev`   | Shown in the footer, set by CI to git SHA.    |
