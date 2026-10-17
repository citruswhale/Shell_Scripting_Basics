# Session 9 – Kubernetes Fundamentals

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

In this session I installed Minikube, checked that the cluster was healthy, read about how Kubernetes is built, and did the hands-on part of the Kubernetes Basics tutorial.

The full output of every command is saved in the [`outputs/`](outputs/) folder:
- [`01-cluster-status.txt`](outputs/01-cluster-status.txt) – install check and cluster health
- [`02-basics-tutorial.txt`](outputs/02-basics-tutorial.txt) – the tutorial steps

## My setup

| Thing | Value |
|---|---|
| Laptop | MacBook (Apple M5, arm64), 24 GB RAM |
| Container runtime | Docker Desktop 4.95 |
| Minikube | v1.39.0, docker driver, profile `devops-lab` |
| Kubernetes | v1.37.0 (kubectl v1.37.1) |
| Cluster size | 1 node, 4 CPUs, 6 GB RAM |

## Task 1 – Install and configure Minikube

I downloaded the `minikube` and `kubectl` binaries for macOS arm64 and started a cluster with its own profile name, so it stays separate from anything else:

```bash
minikube start -p devops-lab --driver=docker --cpus=4 --memory=6g --kubernetes-version=stable
```

Minikube runs the whole cluster inside one Docker container on my laptop. It also set up my kubeconfig so `kubectl` talks to this cluster.

## Task 2 – Verify cluster status

```bash
minikube status -p devops-lab
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -n kube-system
```

```text
$ minikube status -p devops-lab
devops-lab
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

$ kubectl get nodes
NAME         STATUS   ROLES           AGE   VERSION
devops-lab   Ready    control-plane   34s   v1.37.0
```

One thing I noticed: the first time I ran `kubectl get nodes` (about 20 seconds after start) the node said **NotReady**, and CoreDNS was **Pending**. The network plugin (kindnet) was still starting. After waiting a few seconds the node became **Ready** and every `kube-system` pod was Running. Both outputs are in `01-cluster-status.txt`.

```text
$ kubectl get pods -n kube-system
NAME                                 READY   STATUS    RESTARTS   AGE
coredns-559f6c778d-qhjsr             1/1     Running   0          26s
etcd-devops-lab                      1/1     Running   0          32s
kindnet-g2hct                        1/1     Running   0          26s
kube-apiserver-devops-lab            1/1     Running   0          32s
kube-controller-manager-devops-lab   1/1     Running   0          32s
kube-proxy-d6d2p                     1/1     Running   0          26s
kube-scheduler-devops-lab            1/1     Running   0          32s
storage-provisioner                  1/1     Running   0          31s
```

## Task 3 – Kubernetes architecture (short notes)

A cluster has two parts: the **control plane** (the brain) and the **worker nodes** (where apps actually run). In Minikube both are on the same single node, which is why I can see all of them in `kube-system`.

```text
                 kubectl
                    |
        +-----------v------------ Control plane ----------------+
        |  kube-apiserver  <-->  etcd                           |
        |       ^    ^                                          |
        |       |    +-- kube-scheduler                         |
        |       +------- kube-controller-manager                |
        +-------|-----------------------------------------------+
                |
        +-------v----------- Worker node -----------------------+
        |  kubelet --> containerd --> Pods (containers)          |
        |  kube-proxy (Service rules)   CNI (kindnet) networking |
        +--------------------------------------------------------+
```

**Control plane**
- **kube-apiserver** – the front door. Every command (`kubectl`, the scheduler, the kubelet) goes through it.
- **etcd** – a key-value database that stores the whole state of the cluster.
- **kube-scheduler** – picks which node a new Pod should run on.
- **kube-controller-manager** – runs loops that keep checking "what I want" against "what is there" and fixes the difference. For example, it creates a Pod again if one dies.

**Worker node**
- **kubelet** – the agent on each node. It makes sure the containers the API server asked for are running.
- **container runtime** – actually runs the containers. Here it is `containerd 2.3.4`.
- **kube-proxy** – sets up network rules so a Service IP sends traffic to the right Pods.
- **CNI plugin** – gives every Pod its own IP. Minikube uses `kindnet`.

**Add-ons I saw:** `coredns` (DNS names for Services) and `storage-provisioner` (creates volumes for PVCs).

## Task 4 – Basic objects and commands

| Object | What it is |
|---|---|
| Pod | The smallest unit. One or more containers sharing an IP and storage. |
| ReplicaSet | Keeps a fixed number of identical Pods running. |
| Deployment | Manages ReplicaSets, so you get rolling updates and rollbacks. |
| Service | A stable IP/DNS name in front of a changing group of Pods. |
| Namespace | A folder that groups and isolates resources. |
| ConfigMap / Secret | Settings and passwords given to Pods. |

