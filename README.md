# DevOps Course Work – Srinidhi Narendran

**Roll No:** 24BCS10037 · **Batch:** B · **GitHub:** [citruswhale](https://github.com/citruswhale)

All my DevOps homework and my final capstone project in one repository.

## Final capstone – GearLoan
**[`session21-python/`](session21-python/README.md)** – an equipment lending app (FastAPI + PostgreSQL + React) with the full DevOps setup: Docker, GitHub Actions CI/CD with security scans, GHCR, Terraform (AWS VPC + EKS), Helm, Argo CD, and Prometheus + Grafana.

## Sessions

| Session | Topic | Folder |
|---|---|---|
| 1 & 2 | Linux fundamentals | [`Sesh 2 Linux`](Sesh%202%20Linux/README.md) |
| 3 | Shell scripting | [`Sesh 3 Shell Scripting`](Sesh%203%20Shell%20Scripting/README.md) |
| 4 | Networking | [`Sesh 4 Networking`](Sesh%204%20Networking/README.md) |
| 5 | Git & GitHub | [`Sesh 5 Git Github`](Sesh%205%20Git%20Github/README.md) |
| 6 & 7 | Docker fundamentals & images | [`Sesh 6-7 Dockerfiles Images`](Sesh%206-7%20Dockerfiles%20Images/README.md) |
| 8 | Docker networking & volumes | [`Sesh 8 Docker Network`](Sesh%208%20Docker%20Network/README.md) |
| 9 | Kubernetes fundamentals | [`submissions/09-kubernetes-fundamentals`](submissions/09-kubernetes-fundamentals/README.md) |
| 10 | Pods, ReplicaSets & Deployments | [`submissions/10-kubernetes-core-objects`](submissions/10-kubernetes-core-objects/README.md) |
| 11 | Kubernetes networking & Services | [`submissions/11-kubernetes-services`](submissions/11-kubernetes-services/README.md) |
| 12 | Ingress, ConfigMaps & Secrets | [`submissions/12-kubernetes-config-ingress`](submissions/12-kubernetes-config-ingress/README.md) |
| 13 | Storage, HPA & probes | [`submissions/13-storage-hpa-probes`](submissions/13-storage-hpa-probes/README.md) |
| 14 | Kubernetes troubleshooting | [`submissions/14-troubleshooting`](submissions/14-troubleshooting/README.md) |
| 15 | Helm | [`submissions/15-helm`](submissions/15-helm/README.md) |
| 16 | CI/CD & GitHub Actions | [`submissions/16-cicd`](submissions/16-cicd/README.md) |
| 17 | CI/CD & DevSecOps | [`submissions/17-devsecops`](submissions/17-devsecops/README.md) |
| 18 | Terraform & IaC | [`submissions/18-terraform`](submissions/18-terraform/README.md) |
| 19 | Cloud & Terraform in action | [`submissions/19-cloud`](submissions/19-cloud/README.md) |
| 20 | Monitoring, observability & GitOps | [`submissions/20-monitoring-gitops`](submissions/20-monitoring-gitops/README.md) |
| 21 | Final DevOps project | [`session21-python`](session21-python/README.md) |

Reused material and tools: [`SOURCES.md`](SOURCES.md)

## Pipelines
GitHub Actions workflows are in [`.github/workflows/`](.github/workflows/):
- `s16-cicd.yml` – Session 16 demo
- `s17-devsecops.yml` – Session 17 demo
- `capstone-ci-cd.yml` – GearLoan

Each one only runs when its own folder changes.
