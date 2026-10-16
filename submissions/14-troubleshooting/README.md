# Session 14 – Kubernetes Troubleshooting

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

I practised the main troubleshooting commands on a healthy app, then broke things on purpose (9 different problems) and fixed each one using the same routine:

```text
GET  ->  DESCRIBE  ->  EVENTS  ->  LOGS  ->  EXEC / TEST  ->  ROOT CAUSE  ->  FIX  ->  VERIFY
```

Cluster: Minikube `devops-lab` (Kubernetes v1.37), namespace `s14`. Every broken problem has a `broken.yaml` and a `fixed.yaml` in [`issues/`](issues/). The full before/after output is in [`outputs/`](outputs/).

---

## Task 1 – Troubleshooting commands

App used: [`00-app/app.yaml`](00-app/app.yaml) (nginx Deployment `gear-web` with 2 replicas + Service). Full output: [`outputs/00-commands.txt`](outputs/00-commands.txt).

| Command | What it tells me | Example I ran |
|---|---|---|
| `kubectl get` | Quick list and status | `kubectl get pods -n s14`, `kubectl get deploy,rs,svc,endpointslices -n s14`, `--show-labels` |
| `kubectl get -o wide` | Adds Pod IP and node | `gear-web-6645695bc6-jdrcj ... 10.244.0.141 devops-lab` |
| `kubectl describe` | Full details, conditions **and recent events**; the most useful one | `kubectl describe deploy gear-web -n s14` → `Scaled up replica set gear-web-6645695bc6 from 0 to 2` |
| `kubectl logs` | What the app printed (stdout/stderr) | `kubectl logs -n s14 -l app=gear-web --tail=1 --prefix` |
| `kubectl logs --previous` | Logs of the container that crashed before | used in CrashLoopBackOff |
| `kubectl exec` | Run a command inside the container | `kubectl exec ... -- wget -qO- localhost` → `<title>Welcome to nginx!</title>` |
| `kubectl events` | Events for the namespace, newest last | `kubectl events -n s14 --types=Normal` |
| `kubectl explain` | Built-in docs for any field | `kubectl explain pod.spec.containers.resources` |
| `kubectl top` | Live CPU and memory (needs metrics-server) | `kubectl top pods -n s14` |

```text
$ kubectl get pods -n s14 -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP             NODE
gear-web-6645695bc6-jdrcj   1/1     Running   0          1s    10.244.0.141   devops-lab
gear-web-6645695bc6-psz9r   1/1     Running   0          1s    10.244.0.140   devops-lab

$ kubectl exec -n s14 gear-web-6645695bc6-jdrcj -- sh -c 'wget -qO- localhost | grep -o "<title>.*</title>"; head -1 /etc/resolv.conf'
<title>Welcome to nginx!</title>
search s14.svc.cluster.local svc.cluster.local cluster.local
```

---

## Task 2 – Troubleshooting common issues

### Summary

