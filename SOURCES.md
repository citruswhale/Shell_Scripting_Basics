# Sources

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

What I used from other places, and how.

## Course material
- **Instructor repository:** https://github.com/Nency-Ravaliya/devops-heros (MIT License, © 2026 Nensi Ravaliya)
  - Session 14 mini project: `deployment.yaml`, `service.yaml` and `broken-pod.yaml` are copied from `session-14-kubernetes-troubleshooting/mini-project/` and used as given.
  - Session 15 mini project: the `notes-chart/` Helm chart is copied from `session-15-helm/mini-project/`.
  - Session 13 mini project: the namespace/PVC/deployment/service/HPA files follow `session-13-storage-hpa-probes/mini-project/` (same names and settings).
  - Session 12 troubleshooting: the idea for the "trailing newline in a base64 Secret" exercise comes from `session-12-ingress-configmaps-secrets/troubleshooting/secret-base64-gotcha.md`. I rebuilt it with my own PostgreSQL and client files.
  - Session 20 mini project: the folder layout (`app/` + an Argo CD Application kept outside it) follows `session20-monitoring-observability-gitops/08-mini-project/`.
  - Session 21: the rubric in `session21-python/GRADING.md`. My capstone app (**GearLoan**) and all its code are my own; it is not based on the TaskBoard example.
- **Homework document:** the official homework Google Doc for the task lists.

Everything else in the `Sesh 9` to `Sesh 20` folders and `session21-python/` (apps, YAML, Helm charts, Terraform, workflows, dashboards, scripts and READMEs) was written for this repo.

## Public images, charts and tools used
- Container images: `nginx`, `busybox`, `python`, `node`, `postgres`, `curlimages/curl`, `hashicorp/http-echo`, `registry.k8s.io/e2e-test-images/agnhost`, `nginxinc/nginx-unprivileged`.
- Helm charts: `prometheus-community/kube-prometheus-stack`, `podinfo/podinfo` (Session 15 practice), Argo CD official install manifests.
- Terraform modules: `terraform-aws-modules/vpc/aws`, `terraform-aws-modules/eks/aws`.
- Tools: Minikube, kind, kubectl, Helm, Terraform, AWS CLI, Trivy, Gitleaks, Bandit, Semgrep, pip-audit, Playwright (headless Chromium, used to capture the UI screenshots and run the browser test).

## Official documentation I read
Kubernetes (kubernetes.io/docs), Helm (helm.sh/docs), Docker (docs.docker.com), GitHub Actions and Packages (docs.github.com), Terraform (developer.hashicorp.com/terraform), AWS EKS / S3 / VPC / IAM user guides, Prometheus, Grafana, Argo CD and Trivy docs.

## About the screenshots
- **Browser screenshots** (the GearLoan UI, Prometheus, Grafana, Alertmanager, Argo CD, GitHub Actions pages) were taken automatically with Playwright's headless Chromium from the live pages while they were running.
- **Terminal-style images** (for example `pytest-28-passed.png`) are **rendered from the captured command output**, and they say so in their title bar. The raw text files are kept next to them.
