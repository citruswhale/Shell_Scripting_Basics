# GearLoan frontend

React 18 + Vite single page app. No UI library, just plain CSS. The layout switches to stacked cards on phones (375px wide and up).

## Run it locally

Start the backend on port 8000 first (see `../backend/README.md`), then:

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173, /api is proxied to localhost:8000
```

Use `VITE_API_TARGET=http://some-host:8000 npm run dev` to proxy to a different backend.

## Build

```bash
npm run build      # output goes to dist/
```

## Docker

```bash
docker build -t gearloan-frontend .
docker run -p 3000:8080 -e BACKEND_UPSTREAM=backend:8000 gearloan-frontend
```

The image is `nginx-unprivileged`, so it runs as user 101 and listens on port 8080.
nginx serves the built app and forwards `/api/` to the backend.

| Variable           | Default         | Notes |
|--------------------|-----------------|-------|
| `BACKEND_UPSTREAM` | `backend:8000`  | host:port of the API |
| `NGINX_RESOLVER`   | `127.0.0.11`    | DNS server nginx uses to find the backend. `127.0.0.11` is Docker's DNS. In Kubernetes use `kube-dns.kube-system.svc.cluster.local` and give `BACKEND_UPSTREAM` as a full name like `gearloan-backend.gearloan.svc.cluster.local:8000` |

The backend name is looked up when a request comes in, so nginx starts fine even if the
backend isn't up yet (API calls return 502 until it is). `GET /healthz` is a health check
for the frontend container itself.
