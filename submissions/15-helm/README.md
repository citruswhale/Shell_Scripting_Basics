# Session 15 – Helm

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

Helm is a package manager for Kubernetes. A **chart** is a folder of YAML templates plus default values. Installing a chart creates a **release**, and every upgrade or rollback adds a new **revision**, so you can always go back.

Setup: Helm **v4.3.1**, Minikube `devops-lab` (Kubernetes v1.37), namespace `s15`. Raw output is in [`outputs/`](outputs/).

| Task | Folder | Log |
|---|---|---|
| 1. Helm commands | [`01-helm-commands/`](01-helm-commands/) | [`01-helm-commands.txt`](outputs/01-helm-commands.txt) |
| 2. Rollback workflow | [`02-rollback/`](02-rollback/) | [`02-rollback.txt`](outputs/02-rollback.txt) |
| 3. Mini project (notes-chart) | [`03-mini-project/`](03-mini-project/) | [`03-mini-project.txt`](outputs/03-mini-project.txt) |

---

## Task 1 – Helm commands

| Command | What it does | What I saw |
|---|---|---|
| `helm create gearloan-demo` | Makes a starter chart | Chart.yaml, values.yaml, templates for deployment, service, ingress, hpa, httproute, serviceaccount, a test hook |
| `helm lint` | Checks a chart for mistakes | `1 chart(s) linted, 0 chart(s) failed` (only "icon is recommended") |
| `helm template` | Renders the YAML **without** installing | Service, ServiceAccount, Deployment, test Pod |
| `helm repo add / update / list` | Adds chart repositories | added `podinfo` and `prometheus-community` |
| `helm search repo` | Searches the added repos | `podinfo/podinfo 6.15.0` · `kube-prometheus-stack 92.10.1` |
| `helm search hub` | Searches Artifact Hub (all public charts) | several `argo-cd` charts |
| `helm show chart / values` | Chart info and default values before installing | `ui.message: ""`, `replicaCount: 1` |
| `helm install` | Installs a release | `demo-podinfo`, `STATUS: deployed`, `REVISION: 1` |
| `helm list` | Lists releases in a namespace | `demo-podinfo  s15  1  deployed  podinfo-6.15.0` |
| `helm status` | Release status and its resources | Service, Deployment `2/2`, 2 Pods |
| `helm get values / manifest / notes / metadata` | What was actually installed | my values, the 2 rendered objects, the NOTES, `APPLY_METHOD: server-side apply` |
| `helm upgrade` | Changes a release | `REVISION: 2`, 3 Pods, new message |
| `helm history` | All revisions | 1 superseded, 2 deployed |
| `helm rollback` | Goes back to an older revision | `Rollback was a success! Happy Helming!` → revision 3 = "Rollback to 1" |
| `helm uninstall` | Removes the release and everything it made | `release "demo-podinfo" uninstalled` |

Some real output:
```text
$ helm install demo-podinfo podinfo/podinfo -n s15 --set replicaCount=2 --set ui.message="Hello from Srinidhi (24BCS10037)" --wait
NAME: demo-podinfo
NAMESPACE: s15
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete

$ kubectl exec -n s15 client -- curl -s http://demo-podinfo:9898
  "hostname": "demo-podinfo-67c9fb8679-kt9b7",
  "version": "6.15.0",
  "message": "Hello from Srinidhi (24BCS10037)",

$ helm get values demo-podinfo -n s15
USER-SUPPLIED VALUES:
replicaCount: 2
ui:
  message: Hello from Srinidhi (24BCS10037)

$ helm upgrade demo-podinfo podinfo/podinfo -n s15 --reuse-values --set replicaCount=3 --set ui.message="Upgraded by Srinidhi" --wait
Release "demo-podinfo" has been upgraded. Happy Helming!
REVISION: 2

$ helm rollback demo-podinfo 1 -n s15 --wait
Rollback was a success! Happy Helming!

$ helm history demo-podinfo -n s15
REVISION  STATUS      CHART           DESCRIPTION
1         superseded  podinfo-6.15.0  Install complete
2         superseded  podinfo-6.15.0  Upgrade complete
3         deployed    podinfo-6.15.0  Rollback to 1
  "message": "Hello from Srinidhi (24BCS10037)",      <- back to the revision 1 message
```
Things I noticed:
- A rollback doesn't delete history. It adds a **new** revision that copies an old one.
- `--reuse-values` keeps the values from the last release; without it, Helm starts again from the chart defaults.
- In Helm 4, `helm list --all` is gone. `helm list` shows the current releases.

---

## Task 2 – Rollback workflow

My own small chart [`02-rollback/gear-catalog/`](02-rollback/gear-catalog/) shows a message from `values.yaml`, so I can see which revision is live. The values files are [`values-v2.yaml`](02-rollback/values-v2.yaml) and [`values-v3.yaml`](02-rollback/values-v3.yaml).

