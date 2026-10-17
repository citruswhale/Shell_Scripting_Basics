# GearLoan – presentation outline and demo script

**Srinidhi Narendran · 24BCS10037 · Batch B**

Target length is about 10–12 minutes. Show the slides first ([`demo/`](demo/)), then do the live walkthrough in the order the rubric lists. The lines in *italics* are what I plan to say, in my own words.

---

## Part 1 – Slides (≈ 3 min)

| # | Slide | What I say |
|---|---|---|
| 1 | Title | *"GearLoan: an equipment lending app for a college club, built and run with a full DevOps pipeline."* |
| 2 | Problem and app | *Clubs lend cameras and laptops on paper. GearLoan tracks items, loans, due dates and overdue gear, with real rules: no double lending, max 3 loans per person, damaged returns go to maintenance.* |
| 3 | Tech stack | FastAPI + PostgreSQL + Alembic, React + Vite, Docker, GitHub Actions, GHCR, Trivy, Terraform, EKS, Helm, Argo CD, Prometheus, Grafana |
| 4 | Architecture | walk through the diagram: GitHub → Actions → GHCR → Git (values-eks.yaml) → Argo CD → EKS → ingress → frontend/backend → Postgres on EBS; Prometheus scraping the backend |
| 5 | CI/CD flow | tests and scans in parallel → build once → Trivy gate → test deploy in kind → push the same image → bot updates the tag → Argo CD deploys |
| 6 | Infrastructure | Terraform: VPC with 2 public subnets in 2 AZs, no NAT to save cost, EKS 1.37, 2 × m7i-flex.large, EBS CSI driver; about $0.33/hour; destroyed after the demo |
| 7 | Kubernetes setup | Helm chart: 2+ replicas each, HPA, probes, limits, ClusterIP, ingress `/` and `/api`, StatefulSet + PVC, Secret not in Git, restricted Pod Security |
| 8 | Observability | `/metrics` → ServiceMonitor → Prometheus → my Grafana dashboard; alert rules; the alert fired and resolved in testing |
| 9 | Security | non-root images, Bandit, pip-audit/npm audit, Gitleaks over the whole history, Trivy gate; least-privilege workflow permissions |
| 10 | Key learnings | *Wait for readiness instead of guessing; kube-proxy needs a moment after a Service is created; Grafana 13 needs ~700 MiB; build amd64 for EKS; never let GitOps fight the HPA over replicas; a clean scan isn't proof of security; always destroy cloud labs.* |

## Part 2 – Live walkthrough (≈ 8 min)

1. **Codebase overview (1 min).** Open the repo on GitHub and show `session21-python/`: `backend/app/routers`, `alembic/versions/0001_initial.py`, `tests/`, the `frontend/` Dockerfile (multi-stage), `helm/gearloan/templates`, `terraform/`, `monitoring/`.
   *Design decisions: route templates as metric labels, advisory lock for migrations, no `replicas:` when the HPA is on.*
2. **Terraform (1 min).** Show `terraform plan` output (`Plan: 45 to add`), the apply output, and then the **AWS Console**: VPC `gearloan-vpc` with 2 public subnets, EKS `gearloan-eks` Active with 2 nodes.
3. **Kubernetes (1 min).**
   ```bash
   kubectl --context gearloan-eks get nodes
   kubectl --context gearloan-eks get pods,svc,ingress,hpa,pvc -n gearloan
   helm --kube-context gearloan-eks list -A
   ```
   Then open the app through the Ingress (node public IP, port 30080; the account cannot create a load balancer yet).
4. **CI/CD live change (3 min, the main demo).**
   - Change something visible: bump `appVersion` in `helm/gearloan/Chart.yaml` (shown in the app header and `/api/info`), or edit a heading in the frontend.
   - `git commit -am "..." && git push`
   - Open **Actions** and watch the jobs go green: tests → scans → build → Trivy → kind deploy test → push → GitOps update.
   - Open **GHCR** and show the new SHA tag.
5. **Argo CD (1 min).** The Argo CD UI shows `gearloan` going OutOfSync → Synced to the bot's commit, and the new ReplicaSet rolling out. Reload the app and the **new version is live**.
6. **Prometheus (30 s).** Status → Targets: `gearloan-backend` 2/2 **UP**.
7. **Grafana (30 s).** The GearLoan dashboard with live request rate, latency and loan counters.
8. **Wrap-up.** *Everything is torn down with `terraform destroy` after recording; the repo has every command to recreate it.*

## Recording tips
- Record with **Cmd + Shift + 5 → Record Entire Screen** (with the microphone on), or QuickTime.
- Before starting: zoom the terminal font, close other tabs, and open the Argo CD, Grafana and Prometheus port-forwards in separate terminal tabs.
- Save as MP4 in `session21-python/demo/`. GitHub's limit is 100 MB per file; if it's bigger, upload it to the repo's **Releases** as an asset and link it here.