| Command | What it does |
|---|---|
| `kubectl get <type>` | List objects |
| `kubectl describe <type> <name>` | Full details and recent events |
| `kubectl logs <pod>` | Container logs |
| `kubectl exec -it <pod> -- sh` | Open a shell inside a container |
| `kubectl create / apply` | Create objects (imperative / from YAML) |
| `kubectl expose` | Create a Service for a Deployment |
| `kubectl scale` | Change the number of replicas |
| `kubectl set image` | Change the image (starts a rollout) |
| `kubectl rollout status / history / undo` | Watch, list or undo a rollout |
| `kubectl api-resources` | List every object type the cluster knows |

## Task 5 – Kubernetes Basics tutorial (hands-on)

The official tutorial uses the `kubernetes-bootcamp` image, which is only built for amd64. My laptop is arm64, so I used `nginx` instead and followed the same six modules. I kept everything in its own namespace `k8s-basics`.

### Module 1 – Create a cluster
Done in Task 1 and Task 2 above.

### Module 2 – Deploy an app
```bash
kubectl create namespace k8s-basics
kubectl create deployment hello-app --image=nginx:1.27 -n k8s-basics
kubectl get deployments,replicasets,pods -n k8s-basics -o wide
```
```text
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
deployment.apps/hello-app   1/1     1            1           9s    nginx        nginx:1.27   app=hello-app

NAME                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/hello-app-6cc74798cd   1         1         1       9s

NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE
pod/hello-app-6cc74798cd-g7hsc   1/1     Running   0          9s    10.244.0.3   devops-lab
```
One command made three objects: the Deployment created a ReplicaSet, and the ReplicaSet created the Pod.

### Module 3 – Explore the app
```bash
kubectl describe pod <pod> -n k8s-basics
kubectl exec -n k8s-basics <pod> -- sh -c "hostname; nginx -v; curl -s -o /dev/null -w 'local HTTP %{http_code}\n' localhost"
kubectl logs <pod> -n k8s-basics
```
```text
hello-app-6cc74798cd-g7hsc
nginx version: nginx/1.27.5
local HTTP 200
```
`describe` showed the Pod is `Controlled By: ReplicaSet/hello-app-6cc74798cd`, got IP `10.244.0.3`, and has all conditions `True`.

### Module 4 – Expose the app with a Service
```bash
kubectl expose deployment hello-app --type=NodePort --port=80 -n k8s-basics
kubectl get svc,endpointslices -n k8s-basics
```
```text
NAME                TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/hello-app   NodePort   10.99.80.72   <none>        80:32027/TCP   0s

NAME                                             ADDRESSTYPE   PORTS   ENDPOINTS
endpointslice.discovery.k8s.io/hello-app-cm66w   IPv4          80      10.244.0.3
```
Then I tested it from a temporary curl Pod using the Service DNS name:
```text
$ kubectl run curl-test -n k8s-basics --image=curlimages/curl:8.11.1 --rm -i --restart=Never -- \
    curl -s -o /dev/null -w "service HTTP %{http_code}\n" http://hello-app.k8s-basics.svc.cluster.local
service HTTP 200
```

### Module 5 – Scale the app
```bash
kubectl scale deployment hello-app --replicas=4 -n k8s-basics
```
```text
NAME                         READY   STATUS    RESTARTS   AGE   IP
hello-app-6cc74798cd-926r8   1/1     Running   0          0s    10.244.0.6
hello-app-6cc74798cd-cw2f2   1/1     Running   0          0s    10.244.0.7
hello-app-6cc74798cd-g7hsc   1/1     Running   0          17s   10.244.0.3
hello-app-6cc74798cd-ltfjk   1/1     Running   0          0s    10.244.0.5
```

### Module 6 – Update the app (rolling update)
```bash
kubectl set image deployment/hello-app nginx=nginx:1.28 -n k8s-basics
kubectl rollout status deployment/hello-app -n k8s-basics
kubectl rollout history deployment/hello-app -n k8s-basics
```
```text
Waiting for deployment "hello-app" rollout to finish: 2 out of 4 new replicas have been updated...
Waiting for deployment "hello-app" rollout to finish: 3 out of 4 new replicas have been updated...
Waiting for deployment "hello-app" rollout to finish: 1 old replicas are pending termination...
deployment "hello-app" successfully rolled out

hello-app-6cc74798cd-g7hsc  nginx:1.27     <- last old Pod, shutting down
hello-app-759bdf67bc-557s2  nginx:1.28
hello-app-759bdf67bc-ww8gv  nginx:1.28
hello-app-759bdf67bc-wz7p8  nginx:1.28
hello-app-759bdf67bc-wzzhv  nginx:1.28

REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```
The new Pods have a different hash (`759bdf67bc`) because the Deployment made a new ReplicaSet for the new image. The old Pods were replaced a few at a time, so the app never fully went down.

## What I learned
- Minikube is an easy way to get a real cluster on a laptop. It is one node, so there is no real high availability.
- Right after start the node can be NotReady for a few seconds. That is normal, and `kubectl wait` is better than guessing.
- I almost never create Pods directly. A Deployment manages the ReplicaSet, which manages the Pods.
- Pod IPs change. A Service gives a stable name like `hello-app.k8s-basics.svc.cluster.local`.
- Check the image architecture: some tutorial images do not run on Apple Silicon.

## Cleanup
```bash
kubectl delete namespace k8s-basics
```
