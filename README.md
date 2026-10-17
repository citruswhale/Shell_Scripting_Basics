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
| 9 | Kubernetes fundamentals | [`Sesh 9 Kubernetes Fundamentals`](Sesh%209%20Kubernetes%20Fundamentals/README.md) |
| 10 | Pods, ReplicaSets & Deployments | [`Sesh 10 Pods ReplicaSets Deployments`](Sesh%2010%20Pods%20ReplicaSets%20Deployments/README.md) |
| 11 | Kubernetes networking & Services | [`Sesh 11 Kubernetes Services`](Sesh%2011%20Kubernetes%20Services/README.md) |
| 12 | Ingress, ConfigMaps & Secrets | [`Sesh 12 Ingress ConfigMaps Secrets`](Sesh%2012%20Ingress%20ConfigMaps%20Secrets/README.md) |
| 13 | Storage, HPA & probes | [`Sesh 13 Storage HPA Probes`](Sesh%2013%20Storage%20HPA%20Probes/README.md) |
| 14 | Kubernetes troubleshooting | [`Sesh 14 Kubernetes Troubleshooting`](Sesh%2014%20Kubernetes%20Troubleshooting/README.md) |
| 15 | Helm | [`Sesh 15 Helm`](Sesh%2015%20Helm/README.md) |
| 16 | CI/CD & GitHub Actions | [`Sesh 16 CICD GitHub Actions`](Sesh%2016%20CICD%20GitHub%20Actions/README.md) |
| 17 | CI/CD & DevSecOps | [`Sesh 17 DevSecOps`](Sesh%2017%20DevSecOps/README.md) |
| 18 | Terraform & IaC | [`Sesh 18 Terraform`](Sesh%2018%20Terraform/README.md) |
| 19 | Cloud & Terraform in action | [`Sesh 19 Cloud Terraform`](Sesh%2019%20Cloud%20Terraform/README.md) |
| 20 | Monitoring, observability & GitOps | [`Sesh 20 Monitoring GitOps`](Sesh%2020%20Monitoring%20GitOps/README.md) |
| 21 | Final DevOps project | [`session21-python`](session21-python/README.md) |

Reused material and tools: [`SOURCES.md`](SOURCES.md)

## Pipelines
GitHub Actions workflows are in [`.github/workflows/`](.github/workflows/):
- `s16-cicd.yml` – Session 16 demo
- `s17-devsecops.yml` – Session 17 demo
- `capstone-ci-cd.yml` – GearLoan

Each one only runs when its own folder changes.
