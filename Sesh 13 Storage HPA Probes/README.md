# Session 13 – Kubernetes Storage, HPA & Probes

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

All of this ran on my Minikube cluster (`devops-lab`, Kubernetes v1.37). Raw output for every step is in [`outputs/`](outputs/).

| Task | Folder | Log |
|---|---|---|
| 1. Kubernetes volumes | [`01-kubernetes-volumes/`](01-kubernetes-volumes/README.md) | [`01-volumes.txt`](outputs/01-volumes.txt) |
| 2. HPA hands-on | [`02-hpa/`](02-hpa/) | [`02-hpa.txt`](outputs/02-hpa.txt) |
| 3. Mini project | [`03-mini-project/`](03-mini-project/) | [`03-mini-project.txt`](outputs/03-mini-project.txt) |

---

## Task 1 – Kubernetes volumes

The full notes, with a working example for each type, are in **[`01-kubernetes-volumes/README.md`](01-kubernetes-volumes/README.md)**: emptyDir, hostPath, PersistentVolume, PersistentVolumeClaim, StorageClass and dynamic provisioning.

Short version of what I proved:
- **emptyDir:** shared between 2 containers, and gone when the Pod was re-created.
- **hostPath:** the file survived a new Pod, and I could read it on the node with `minikube ssh`.
- **Static PV:** a hand-made 200Mi PV bound to a 100Mi claim.
- **Dynamic PVC:** the StorageClass created a PV by itself. Data survived Pod deletion.
- **Reclaim policies:** `Delete` removed the dynamic PV with its claim, and `Retain` kept the manual PV as `Released`.

---

## Task 2 – HPA hands-on

Files: [`02-hpa/hpa.yml`](02-hpa/hpa.yml) (namespace, Deployment, Service, HPA) and [`02-hpa/load-generator.yaml`](02-hpa/load-generator.yaml).

**How it is set up**
- `web` is nginx with `requests.cpu: 50m`. The HPA percentage is measured against this request, so without a CPU request the HPA can't work.
- HPA: min 1, max 6, target **50% average CPU**.
- I set `scaleDown.stabilizationWindowSeconds: 60` (the default is 300) so I could see the scale-down in the lab.
- The load generator is 3 busybox Pods running `while true; do wget -q -O /dev/null http://web; done`.

### 1–3. Deploy, configure and verify the HPA
```bash
minikube addons enable metrics-server -p devops-lab
kubectl apply -f 02-hpa/hpa.yml
```
```text
$ kubectl top nodes
NAME         CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
devops-lab   154m         1%       1090Mi          9%

$ kubectl get hpa web -n s13-hpa
NAME   REFERENCE        TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
web    Deployment/web   cpu: 2%/50%   1         6         1          76s

$ kubectl describe hpa web -n s13-hpa
Metrics:                                               ( current / target )
  resource cpu on pods  (as a percentage of request):  2% (1m) / 50%
Conditions:
  AbleToScale     True    ReadyForNewScale    recommended size matches current size
  ScalingActive   True    ValidMetricFound    the HPA was able to successfully calculate a replica count ...
```

### 4–7. Load generator, CPU and scaling
```bash
kubectl apply -f 02-hpa/load-generator.yaml
```
About 1.5 minutes after the load started:
```text
$ kubectl top pods -n s13-hpa
NAME                              CPU(cores)   MEMORY(bytes)
load-generator-86f8cdf745-lhpr5   301m         3Mi
load-generator-86f8cdf745-pjfw4   301m         4Mi
load-generator-86f8cdf745-qwn9k   301m         5Mi
web-7584b47678-hnf7p              62m          10Mi          <- 62m of a 50m request = over 100%
```
About 3 minutes in:
```text
$ kubectl get hpa web -n s13-hpa
NAME   REFERENCE        TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
web    Deployment/web   cpu: 72%/50%   1         6         3          4m17s

$ kubectl get pods -n s13-hpa -l app=web
web-7584b47678-2c29d   1/1     Running   0          2m2s
web-7584b47678-96dgc   1/1     Running   0          2s       <- just added
web-7584b47678-hnf7p   1/1     Running   0          4m17s
web-7584b47678-vclr7   1/1     Running   0          2s       <- just added
web-7584b47678-w79zc   1/1     Running   0          2m2s

$ kubectl top pods -n s13-hpa
web-7584b47678-2c29d              36m          9Mi           <- load now spread over more Pods
web-7584b47678-hnf7p              36m          10Mi
web-7584b47678-w79zc              36m          9Mi
```
`kubectl describe hpa` events:
```text
Normal   SuccessfulRescale   horizontal-pod-autoscaler  New size: 3; reason: cpu resource utilization (percentage of request) above target
Normal   SuccessfulRescale   horizontal-pod-autoscaler  New size: 5; reason: cpu resource utilization (percentage of request) above target
```