```text
Install (v1) -> Verify -> Upgrade (v2) -> Verify -> Upgrade again (v3) -> Verify -> Rollback to 2 -> Verify
```

For each "verify" I waited 10 seconds, listed the Pods, and sent 6 requests to the Service:

| Step | Command | Revision | Pods | 6 requests returned |
|---|---|---|---|---|
| Install | `helm install catalog gear-catalog -n s15 --wait` | 1 | 2 Running | `6 GearLoan catalog v1 - cameras and laptops` |
| Upgrade | `helm upgrade catalog gear-catalog -f values-v2.yaml --wait` | 2 | 3 Running | `6 GearLoan catalog v2 - now with tripods and microphones` |
| Upgrade again | `helm upgrade catalog gear-catalog -f values-v3.yaml --wait` | 3 | 4 Running | `6 GearLoan catalog v3 - experimental search page` |
| Rollback | `helm rollback catalog 2 --wait` | 4 | 3 Running | `6 GearLoan catalog v2 - now with tripods and microphones` |

```text
$ helm history catalog -n s15
REVISION  STATUS      CHART               APP VERSION  DESCRIPTION
1         superseded  gear-catalog-0.1.0  1.0.0        Install complete
2         superseded  gear-catalog-0.1.0  1.0.0        Upgrade complete
3         superseded  gear-catalog-0.1.0  1.0.0        Upgrade complete
4         deployed    gear-catalog-0.1.0  1.0.0        Rollback to 2

$ helm get values catalog -n s15        # after the rollback
USER-SUPPLIED VALUES:
message: GearLoan catalog v2 - now with tripods and microphones
replicaCount: 3
```
The rollback brought back **both** the message and the replica count (4 → 3), because it restores the whole set of values from revision 2. The Pod hash after the rollback (`catalog-84b856947-...`) is the same as in revision 2, so Kubernetes re-used revision 2's ReplicaSet.

---

## Task 3 – Mini project: notes-chart

The instructor's chart is in [`03-mini-project/notes-chart/`](03-mini-project/notes-chart/): Chart.yaml, values.yaml (dev, 1 replica, nginx 1.24), values-prod.yaml (3 replicas, nginx 1.25), and templates for configmap, deployment and NodePort service.

| Step | What I ran | Result |
|---|---|---|
| Lint | `helm lint notes-chart` | `1 chart(s) linted, 0 chart(s) failed` |
| Render | `helm template notes-dev notes-chart` | ConfigMap `notes-dev-config` with `ENVIRONMENT: "development"`, NodePort 30090 |
| Install (dev) | `helm install notes-dev notes-chart -n s15` | REVISION 1, 1 Pod, `nginx version: nginx/1.24.0`, env `APP_NAME=notes-app ENVIRONMENT=development` |
| Upgrade to prod | `helm upgrade notes-dev notes-chart -f notes-chart/values-prod.yaml` | REVISION 2, **3 Pods**, `nginx/1.25.5`, `ENVIRONMENT=production` |
| Bad upgrade | `... --set image.tag=broken-tag-does-not-exist` | REVISION 3; the new Pod is `ImagePullBackOff`, the 3 old Pods keep running |
| Rollback | `helm rollback notes-dev 2` | `Rollback was a success! Happy Helming!` → 3 Pods on `nginx/1.25.5` |

```text
$ kubectl get pods -n s15 -l app=notes-dev        # after the bad upgrade
notes-dev-deploy-79b4dbdffd-4tt8g   0/1     ImagePullBackOff   0          25s
notes-dev-deploy-bbcc464b4-cl4bh    1/1     Running            0          26s
notes-dev-deploy-bbcc464b4-m7bw2    1/1     Running            0          27s
notes-dev-deploy-bbcc464b4-q4tsg    1/1     Running            0          37s

$ helm history notes-dev -n s15                   # after the rollback
REVISION  STATUS      CHART              DESCRIPTION
1         superseded  notes-chart-0.1.0  Install complete
2         superseded  notes-chart-0.1.0  Upgrade complete
3         superseded  notes-chart-0.1.0  Upgrade complete      <- the broken one
4         deployed    notes-chart-0.1.0  Rollback to 2
```
**Why the app never went down during the bad upgrade:** the Deployment's rolling update waits for the new Pod to be ready before removing old ones. The broken Pod never got ready, so the 3 healthy Pods kept serving.

Helm still marked revision 3 as `deployed`, because I didn't use `--wait`. With `--wait` (or `--atomic` / `--rollback-on-failure`), Helm would have marked it `failed` and rolled back by itself.

---

## What I learned
- Templates + values = the same chart for dev and prod. Only the values file changes.
- `helm template` and `helm lint` catch mistakes before anything reaches the cluster. They don't prove the app works, though; only a real install does.
- Always use `--wait` in scripts and CI, so a broken release is noticed.
- Every change is a revision, so a rollback is one command.

## Cleanup
```bash
helm uninstall notes-dev catalog -n s15
kubectl delete namespace s15
```
