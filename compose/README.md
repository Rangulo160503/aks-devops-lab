# Local docker-compose stack

```bash
docker compose -f compose/docker-compose.yml up --build
```

Services:

| Service   | Port  | Notes                                      |
|-----------|-------|--------------------------------------------|
| postgres  | 5432  | Data in named volume `pgdata`.             |
| backend   | 8000  | Flask + Gunicorn, talks to `postgres:5432`.|
| frontend  | 8080  | nginx serving the built SPA.               |

The frontend container is the **production** image. It only serves static
assets, so it cannot reach `/api` on its own (no nginx proxy is configured to
keep parity with Kubernetes, where Ingress does the routing). For interactive
dev use the Vite dev server:

```bash
cd app/frontend
npm install
npm run dev    # http://localhost:5173, Vite proxies /api to localhost:8000
```

The compose stack is mainly a smoke-test harness to verify the **container
images** themselves build and boot.
