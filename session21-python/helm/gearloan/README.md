# gearloan Helm chart

Deploys GearLoan to Kubernetes: FastAPI backend, nginx/React frontend and a
single Postgres pod with a PVC.

| Object | Name | Notes |
|---|---|---|
| Deployment + ClusterIP Service | `gearloan-backend` | port 8000, probes `/health` (startup, liveness) and `/ready` (readiness) |
| Deployment + ClusterIP Service | `gearloan-frontend` | port 8080, probes `/healthz` |
| StatefulSet + headless Service | `gearloan-postgres` | PVC `data-gearloan-postgres-0` |
| HPA | backend, frontend | CPU 70 %, 2 to 5 pods |
| Ingress | `gearloan` | `/api` -> backend, `/` -> frontend |
| ConfigMap / Secret | `gearloan-backend` / `gearloan-db` | settings / DB password |
| ServiceMonitor | `gearloan-backend` | only when `serviceMonitor.enabled=true` |

## Install

```bash
# minikube: build the images and copy them into the node
docker build -t gearloan-backend:local backend
docker build -t gearloan-frontend:local frontend
minikube -p devops-lab image load gearloan-backend:local
minikube -p devops-lab image load gearloan-frontend:local

kubectl apply -f k8s/namespace.yaml
helm lint helm/gearloan -f helm/gearloan/values-local.yaml

export PGPW=$(openssl rand -hex 16)      # or leave it out and the chart makes one
helm upgrade --install gearloan helm/gearloan -n gearloan \
  -f helm/gearloan/values-local.yaml --set postgres.password="$PGPW" \
  --wait --timeout 5m

# test through the ingress
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8090:80
curl -H "Host: gearloan.local" http://127.0.0.1:8090/api/info
```

Later upgrades do not need the password again: the chart reads the existing
Secret (`lookup`) and keeps it.

```bash
helm upgrade gearloan helm/gearloan -n gearloan -f helm/gearloan/values-local.yaml --set backend.appVersion=1.0.1 --wait
helm history gearloan -n gearloan
helm rollback gearloan 1 -n gearloan     # if needed
```

## Main values

| Key | Default | Description |
|---|---|---|
| `image.registry` | `ghcr.io/citruswhale` | empty = plain local image names |
| `image.pullPolicy` | `IfNotPresent` | `Never` in values-local.yaml |
| `backend.image.repository` / `.tag` | `gearloan-backend` / `""` | empty tag = Chart `appVersion` |
| `frontend.image.repository` / `.tag` | `gearloan-frontend` / `""` | same |
| `backend.appVersion` | `""` | shown by `/api/info`, empty = Chart `appVersion` |
| `backend.replicaCount`, `frontend.replicaCount` | `2` | only used when the HPA is off |
| `backend.hpa.*`, `frontend.hpa.*` | on, 2-5, 70 % | when on, Deployments have no `replicas:` field |
| `backend.resources` | 100m/128Mi, limit 500m/512Mi | |
| `frontend.resources` | 50m/64Mi, limit 200m/128Mi | |
| `frontend.nginxResolver` | `kube-dns.kube-system.svc.cluster.local` | DNS nginx uses to find the backend |
| `postgres.enabled` | `true` | `false` + `postgres.externalHost` for RDS |
| `postgres.password` | `""` | empty = random on first install, kept on upgrade |
| `postgres.existingSecret` | `""` | your own Secret with key `postgres-password` |
| `postgres.storage.size` / `.storageClassName` | `1Gi` / `""` | `standard` on minikube, `gp3` on EKS |
| `postgres.resources` | 100m/256Mi, limit 500m/512Mi | |
| `ingress.enabled` / `.className` / `.host` | `true` / `nginx` / `""` | `gearloan.local` on minikube |
| `serviceMonitor.enabled` | `false` | needs kube-prometheus-stack CRDs |
| `serviceMonitor.labels` | `release: kube-prometheus-stack` | must match the Prometheus selector |

Values files: `values-local.yaml` (minikube), `values-eks.yaml` (EKS + Argo CD).

## Database migrations

The backend container runs `alembic upgrade head` before it starts uvicorn.
`alembic/env.py` takes a Postgres advisory lock first, so with 2+ replicas only
one pod migrates and the others wait, then find nothing to do. An init
container (`wait-for-db`) waits for Postgres, so pods do not crash-loop on the
first install. No Helm hook Job is needed, and this works the same on install,
upgrade and under Argo CD.

## Notes

- The password goes into a connection URL, so use letters and digits only.
- Postgres reads the password only when the volume is empty. Changing it later
  means changing it inside Postgres too.
- `helm uninstall` keeps the PVC. Delete it by hand to start with an empty DB:
  `kubectl delete pvc data-gearloan-postgres-0 -n gearloan`.
- The namespace uses Pod Security `restricted`; every pod here passes it.
