# Session 10 – Kubernetes Pods, ReplicaSets & Deployments

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

I tried all 4 deployment strategies and 12 Pod lifecycle cases on my Minikube cluster (`devops-lab`, Kubernetes v1.37). Everything runs in a namespace called `s10`.

For the app I used `hashicorp/http-echo`. It is a tiny web server that replies with one line of text, so I can see exactly which version answered each request. To send traffic I used a small `client` Pod (curl image) inside the same namespace.

All raw output is in [`outputs/`](outputs/).

```bash
kubectl apply -f namespace.yaml
kubectl run client -n s10 --image=curlimages/curl:8.11.1 --restart=Never --command -- sleep 3600
```

## Folder layout

| Folder | What is in it |
|---|---|
| [`01-rolling-update/`](01-rolling-update/) | v1 and v2 Deployment + Service |
| [`02-blue-green/`](02-blue-green/) | blue Deployment, green Deployment, one Service |
| [`03-canary/`](03-canary/) | stable Deployment (4 Pods), canary Deployment (1 Pod), one Service |
| [`04-recreate/`](04-recreate/) | v1 and v2 Deployment with `strategy: Recreate` + Service |
| [`05-pod-lifecycle/`](05-pod-lifecycle/) | 12 small Pod YAMLs, one per lifecycle case |

---

## Task 1 – Deployment strategies

### 01. Rolling update

The Deployment has 4 replicas and this strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # at most 1 extra Pod during the update
    maxUnavailable: 0  # never go below 4 ready Pods
minReadySeconds: 3
```

**Steps**
```bash
kubectl apply -f 01-rolling-update/deployment-v1.yaml -f 01-rolling-update/service.yaml
kubectl apply -f 01-rolling-update/deployment-v2.yaml      # the update
kubectl rollout status deploy/web-rolling -n s10
kubectl get rs -n s10 -l app=web-rolling
kubectl rollout undo deploy/web-rolling -n s10            # rollback
```

**What I saw.** While the update ran I kept a watch on the Pods and a curl loop going (2 requests a second). Part of the watch:
```text
ADDED      web-rolling-764cfb56d-hf42g    0/1     Pending             0          0s     <- new v2 Pod
MODIFIED   web-rolling-764cfb56d-hf42g    1/1     Running             0          1s
MODIFIED   web-rolling-549b5898c9-q6r28   1/1     Terminating         0          18s    <- only then one v1 Pod goes
ADDED      web-rolling-764cfb56d-xm7cj    0/1     Pending             0          0s     <- next v2 Pod
...
```
And the curl loop:
```text
17:47:25 rolling update - version 1
17:47:26 rolling update - version 1
17:47:26 rolling update - version 2
17:47:28 rolling update - version 2
17:47:29 rolling update - version 1     <- old and new both answering
17:47:29 rolling update - version 2
...
17:47:38 rolling update - version 2
```
```text
$ kubectl get rs -n s10 -l app=web-rolling
NAME                     DESIRED   CURRENT   READY   AGE
web-rolling-549b5898c9   0         0         0       33s     <- old ReplicaSet kept (for rollback)
web-rolling-764cfb56d    4         4         4       19s     <- new ReplicaSet
```
- One new Pod came up first, then one old Pod went away, and this repeated 4 times.
- For about 10 seconds both versions answered, and **not a single request failed**.
- `kubectl rollout undo` brought back version 1 the same way.
- The old Pods show `Error` while terminating because http-echo exits with a non-zero code when it gets SIGTERM. The Pods were still removed normally.

Full log: [`outputs/01-rolling-update.txt`](outputs/01-rolling-update.txt)

### 02. Blue-green

Two full Deployments run at the same time: `web-blue` (v1) and `web-green` (v2), 2 Pods each. There is one Service, `web-bg`. Its selector picks the colour that gets traffic:

```yaml
selector:
  app: web-bg
  color: blue     # change to green to switch
