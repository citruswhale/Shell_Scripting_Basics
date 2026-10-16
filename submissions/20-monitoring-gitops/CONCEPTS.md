# Monitoring, Observability and GitOps

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

Example app: GearLoan (FastAPI backend with `/metrics`, React, PostgreSQL),
installed with Helm, monitored by kube-prometheus-stack, deployed by Argo CD
from `citruswhale/Shell_Scripting_Basics`.

## Task 1: Monitoring

Monitoring means collecting known numbers and messages about a system and
raising an alarm when something crosses a limit.

### 1.1 Metrics

A metric is a number measured over time, with labels.

```
http_requests_total{method="POST", path="/loans", status="201"}  42
```

| Prometheus type | Meaning | GearLoan example |
|-----------------|---------|------------------|
| Counter | Only goes up (resets on restart) | `gearloan_loans_created_total` |
| Gauge | Goes up and down | Number of DB connections in use |
| Histogram | Counts values into buckets | `http_request_duration_seconds` |

Prometheus **pulls** (scrapes) `/metrics` on a fixed interval. `rate()` turns a counter into a per-second speed.

### 1.2 Logs

A log is a text line written by the app when something happens.

Metrics tell you **that** errors went up. Logs tell you **which** request failed and why.

### 1.3 Alerts

An alert is a rule that checks a metric and notifies someone when it stays
bad for some time. Prometheus checks the rule and Alertmanager sends the
message (email, Slack, etc).

### 1.4 CPU utilization

How much CPU a container uses compared to what it asked for.

```promql
# CPU cores used by each GearLoan pod (5 min average)
sum by (pod) (
  rate(container_cpu_usage_seconds_total{namespace="gearloan", container!=""}[5m])
)
```

### 1.5 Memory utilization

```promql
# Working set memory per pod in MiB
sum by (pod) (
  container_memory_working_set_bytes{namespace="gearloan", container!=""}
) / 1024 / 1024
```

Working set is the number compared with the memory limit for OOM kills.

### 1.6 Application health

| Signal | PromQL |
|--------|--------|
| Request rate | `sum(rate(http_requests_total[5m]))` |
| Error ratio | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| p95 latency | `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` |
| Pods ready | `kube_pod_status_ready{namespace="gearloan", condition="true"}` |
| Target up | `up{job="gearloan-backend"}` |
| Business metric | `increase(gearloan_loans_created_total[1h])` |

### 1.7 Example alert rule

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: gearloan-alerts
  namespace: gearloan
  labels:
    release: kube-prometheus-stack     # so Prometheus picks it up
spec:
  groups:
    - name: gearloan.rules
      rules:
        - alert: GearLoanHighErrorRate
          expr: |
            sum(rate(http_requests_total{namespace="gearloan", status=~"5.."}[5m]))
              /
            sum(rate(http_requests_total{namespace="gearloan"}[5m])) > 0.05
          for: 5m                      # must stay true for 5 minutes
          labels:
            severity: warning
          annotations:
            summary: "GearLoan backend 5xx rate above 5%"
```

## Task 2: Observability

### 2.1 Monitoring vs observability

| Monitoring | Observability |
|------------|---------------|
| Watches things you already know can break | Helps you find out things you did not expect |
| "Is CPU above 80%?" | "Why are only loan requests from one page slow?" |
| Dashboards and alerts | Metrics, logs and traces that can be joined and searched |

Monitoring is part of observability. One click can pass through many pods,
so you need data that lets you follow one request and ask new questions.

### 2.2 The three pillars

| Pillar | What it is | Answers | Example tool |
|--------|-----------|---------|--------------|
| Metrics | Numbers over time | What is wrong and how much? | Prometheus |
| Logs | Timestamped event text | What exactly happened? | Loki, ELK |
| Traces | Path of one request across services, split into spans | Where is the time spent? | Jaeger, Tempo |

### 2.3 Common tools

| Tool | Job |
|------|-----|
| Prometheus + Alertmanager | Scrapes and stores metrics, runs PromQL and alert rules, sends alerts |
| Grafana | Dashboards for Prometheus, Loki, Tempo and others |
| Loki | Log storage that indexes labels only, queried with LogQL |
| ELK (Elasticsearch, Logstash, Kibana) | Full-text log search and dashboards |
| OpenTelemetry | Standard SDKs and Collector to produce and send metrics, logs and traces |
| Jaeger / Tempo | Trace storage and trace viewer |

### 2.4 Kubernetes observability

**metrics-server vs Prometheus**

| | metrics-server | Prometheus |
|-|----------------|------------|
| Data | Current CPU and memory only, kept in memory | Any metric, stored with history |
| Used by | `kubectl top`, HPA | Grafana, alerts, PromQL |

**Parts installed by kube-prometheus-stack**

| Part | Gives |
|------|-------|
| node-exporter | Node metrics: CPU, memory, disk, network (`node_*`) |
| kube-state-metrics | State of Kubernetes objects (`kube_pod_status_ready`, `kube_deployment_status_replicas`) |
| kubelet / cAdvisor | Container metrics (`container_cpu_usage_seconds_total`) |
| Prometheus Operator | Turns `ServiceMonitor` and `PrometheusRule` objects into Prometheus config |

**ServiceMonitor** tells Prometheus which Service to scrape:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: gearloan-backend
  namespace: gearloan
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: gearloan-backend
  endpoints:
    - port: http          # named port on the Service
      path: /metrics
      interval: 15s
```