| # | Problem | What I saw | Command that showed the cause | Root cause | Fix |
|---|---|---|---|---|---|
| 1 | CrashLoopBackOff | `Error`, restarts going up | `kubectl logs` | App exits: `DATABASE_URL is not set` | Add the env var |
| 2 | ImagePullBackOff / ErrImagePull | `ImagePullBackOff` | `kubectl describe` events | Typo in tag `1.27-alpinee` (not found) | Correct tag `1.27-alpine` |
| 3 | Pending | `Pending` forever | `kubectl describe` events | Asks for 16 CPU / 32Gi; node has 10 CPU / ~12 GB | Realistic requests/limits |
| 4 | ContainerCreating | Stuck in `ContainerCreating` | `kubectl describe` events | Mounts Secret `gear-web-tls` that doesn't exist | Create the Secret |
| 5 | Service connectivity | `curl` exit 7, HTTP 000 | `describe svc` + Pod ports | `targetPort: 8080` but nginx listens on 80 | `targetPort: 80` |
| 6 | DNS | `curl` exit 6 (can't resolve) | `nslookup`, `get svc -A` | Used namespace `default`; Service is in `s14` | Correct FQDN `gear-web.s14.svc.cluster.local` |
| 7 | Pod networking | Service **and** Pod IP refused | `exec` inside the Pod, `/proc/net/tcp` | App bound to `127.0.0.1` only | Bind to `0.0.0.0` |
| 8 | Configuration | `CreateContainerConfigError` | `kubectl describe` events | Wrong ConfigMap key `MAX_LOAN_DAYS` vs `max_loan_days` | Use the right key |
| 9 | OOMKilled | `OOMKilled`, exit code 137 | `kubectl describe` | Needs ~150 MiB, limit 64Mi | Request 192Mi / limit 256Mi |

### 1. CrashLoopBackOff – [`issues/01-crashloopbackoff/`](issues/01-crashloopbackoff/)
```text
$ kubectl get pod crashloop -n s14
NAME        READY   STATUS   RESTARTS      AGE
crashloop   0/1     Error    2 (19s ago)   20s

$ kubectl logs crashloop -n s14
FATAL: DATABASE_URL is not set

$ kubectl describe pod crashloop -n s14
    State:          Terminated
      Reason:       Error
      Exit Code:    1
    Restart Count:  2
  Warning  BackOff  kubelet  Back-off restarting failed container api in pod crashloop_s14(...)
```
**Root cause:** the container starts fine, but the program exits with code 1 because a required setting is missing. Kubernetes keeps restarting it and waits longer each time; that waiting is the "BackOff".
**Fix:** add `DATABASE_URL` to `env` in [`fixed.yaml`](issues/01-crashloopbackoff/fixed.yaml).
```text
crashloop   1/1     Running   0          3s
$ kubectl logs crashloop -n s14
connected to postgres.s14.svc.cluster.local:5432/gearloan
```

### 2. ImagePullBackOff / ErrImagePull – [`issues/02-imagepullbackoff/`](issues/02-imagepullbackoff/)
```text
imagepull   0/1     ImagePullBackOff   0          15s

$ kubectl describe pod imagepull -n s14
  Warning  Failed   kubelet  Failed to pull image "nginx:1.27-alpinee": rpc error: code = NotFound ...
  Warning  Failed   kubelet  Error: ErrImagePull
  Normal   BackOff  kubelet  Back-off pulling image "nginx:1.27-alpinee"
  Warning  Failed   kubelet  Error: ImagePullBackOff

$ docker manifest inspect nginx:1.27-alpinee   -> tag not found on Docker Hub
$ docker manifest inspect nginx:1.27-alpine    -> tag exists
```
**Root cause:** a typo in the image tag. `ErrImagePull` is the first failure; `ImagePullBackOff` means the kubelet is waiting before it tries again. Other common causes are a private registry without `imagePullSecrets`, or an image built for the wrong CPU architecture.
**Fix:** `image: nginx:1.27-alpine` → `imagepull   1/1   Running`.

### 3. Pending – [`issues/03-pending/`](issues/03-pending/)
```text
pending   0/1     Pending   0          8s

$ kubectl describe pod pending -n s14
  Warning  FailedScheduling  default-scheduler  0/1 nodes are available: 1 Insufficient cpu, 1 Insufficient memory.

$ kubectl describe node devops-lab
Allocatable:
  cpu:                10
  memory:             12232784Ki
```
**Root cause:** the scheduler can't find any node with enough free CPU or memory for the **requests** (16 CPU, 32Gi). Other reasons for Pending: a PVC that isn't bound, nodeSelector/affinity/taints that match no node, or the Pod limit per node being reached.
**Fix:** requests `50m` / `64Mi`, limits `200m` / `128Mi` → `Running` on `devops-lab`.

### 4. ContainerCreating – [`issues/04-containercreating/`](issues/04-containercreating/)
```text
creating   0/1     ContainerCreating   0          20s

$ kubectl describe pod creating -n s14
  Normal   Scheduled    default-scheduler  Successfully assigned s14/creating to devops-lab
  Warning  FailedMount  kubelet  MountVolume.SetUp failed for volume "tls" : secret "gear-web-tls" not found

$ kubectl get secret gear-web-tls -n s14
Error from server (NotFound): secrets "gear-web-tls" not found
```
**Root cause:** the Pod was scheduled, but the kubelet can't prepare its volume, so the container is never created. Other causes: a slow image pull, the CNI not being ready, or a cloud disk that can't attach.
**Fix:** create the Secret ([`fixed.yaml`](issues/04-containercreating/fixed.yaml)). I didn't change the Pod at all; the kubelet retried and it started by itself:
```text
secret/gear-web-tls created
creating   1/1     Running   0          32s
$ kubectl exec -n s14 creating -- ls /etc/tls
note.txt
```

### 5. Service connectivity – [`issues/05-service-connectivity/`](issues/05-service-connectivity/)
```text
$ kubectl exec -n s14 client -- curl -s -m 5 -o /dev/null -w "HTTP %{http_code}\n" http://gear-web-svc
HTTP 000
command terminated with exit code 7

$ kubectl get endpointslices -n s14 -l kubernetes.io/service-name=gear-web-svc
gear-web-svc-cdbm8   IPv4          8080    10.244.0.141,10.244.0.140      <- endpoints exist, so the selector is fine

$ kubectl describe svc gear-web-svc -n s14
TargetPort:               8080/TCP
Endpoints:                10.244.0.141:8080,10.244.0.140:8080

$ kubectl get pod ... -o jsonpath='{.items[0].spec.containers[0].ports}'
[{"containerPort":80,"protocol":"TCP"}]

pod 10.244.0.141 port 80 -> HTTP 200
pod 10.244.0.141 port 8080 -> refused (exit 7)
```
**Root cause:** the selector is fine, since there are endpoints. But the Service sends traffic to port 8080, where nothing is listening. (Empty endpoints would point to a selector/label problem instead; I did that one in the mini project below.)
**Fix:** `targetPort: 80` → endpoints now on port 80, `HTTP 200`.

### 6. DNS – [`issues/06-dns/`](issues/06-dns/)
```text
$ kubectl logs dns-client -n s14
HTTP 000
curl failed with exit 6            <- exit 6 = could not resolve host

$ kubectl exec -n s14 client -- nslookup gear-web.default.svc.cluster.local
** server can't find gear-web.default.svc.cluster.local: NXDOMAIN

$ kubectl get svc -A | grep gear-web
s14                 gear-web      ClusterIP   10.100.132.17   <none>   80/TCP

$ kubectl exec -n s14 client -- nslookup gear-web.s14.svc.cluster.local
Name:	gear-web.s14.svc.cluster.local
Address: 10.100.132.17
```
**Root cause:** the client used the FQDN for namespace `default`, but the Service is in `s14`. DNS itself works fine (CoreDNS answered `NXDOMAIN`). The name was simply wrong.
**Fix:** use `gear-web.s14.svc.cluster.local` → `HTTP 200`.

### 7. Pod networking – [`issues/07-pod-networking/`](issues/07-pod-networking/)
```text
$ kubectl exec -n s14 client -- curl -s -m 5 http://inventory-api
curl failed, exit 7

$ kubectl get endpointslices ... inventory-api
inventory-api-b4t6c   IPv4          8000    10.244.0.155          <- endpoint exists, ports match

direct to pod IP 10.244.0.155:8000 also fails (exit 7)            <- not a Service problem

$ kubectl exec -n s14 deploy/inventory-api -- python3 -c "...urlopen('http://127.0.0.1:8000')..."
from inside the pod: 200                                          <- the app works locally

$ kubectl exec -n s14 deploy/inventory-api -- cat /proc/net/tcp     (listening sockets)
listening on 0100007F:1F40        <- 0100007F = 127.0.0.1, 1F40 = port 8000
```
**Root cause:** the app listens only on the loopback address `127.0.0.1`, so it can only be reached from inside its own Pod. Traffic arriving on the Pod IP `10.244.0.155` is refused.
**Fix:** `--bind 0.0.0.0` → `HTTP 200` through the Service. The same mistake is common with Flask/FastAPI dev servers that default to `127.0.0.1`.

### 8. Configuration issue – [`issues/08-configuration/`](issues/08-configuration/)
```text
config-app   0/1     CreateContainerConfigError   0          9s

$ kubectl describe pod config-app -n s14
  Warning  Failed  kubelet  Error: couldn't find key MAX_LOAN_DAYS in ConfigMap s14/loan-settings

$ kubectl get configmap loan-settings -n s14 -o jsonpath='{.data}'
{"max_loan_days":"14"}
```
**Root cause:** ConfigMap keys are case-sensitive, and the Pod asked for `MAX_LOAN_DAYS`.
**Fix:** `key: max_loan_days` → `Running`, logs `MAX_LOAN_DAYS=14`.

### 9. OOMKilled (resource problem) – [`issues/09-oomkilled/`](issues/09-oomkilled/)
```text
oom    0/1     OOMKilled   2 (19s ago)   20s

$ kubectl describe pod oom -n s14
    State:          Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Restart Count:  2
    Limits:
      memory:  64Mi
```
**Root cause:** the program needs about 150 MiB, but the memory limit is 64Mi. When it goes over, the kernel kills it. Exit code `137` = 128 + signal 9 (SIGKILL).
**Fix:** request `192Mi`, limit `256Mi`:
```text
oom    1/1     Running   0          70s
$ kubectl logs oom -n s14
built report using 150 MiB
$ kubectl top pod oom -n s14
NAME   CPU(cores)   MEMORY(bytes)
oom    0m           153Mi
```
Unlike memory, a container that goes over its **CPU** limit is not killed, only slowed down (throttled).

---

## Task 3 – Mini project (instructor's "Troubleshooting Challenge")

Files: [`mini-project/`](mini-project/). These are the instructor's `deployment.yaml`, `service.yaml` and `broken-pod.yaml`, plus my `service-broken-selector.yaml`. I ran it in namespace `s14-mp`. Full output: [`outputs/10-mini-project.txt`](outputs/10-mini-project.txt).

**Deploy and check.** 2 nginx Pods are Running; `curl localhost` inside a Pod gives `<title>Welcome to nginx!</title>`; the Service selector is `app=troubleshooting-app` and it has 2 endpoints.

### The broken Pod
```text
$ kubectl get pod project-broken-pod -n s14-mp
NAME                 READY   STATUS         RESTARTS   AGE
project-broken-pod   0/1     ErrImagePull   0          15s

$ kubectl describe pod project-broken-pod -n s14-mp
  Normal   Pulling    kubelet  Pulling image "nginx:this-tag-does-not-exist"
  Warning  Failed     kubelet  Failed to pull image "nginx:this-tag-does-not-exist": rpc error: code = NotFound ...
  Warning  Failed     kubelet  Error: ErrImagePull
  Normal   BackOff    kubelet  Back-off pulling image "nginx:this-tag-does-not-exist"
  Warning  Failed     kubelet  Error: ImagePullBackOff
```
1. **What is the Pod status?** `ErrImagePull`, which then turns into `ImagePullBackOff`.
2. **What is the actual error?** `Failed to pull image "nginx:this-tag-does-not-exist": ... NotFound`.
3. **Which command helped?** `kubectl describe pod project-broken-pod`, the Events section.
4. **What is wrong with the image?** The tag `this-tag-does-not-exist` doesn't exist on Docker Hub.
5. **How would you fix it?** Use a real tag, like `nginx:1.27`. After that: `project-broken-pod   1/1   Running`.

### The Service selector problem
```text
$ kubectl get endpoints troubleshooting-service -n s14-mp
NAME                      ENDPOINTS   AGE
troubleshooting-service   <none>      20s
HTTP 000

$ kubectl get pods -n s14-mp --show-labels
troubleshooting-app-59d4957864-mq42f   1/1   Running   app=troubleshooting-app,pod-template-hash=59d4957864
troubleshooting-app-59d4957864-znp7c   1/1   Running   app=troubleshooting-app,pod-template-hash=59d4957864

$ kubectl describe svc troubleshooting-service -n s14-mp
Selector:                 app=wrong-app
Endpoints:
```
Pod label `app=troubleshooting-app` ≠ selector `app=wrong-app`. I put the selector back:
```text
troubleshooting-service   10.244.0.176:80,10.244.0.177:80   25s
HTTP 200
Name:	troubleshooting-service.s14-mp.svc.cluster.local
```

### Troubleshooting table

| Problem | What I saw | Command I used | Root cause | Fix |
|---|---|---|---|---|
| **Broken Pod** | `0/1 ErrImagePull` | `kubectl get pod`, `kubectl describe pod` | Image can't be pulled | Fix the image reference |
| **Service problem** | Endpoints `<none>`, curl `HTTP 000` | `kubectl get endpoints`, `get pods --show-labels`, `describe svc` | Selector `app=wrong-app` matches no Pod | Selector `app=troubleshooting-app` |
| **Image problem** | `NotFound` in Events | `kubectl describe pod` | Tag `this-tag-does-not-exist` doesn't exist | `nginx:1.27` |

### README questions

1. **What does `kubectl get` tell us?** A short list of objects and their current state: READY, STATUS, RESTARTS, AGE. With `-o wide` it also shows the IP and node. It's the first thing I run.
2. **`get` vs `describe`?** `get` is a one-line summary. `describe` shows everything about one object, including conditions and, most importantly, the **Events** that explain *why* it's in that state.
3. **Why use `kubectl logs`?** To see what the program itself printed. Kubernetes can tell me *that* a container crashed; only the logs tell me *why* the app crashed (`FATAL: DATABASE_URL is not set`).
4. **When use `kubectl exec`?** When the Pod runs but something is still wrong: to test from inside (`curl localhost`), check files, env vars and DNS, or see which address the app listens on (issue 7).
5. **What does `CrashLoopBackOff` mean?** The container keeps starting and then exiting. Kubernetes restarts it with growing delays (10 s, 20 s, 40 s ... up to 5 min).
6. **What does `ImagePullBackOff` mean?** The kubelet couldn't download the image (wrong name or tag, private registry without credentials, no network) and is waiting before it tries again.
7. **Why can a Pod stay `Pending`?** No node fits it: not enough CPU or memory for its requests, an unbound PVC, a nodeSelector, affinity or taint that matches no node, or the Pod-per-node limit is reached. `describe` shows `FailedScheduling` with the reason.
8. **Why can a Service have no endpoints?** Its selector matches no Pods (typo, wrong label), or the matching Pods are not Ready (readiness probe failing), or they're in another namespace.
9. **Selector vs Pod labels?** The Service selector is a label query. Every **Ready** Pod in the same namespace whose labels match becomes an endpoint. They're only connected through the labels.
10. **What is Kubernetes DNS?** CoreDNS, running in `kube-system`. It gives every Service a name like `<svc>.<namespace>.svc.cluster.local`, so Pods can find each other by name instead of by IP.

---

## Cleanup
```bash
kubectl delete namespace s14 s14-mp
```