```

**Steps**
```bash
kubectl apply -f 02-blue-green/
kubectl get pods -n s10 -l app=web-bg -L color
kubectl exec -n s10 client -- curl -s web-bg                       # BLUE
kubectl patch svc web-bg -n s10 -p '{"spec":{"selector":{"app":"web-bg","color":"green"}}}'
kubectl get endpointslices -n s10 -l kubernetes.io/service-name=web-bg
kubectl exec -n s10 client -- curl -s web-bg                       # GREEN
```

**What I saw**
```text
selector: {"app":"web-bg","color":"blue"}
web-bg-zj2ff   IPv4   8080   10.244.0.25,10.244.0.26      <- blue Pod IPs
BLUE - version 1

$ kubectl patch svc web-bg ... color=green
selector: {"app":"web-bg","color":"green"}
web-bg-zj2ff   IPv4   8080   10.244.0.28,10.244.0.27      <- green Pod IPs
```
**First try:** right after the patch the EndpointSlice already listed the green IPs, but my 4 curl requests still got `BLUE`. kube-proxy on the node had not updated its rules yet.

**Second try:** I patched to green again and sent 10 requests over 5 seconds. All 10 said `GREEN - version 2`.

So the switch is not instant to the millisecond, but it is a single change and there is no mix of versions. To roll back I just patch the selector back to `blue`, and the blue Pods are still running and ready.

Full log: [`outputs/02-blue-green.txt`](outputs/02-blue-green.txt)

### 03. Canary

Two Deployments share the same `app: web-canary` label:
- `web-stable`: 4 Pods (v1), label `track: stable`
- `web-canary`: 1 Pod (v2), label `track: canary`

The Service only selects `app: web-canary`, so it sends traffic to all 5 Pods. 1 out of 5 is about **20%** to the canary.

**Steps**
```bash
kubectl apply -f 03-canary/
kubectl get pods -n s10 -l app=web-canary -L track
kubectl exec -n s10 client -- sh -c 'for i in $(seq 1 500); do curl -s --max-time 2 web-canary || echo FAILED; done | sort | uniq -c'
```

**What I saw**
```text
web-canary-78c566c664-pwbjr   1/1   Running   canary
web-stable-5d66d85977-9btxj   1/1   Running   stable
web-stable-5d66d85977-jmrm4   1/1   Running   stable
web-stable-5d66d85977-xdtjb   1/1   Running   stable
web-stable-5d66d85977-zqmjx   1/1   Running   stable

    113 CANARY - version 2        <- 22.6%
    387 STABLE - version 1        <- 77.4%
```
- 113 out of 500 requests (22.6%) went to the canary, close to the 20% I expected, with 0 failures.
- It is not exactly 20% because kube-proxy picks a Pod at random for each connection. **The Pod ratio controls the split only roughly.** For an exact percentage you need something like an Ingress controller or a service mesh with traffic weights.
- In my first try I counted 200 requests just after the Pods started, and 6 came back empty. I re-ran it after all Pods were Ready, counting failures, and got the clean result above.
- To promote the canary I scaled `web-canary` to 4 and `web-stable` to 0. After that 50 out of 50 requests said `CANARY - version 2`.

Full log: [`outputs/03-canary.txt`](outputs/03-canary.txt)

### 04. Recreate

```yaml
strategy:
  type: Recreate