**Scale down.** I deleted the load generator and watched:
```text
21:00:28  cpu: 0%/50% replicas=5
21:00:43  cpu: 0%/50% replicas=1

Normal   SuccessfulRescale   New size: 1; reason: All metrics below target
```

**How the HPA picked 3 and then 5:**

```text
desired = ceil( current_replicas × current_cpu% / target% )
```
- 1 Pod at about 124% (62m / 50m) → ceil(1 × 124 / 50) = 3.
- Then 3 Pods at 72% → ceil(3 × 72 / 50) = 5.

Right after the HPA was created, its events also showed a couple of `FailedGetResourceMetric` warnings. metrics-server needs about a minute to collect the first numbers for a new Pod, and they stopped on their own.

### 8–9. Output
Full output: [`outputs/02-hpa.txt`](outputs/02-hpa.txt).

---

## Task 3 – Mini project: "Production-ready web app"

This is the instructor's mini project: [`03-mini-project/`](03-mini-project/). It has a namespace, a 500Mi RWO PVC, an nginx Deployment with 2 replicas, the Service `web-service`, and an HPA (2–5 Pods, 50% CPU). The Deployment has CPU/memory requests and limits, a PVC mounted at `/data`, and all 3 probes:

| Probe | Path | Settings | What it protects |
|---|---|---|---|
| startup | `/` | every 2 s, up to 30 failures (60 s) | gives slow starts time before the other probes run |
| readiness | `/` | every 5 s, 2 failures | takes the Pod out of the Service if it can't serve |
| liveness | `/` | every 5 s, 3 failures | restarts a stuck container |

The Deployment uses `strategy: Recreate` because the volume is ReadWriteOnce.

```text
$ kubectl get pvc -n production-webapp
NAME       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
web-data   Bound    pvc-85799592-f7b5-42ea-a596-2d8f4799c4cb   500Mi      RWO            standard

$ kubectl get pods -n production-webapp
web-app-d45775485-h2rq8   1/1     Running   0          8s
web-app-d45775485-jd9p6   1/1     Running   0          8s

$ kubectl get hpa -n production-webapp
NAME          REFERENCE            TARGETS       MINPODS   MAXPODS   REPLICAS
web-app-hpa   Deployment/web-app   cpu: 1%/50%   2         5         2
```

### Verify storage persistence
```text
$ kubectl exec -n production-webapp web-app-d45775485-h2rq8 -- sh -c 'echo "Student: Srinidhi Narendran (24BCS10037)" > /data/student.txt'

$ kubectl delete pods -n production-webapp -l app=web-app          # delete BOTH Pods
pod "web-app-d45775485-h2rq8" deleted
pod "web-app-d45775485-jd9p6" deleted

# brand new Pods:
web-app-d45775485-qmrql: Student: Srinidhi Narendran (24BCS10037)
web-app-d45775485-w7mcf: Student: Srinidhi Narendran (24BCS10037)
```
Both Pods are on the same node, so both can mount the RWO volume and see the same file.

### Service check
```text
# from inside the cluster
web-service -> HTTP 200
# from my Mac with: kubectl port-forward -n production-webapp svc/web-service 8089:80
$ curl -s http://localhost:8089 | grep -o "<title>.*</title>"
<title>Welcome to nginx!</title>
```