**Quick kubectl checks**

```bash
kubectl top nodes
kubectl top pods -n gearloan
kubectl logs deploy/gearloan-backend -n gearloan --tail=50
kubectl get events -n gearloan --sort-by=.lastTimestamp
kubectl describe pod <pod> -n gearloan        # probes, restarts, OOMKilled
```

## Task 3: GitOps

### 3.1 What is GitOps

GitOps is a way to run deployments where the Git repo holds the full wanted
state of the system, and an agent inside the cluster keeps the cluster equal
to what is in Git.

### 3.2 Four main ideas

| Idea | Meaning |
|------|---------|
| Git is the source of truth | The repo says what should run. Not someone's terminal. |
| Declarative configuration | You describe the end state (YAML, Helm values), not the steps. |
| Versioned and reviewed | Every change is a commit or PR. Rollback is `git revert`. |
| Continuous reconciliation | An agent keeps comparing cluster vs Git and fixes the difference. |

### 3.3 GitOps workflow

```
 Developer --PR (new image tag)--> GitHub repo --merge--> master
                                                            |
                         Argo CD polls Git or gets webhook  |
                                                            v
 +---------------- Kubernetes cluster ------------------------+
 | Argo CD: compare Git (desired) with cluster (live)         |
 |   OutOfSync -> apply diff -> wait for Synced + Healthy     |
 | gearloan namespace: backend, frontend, postgres            |
 +------------------------------------------------------------+
```

### 3.4 Push vs pull deployment

| | Push (classic CI/CD) | Pull (GitOps) |
|-|----------------------|---------------|
| Who applies | CI runner runs `kubectl` / `helm upgrade` | Agent inside the cluster |
| Cluster credentials | Stored in CI secrets | Stay inside the cluster |
| Drift fixed? | No, only at next pipeline run | Yes, all the time |
| Example | GitHub Actions job with a kubeconfig | Argo CD, Flux |

### 3.5 Argo CD terms

| Term | Meaning |
|------|---------|
| Application | Argo CD object: which repo, path and revision, and which cluster and namespace |
| Sync | Apply Git to the cluster. Status is `Synced` or `OutOfSync` |
| Health | `Healthy`, `Progressing`, `Degraded`, `Missing` |
| Drift | Live state is different from Git (for example someone ran `kubectl edit`) |
| Self-heal | Argo CD undoes drift on its own |
| Prune | Deletes objects that were removed from Git |

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: gearloan
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/citruswhale/Shell_Scripting_Basics.git
    targetRevision: master
    path: helm/gearloan                   # example path to the Helm chart
  destination:
    server: https://kubernetes.default.svc
    namespace: gearloan
  syncPolicy:
    automated:
      prune: true        # delete what was removed from Git
      selfHeal: true     # undo manual changes
    syncOptions:
      - CreateNamespace=true
```

### 3.6 Who owns replicas when an HPA exists

The HPA changes `spec.replicas` on the Deployment. If the chart also sets
`replicas: 2`, Argo CD sees a difference and, with self-heal on, sets it
back to 2. The HPA and Argo CD then fight each other.

**Option A: leave replicas out of the chart when HPA is on (preferred)**

```yaml
# templates/deployment.yaml
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
```

**Option B: tell Argo CD to ignore the field**

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      name: gearloan-backend
      jsonPointers:
        - /spec/replicas
  syncPolicy:
    syncOptions:
      - RespectIgnoreDifferences=true   # also skip it during sync
```

Rule: the HPA owns the replica count, Git owns everything else.