```

**Steps**
```bash
kubectl apply -f 04-recreate/deployment-v1.yaml -f 04-recreate/service.yaml
kubectl apply -f 04-recreate/deployment-v2.yaml
```

**Mistake on my first try:** I ran `kubectl apply -f 04-recreate/`. That applied v1 and v2 one after the other, so it went straight to v2 and I couldn't see the switch. I deleted the Deployment and did it again with only v1 first.

**What I saw (second try).** The watch shows all three v1 Pods (`6845d79c6`) going to Terminating before any v2 Pod (`9cf5767c9`) is even created:
```text
MODIFIED   web-recreate-6845d79c6-frbw4   1/1     Terminating   0          4s
MODIFIED   web-recreate-6845d79c6-6dgws   1/1     Terminating   0          4s
MODIFIED   web-recreate-6845d79c6-vx7wc   1/1     Terminating   0          4s
...
DELETED    web-recreate-6845d79c6-6dgws   0/1     Error         0          4s
ADDED      web-recreate-9cf5767c9-69sg5   0/1     Pending       0          0s     <- v2 only starts now
ADDED      web-recreate-9cf5767c9-6vpgg   0/1     Pending       0          0s
ADDED      web-recreate-9cf5767c9-v6rqx   0/1     Pending       0          0s
```
The curl loop shows the downtime:
```text
17:49:12 recreate - version 1
17:49:12 NO RESPONSE
17:49:14 NO RESPONSE
17:49:14 recreate - version 2
```
There were about 2 seconds with no answer at all. That is the price of Recreate. It is only worth it when two versions must never run together, for example when they can't share the same database schema.

Full log: [`outputs/04-recreate.txt`](outputs/04-recreate.txt)

### Strategy comparison

| Strategy | Downtime | Both versions at once? | Extra resources | Rollback |
|---|---|---|---|---|
| Rolling update | None (I saw 0 failures) | Yes, for a short time | +1 Pod (maxSurge) | `rollout undo` |
| Blue-green | None | No, traffic switches in one go | Double (both colours run) | Patch the selector back |
| Canary | None | Yes, on purpose | A few extra Pods | Scale the canary to 0 |
| Recreate | Yes (~2 s for me) | Never | None | Apply the old version |

---

## Task 2 – Pod lifecycle

I applied all 12 YAML files from [`05-pod-lifecycle/`](05-pod-lifecycle/) together and took snapshots of `kubectl get pods`. Then I checked each Pod with `describe`, `logs` and `-o jsonpath`.

```bash
kubectl apply -f 05-pod-lifecycle/
kubectl get pods -n s10
kubectl describe pod <name> -n s10
kubectl logs <name> -n s10
kubectl get pod <name> -n s10 -o jsonpath='{.status.phase}'
```

> **Note about my run:** my laptop's Docker VM paused twice while I was doing this. The first time it froze for so long that the whole run was useless, so I kept that log separately ([`outputs/05-pod-lifecycle-attempt1-vm-paused.txt`](outputs/05-pod-lifecycle-attempt1-vm-paused.txt)) and ran everything again. In the second run the first two snapshots are fine. The VM paused again before the third one, so it was taken at 20:09:27, about 8 minutes later than I planned. The states in it are still real.

**Snapshot ~8 seconds after apply (20:00:49)**
```text
NAME               READY   STATUS         RESTARTS     AGE
life-crashloop     0/1     Error          1 (6s ago)   8s
life-failed        0/1     Error          0            8s
life-imagepull     0/1     ErrImagePull   0            8s
life-init          0/1     Init:0/1       0            8s
life-liveness      1/1     Running        0            8s
life-multi         2/2     Running        0            8s
life-pending       0/1     Pending        0            8s
life-readiness     0/1     Running        0            8s
life-running       1/1     Running        0            8s
life-startup       0/1     Running        0            8s
life-succeeded     0/1     Completed      0            8s
life-termination   1/1     Running        0            8s
```

**Snapshot ~33 seconds after apply (20:01:14)**
```text
life-crashloop     0/1     Error          2 (28s ago)   33s
life-imagepull     0/1     ErrImagePull   0             33s
life-init          1/1     Running        0             33s     <- init finished
life-readiness     1/1     Running        0             33s     <- now ready
life-startup       1/1     Running        0             33s     <- startup probe passed
```

**Last snapshot (20:09:27, after the VM pause)**
```text
life-crashloop     0/1     Error              3 (45s ago)   67s
life-imagepull     0/1     ImagePullBackOff   0             67s
life-liveness      1/1     Running            1 (16s ago)   67s  <- restarted by liveness probe
life-pending       0/1     Pending            0             67s
```

### What each case showed

| # | File | What I saw | Why |
|---|---|---|---|
| 1 | `01-running.yaml` | `Running`, `1/1` | Normal nginx Pod. |
| 2 | `02-pending.yaml` | Stayed `Pending` the whole time | It asks for 50 CPUs. The scheduler said `0/1 nodes are available: 1 Insufficient cpu`. |
| 3 | `03-succeeded.yaml` | `Completed`, `phase=Succeeded exitCode=0` | The script ran, printed `done` and exited 0. With `restartPolicy: Never` it is not started again. |
| 4 | `04-failed.yaml` | `Error`, `phase=Failed exitCode=1` | It printed `something went wrong` and exited 1. Not restarted because of `restartPolicy: Never`. |
| 5 | `05-crashloopbackoff.yaml` | `Error` -> restarts 1, 2, 3 ... with `Back-off restarting failed container` | It exits 1 every time and `restartPolicy: Always` keeps starting it again, waiting longer each time (back-off). |
| 6 | `06-imagepullbackoff.yaml` | `ErrImagePull` first, then `ImagePullBackOff` | The tag `nginx:this-tag-does-not-exist` is `not found` on Docker Hub. The kubelet keeps retrying, slower each time. |
| 7 | `07-readiness.yaml` | `Running` but `0/1` at 8 s, `1/1` at 33 s | The container runs, but the readiness probe fails until `/tmp/ready` exists (after 20 s). While not ready it gets no Service traffic, and it is **not** restarted. |
| 8 | `08-liveness.yaml` | `RESTARTS 1` and the event `failed liveness probe, will be restarted` | After 15 s the health file is deleted, the probe fails 2 times, and the kubelet kills and restarts the container. |
| 9 | `09-startup.yaml` | `0/1` at 8 s, `1/1` at 33 s, 0 restarts | The startup probe failed 5 times while the app "booted" (25 s), but it allows up to 50 s, so it was never killed. The liveness probe only begins after startup succeeds. |
| 10 | `10-init-container.yaml` | `Init:0/1` -> `Running`, and the page says `made by init container` | The init container must finish (`Completed`) before nginx starts. It wrote the HTML file into a shared `emptyDir`. |
| 11 | `11-multi-container.yaml` | `2/2` ready, and the sidecar printed the nginx access log line | Two containers in one Pod share the same volume. The sidecar `log-reader` reads what `web` writes. |
| 12 | `12-termination.yaml` | Log: `app running` -> `got SIGTERM, cleaning up` -> `cleanup done`; delete took 5 s | On delete, Kubernetes sends SIGTERM first. My `trap` cleaned up for 5 s and exited, well inside the 20 s grace period, so it never needed a SIGKILL. |

Some useful outputs:
```text
$ kubectl describe pod life-pending -n s10
  Warning  FailedScheduling  default-scheduler  0/1 nodes are available: 1 Insufficient cpu.