### HPA under load
I ran 3 load-generator Pods (`wget` loop against `web-service`):
```text
21:04:28  cpu: 84%/50% replicas=2
21:04:43  cpu: 84%/50% replicas=4      <- scaled out
21:05:28  cpu: 57%/50% replicas=4
21:06:28  cpu: 42%/50% replicas=4      <- settled below target, so it stopped at 4
...
$ kubectl top pods -n production-webapp -l app=web-app
web-app-d45775485-9gf28   47m          9Mi
web-app-d45775485-9w2sv   46m          10Mi
web-app-d45775485-qmrql   45m          9Mi
web-app-d45775485-w7mcf   47m          10Mi
```
After I deleted the load generator, this HPA used the **default 5-minute** scale-down window:
```text
21:12:36  cpu: 1%/50% replicas=4
...
21:16:38  cpu: 1%/50% replicas=3
21:17:38  cpu: 1%/50% replicas=2      <- back to minReplicas

TIME                   MESSAGE
2026-10-16T19:04:27Z   New size: 4; reason: cpu resource utilization (percentage of request) above target
2026-10-16T19:16:12Z   New size: 3; reason: All metrics below target
2026-10-16T19:17:12Z   New size: 2; reason: All metrics below target
```
It never reached 5. At 4 Pods the CPU was around 42–47%, already under the 50% target.

### Readiness failure and recovery (bonus challenge 2)
I pinned the HPA to 2 Pods so it wouldn't interfere, then changed the readiness path to `/does-not-exist`:
```text
$ kubectl get pods -n production-webapp -l app=web-app
web-app-5945bfc776-bsx85   0/1     Running   0          50s      <- Running, but NOT ready
web-app-5945bfc776-sv5qk   0/1     Running   0          50s         and 0 restarts

$ kubectl get endpointslices ... web-service
10.244.0.167 ready=false
10.244.0.168 ready=false

Warning  Unhealthy  kubelet  Readiness probe failed: HTTP probe failed with statuscode: 404

web-service -> HTTP 000        <- no ready Pods, so the Service has nowhere to send traffic
```
`kubectl rollout status` also timed out, because the new Pods never became ready. This is how a bad release gets stopped.

I changed the path back to `/`:
```text
web-app-d45775485-cc6z5   1/1     Running   0          13s
web-app-d45775485-gt2zt   1/1     Running   0          13s
10.244.0.170 ready=true
10.244.0.171 ready=true
```

### Liveness failure and recovery (bonus challenge 3)
I changed the liveness path to `/crash`:
```text
$ kubectl get pods -n production-webapp -l app=web-app      # 50 seconds later
web-app-85d86b65d-wpsf6   0/1     Running   3 (5s ago)   50s
web-app-85d86b65d-xql7c   0/1     Running   3 (5s ago)   50s

Warning  Unhealthy  kubelet  Liveness probe failed: HTTP probe failed with statuscode: 404
Normal   Killing    kubelet  Container nginx failed liveness probe, will be restarted
```
After I changed it back to `/`, the Pods stayed at 0 restarts. My file was still on the PVC after all those restarts:
```text
web-app-d45775485-8xfp2   1/1     Running   0          49s
web-app-d45775485-k7rcr   1/1     Running   0          49s
web-app-d45775485-8xfp2: Student: Srinidhi Narendran (24BCS10037)
web-app-d45775485-k7rcr: Student: Srinidhi Narendran (24BCS10037)
```

### Readiness vs liveness – what I saw

| | Readiness fails | Liveness fails |
|---|---|---|
| STATUS | `Running` | `Running`, restarting |
| READY | `0/1` | `0/1` while restarting |
| RESTARTS | stays 0 | goes up (3 in 50 s) |
| Service endpoints | marked `ready=false`, no traffic | dropped while restarting |
| Use it for | "not ready **yet**" (warming up, DB down) | "stuck and will never recover by itself" |

**Lesson:** don't point liveness at something that depends on another service, like the database. If the DB goes down, every Pod would be restarted for no reason. Readiness is the right probe for that.

---

## Cleanup
```bash
kubectl delete namespace s13-hpa production-webapp
```
