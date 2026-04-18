# Frontend (React + TypeScript + Vite)

Dashboard mínimo que consume la API v1 de Flask (`/api/v1/runs`).

## Scripts

```bash
npm install
npm run dev        # http://localhost:5173  (proxy a http://127.0.0.1:5000)
npm run build      # dist/
npm run typecheck
```

Vite hace proxy de `/api` a Flask en `127.0.0.1:5000` (ver `vite.config.ts`).
Asegúrate de tener el backend con `flask --app backend.main run` (o Docker).
