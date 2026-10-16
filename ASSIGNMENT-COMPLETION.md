# Assignment completion checklist

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

Status key:
- ✅ **done** – done and checked with a real run
- 🟡 **partial** – part of it is still missing
- ⏳ **pending** – not run yet (waiting on something)
- 👤 **student** – only I can do it (narration, form submission, console login)

Sessions 1–8 were done earlier and aren't listed here.

## Sessions 9–20

| Session | Requirement | Where | How it was checked | Status |
|---|---|---|---|---|
| 9 | Install Minikube, cluster status, architecture notes, Kubernetes Basics hands-on | [09](submissions/09-kubernetes-fundamentals/README.md) | `minikube status`, `kubectl get nodes`, tutorial modules 1–6 on nginx | ✅ |
| 10 | Rolling update, blue-green, canary, recreate | [10](submissions/10-kubernetes-core-objects/README.md) | live watch + curl loops during each update | ✅ |
| 10 | Pod lifecycle (12 cases) | [10](submissions/10-kubernetes-core-objects/README.md) | snapshots at 8 s / 33 s / 68 s + describe/logs | ✅ |
| 11 | ClusterIP, NodePort, LoadBalancer, ExternalName, Headless | [11](submissions/11-kubernetes-services/README.md) | curl/nslookup for each; `minikube tunnel` for the LoadBalancer | ✅ |
| 11 | Object comparisons, `fqdn/README.md`, `coredns/README.md` | [11](submissions/11-kubernetes-services/README.md) | written + real DNS lookups | ✅ |
| 12 | ConfigMap, Secret, Ingress, Ingress vs controller, troubleshooting | [12](submissions/12-kubernetes-config-ingress/README.md) | values checked inside Pods; path + host routing via ingress-nginx; 2 before/after drills | ✅ |
| 13 | Volumes doc, HPA under real load, mini project, probes | [13](submissions/13-storage-hpa-probes/README.md) | metrics-server, 1→3→5→1 and 2→4→2 scaling; PVC survives Pod delete; readiness/liveness break and recover | ✅ |
| 14 | kubectl commands + 9 issue types + mini project | [14](submissions/14-troubleshooting/README.md) | broken.yaml → investigate → fixed.yaml → verify for each | ✅ |
| 15 | All Helm commands, install→upgrade→upgrade→rollback, notes-chart | [15](submissions/15-helm/README.md) | Helm v4.3.1 real output | ✅ |
| 16 | CI/CD demo: app, Dockerfile, CI + CD, artifacts, secrets | [16](submissions/16-cicd/README.md) | [green run 38961008859](https://github.com/citruswhale/Shell_Scripting_Basics/actions/runs/38961008859) | ✅ |
| 17 | Build, test, SAST, SCA, secret scan, image scan, gate, push, deploy | [17](submissions/17-devsecops/README.md) | [green run 38961008905](https://github.com/citruswhale/Shell_Scripting_Basics/actions/runs/38961008905) | ✅ |
| 18 | Terraform S3 demo: init/fmt/validate/plan/apply/show/output/destroy | [18](submissions/18-terraform/README.md) | code + plan ready; apply waiting for AWS approval | ⏳ |
| 18 | AWS research READMEs (IAM, EC2, S3, VPC, DynamoDB/RDS) | [18/aws-services](submissions/18-terraform/aws-services/) | written | ✅ |
| 19 | VPC/subnet/SG/EC2/S3 project with plan/apply/destroy | [19](submissions/19-cloud/README.md) | code + plan ready; apply waiting for AWS approval | ⏳ |
| 20 | Monitoring demo, observability doc, GitOps demo | [20](submissions/20-monitoring-gitops/README.md) | Prometheus targets UP, live Grafana, alert fired and resolved, Argo CD sync + self-heal | ✅ |

## Session 21 – capstone (rubric modules)

| Module | Requirement | Where | Evidence | Status |
|---|---|---|---|---|
| M1 | FastAPI `/health`, CRUD endpoints, PostgreSQL + Alembic, React UI, responsive | [`backend/`](session21-python/backend/), [`frontend/`](session21-python/frontend/) | [browser test](session21-python/evidence/browser-test/), desktop/mobile screenshots | ✅ |
| M2 | pytest, ≥5 tests on ≥3 endpoints, test DB, conftest/pytest.ini | [`backend/tests/`](session21-python/backend/tests/) | 28 passed on an isolated `gearloan_test` DB | ✅ |
| M3 | Public repo, meaningful commits (≥10), .gitignore | this repo | [commit history screenshot](session21-python/evidence/screenshots/github-commit-history.png) | ✅ |
| M4 | Backend Dockerfile, multi-stage frontend, non-root, compose up --build | [`docker-compose.yml`](session21-python/docker-compose.yml) | [compose output](session21-python/evidence/local/compose-up.txt): uid 10001 / 101 | ✅ |
| M5 | Workflow on push to main, pytest job, frontend build, both images, GHCR, SHA tags | [`capstone-ci-cd.yml`](.github/workflows/capstone-ci-cd.yml) | [green run 38964516947](https://github.com/citruswhale/Shell_Scripting_Basics/actions/runs/38964516947): 15 jobs; GHCR tags `22d5492` + full SHA ([screenshot](session21-python/evidence/screenshots/ghcr-gearloan-backend.png)) | ✅ |
| M6 | Trivy on both images, fails on HIGH/CRITICAL, explanation | same workflow | Trivy gate on both images: Debian 13.7 (backend) and Alpine 3.24.2 (frontend), 0 HIGH/CRITICAL with a fix ([log](session21-python/evidence/ci/github-actions-run-38964516947.txt)) | ✅ |
| M7 | Terraform VPC (2 public subnets) + EKS node group, init/plan/destroy, tfvars.example | [`terraform/`](session21-python/terraform/) | validate + plan pass (45 resources); apply waiting for AWS approval | ⏳ |
| M8 | k8s/namespace.yaml, Helm chart, 2+2 replicas, ClusterIP, Ingress `/` + `/api`, pods Running | [`helm/`](session21-python/helm/), [`k8s/`](session21-python/k8s/) | works on Minikube ([evidence](session21-python/evidence/k8s-local/)); EKS run pending | 🟡 |
| M9 | /metrics, Prometheus scraping, Grafana with live panel | [`monitoring/`](session21-python/monitoring/) | targets UP + live dashboard on Minikube ([Session 20](submissions/20-monitoring-gitops/README.md)); EKS run pending | 🟡 |
| M10 | Root README, demo video, PPT/PDF slides | [`session21-python/README.md`](session21-python/README.md), `demo/` | not written yet | ⏳ |

## Things only I can do
- 👤 Approve the AWS spending, and log in to the AWS Console for the VPC/EKS screenshots while the cluster is running.
- 👤 Record or narrate the presentation video (the brief requires my own presentation).
- 👤 Submit the form.