$ kubectl describe pod life-imagepull -n s10
  Warning  Failed   kubelet  Failed to pull image "nginx:this-tag-does-not-exist": ... not found
  Warning  Failed   kubelet  Error: ImagePullBackOff

$ kubectl describe pod life-liveness -n s10
  Normal   Killing    kubelet  Container app failed liveness probe, will be restarted
  Warning  Unhealthy  kubelet  Liveness probe failed:

$ kubectl logs life-init -n s10 -c wait-a-bit
init: preparing files

$ kubectl logs -f life-termination -n s10      # while I ran kubectl delete pod
app running
got SIGTERM, cleaning up
cleanup done
```

**Small thing I noticed:** `kubectl logs life-crashloop --previous` said `unable to retrieve container logs`. The container crashes so often that the old one had already been cleaned up. `kubectl describe` and the restart count were more useful there.

### Pod phases in short
- **Pending** – accepted, but not running yet: waiting for a node, or still pulling the image or running init containers.
- **Running** – at least one container is running. That does **not** mean ready; check the READY column.
- **Succeeded** – all containers exited with 0 and won't restart.
- **Failed** – all containers stopped and at least one exited with an error.
- **Unknown** – the node can't be reached.

`CrashLoopBackOff`, `ImagePullBackOff` and `ErrImagePull` are not phases. They are *reasons* a container is waiting.

### Probes in short
| Probe | Question it asks | If it fails |
|---|---|---|
| Readiness | "Can you take traffic right now?" | Removed from Service endpoints, not restarted |
| Liveness | "Are you still alive?" | Container is restarted |
| Startup | "Have you finished starting?" | Other probes wait; restarted only if it never starts |

Full log: [`outputs/05-pod-lifecycle.txt`](outputs/05-pod-lifecycle.txt)

---

## Cleanup
```bash
kubectl delete namespace s10
```
