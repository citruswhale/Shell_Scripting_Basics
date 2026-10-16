# Session 11 – Kubernetes Networking & Services

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

I deployed one small app and put all 5 Service types in front of it. I tested each one, looked at EndpointSlices and DNS, and fixed a broken Service. Everything ran on my Minikube cluster (`devops-lab`, Kubernetes v1.37, docker driver on macOS) in a namespace called `s11`.

Other docs for this session:
- [`fqdn/README.md`](fqdn/README.md) – FQDNs and Kubernetes DNS names
- [`coredns/README.md`](coredns/README.md) – CoreDNS and DNS troubleshooting
- [`outputs/`](outputs/) – raw output of every command I ran

## The app

[`00-app/web-deployment.yaml`](00-app/web-deployment.yaml) runs 3 Pods of `agnhost serve-hostname`. Each Pod replies with **its own Pod name**, so I can see which Pod answered. [`00-app/client-pod.yaml`](00-app/client-pod.yaml) is a test Pod I `exec` into to run `curl` and `nslookup` from inside the cluster.

```bash
kubectl apply -f 00-app/namespace.yaml
kubectl apply -f 00-app/
```
```text
NAME                   READY   STATUS    IP
client                 1/1     Running   10.244.0.72
web-658885c57f-4hv8d   1/1     Running   10.244.0.75
web-658885c57f-r6xc5   1/1     Running   10.244.0.74
web-658885c57f-xf56z   1/1     Running   10.244.0.73
```

---

## Task 1 – The 5 Service types

### 1. ClusterIP – [`01-clusterip/service.yaml`](01-clusterip/service.yaml)

The default type. It gets a virtual IP that **only works inside the cluster**.

```text
$ kubectl get svc web-clusterip -n s11
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
web-clusterip   ClusterIP   10.102.106.60   <none>        80/TCP    1s

$ kubectl get endpointslices -n s11 -l kubernetes.io/service-name=web-clusterip
NAME                  ADDRESSTYPE   PORTS   ENDPOINTS
web-clusterip-p65gj   IPv4          8080    10.244.0.73,10.244.0.75,10.244.0.74
```
The Service port is 80, but the endpoints use 8080. `targetPort: http` points at the named container port.

**Test from inside the cluster (30 requests):**
```text
$ kubectl exec -n s11 client -- sh -c 'for i in $(seq 1 30); do curl -s web-clusterip -w " %{http_code}\n"; done | sort | uniq -c'
     10 web-658885c57f-4hv8d 200
     10 web-658885c57f-r6xc5 200
     10 web-658885c57f-xf56z 200
```
Traffic was spread over all 3 Pods.

**Test from my Mac:**
```text
ClusterIP is 10.102.106.60. Trying it from my Mac:
-> no answer from the Mac (exit 28): a ClusterIP only works inside the cluster
```

> **My mistake first:** my first test ran less than a second after I created the Service, and 6 of 9 requests got nothing back. The Pods were fine (I curled each Pod IP directly and got 200). kube-proxy simply had not written its rules yet. A minute later 30 out of 30 worked. Both runs are in [`outputs/01-clusterip.txt`](outputs/01-clusterip.txt).

### 2. NodePort – [`02-nodeport/service.yaml`](02-nodeport/service.yaml)

Opens the same port (here `30080`) on **every node**, so traffic from outside the cluster can come in through `<node-ip>:30080`.

```text
$ kubectl get svc web-nodeport -n s11
NAME           TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
web-nodeport   NodePort   10.98.169.33   <none>        80:30080/TCP   0s

$ minikube ip -p devops-lab
192.168.49.2
```
**Tests:**
```text
# from inside the cluster, using the node IP
$ kubectl exec -n s11 client -- curl -s http://192.168.49.2:30080
web-658885c57f-xf56z 200
web-658885c57f-4hv8d 200
web-658885c57f-r6xc5 200

# kube-proxy rule on the node
$ minikube ssh -- "sudo iptables-save -t nat | grep web-nodeport"
-A KUBE-NODEPORTS -p tcp -m comment --comment "s11/web-nodeport" -m tcp --dport 30080 -j KUBE-EXT-HSC7BRQC7LFEXT25

# from my Mac, straight to 192.168.49.2:30080
-> no answer (exit 28)

# from my Mac, using the URL that `minikube service --url` gave me
$ minikube service web-nodeport -n s11 -p devops-lab --url
http://127.0.0.1:51899
! Because you are using a Docker driver on darwin, the terminal needs to be open to run it.
$ curl http://127.0.0.1:51899
web-658885c57f-xf56z 200
web-658885c57f-xf56z 200
web-658885c57f-r6xc5 200
```
On macOS with the docker driver, the node IP `192.168.49.2` is inside Docker Desktop's own network, so my Mac can't reach it directly. `minikube service` makes a local tunnel to fix that. On a real Linux node or a cloud VM, `<node-ip>:30080` would work directly.

My first NodePort test also ran too early and failed the same way as ClusterIP. Full log: [`outputs/02-nodeport.txt`](outputs/02-nodeport.txt)

### 3. LoadBalancer – [`03-loadbalancer/service.yaml`](03-loadbalancer/service.yaml)

Asks the cloud provider for an external load balancer. Minikube has no cloud, so at first nothing gave it an IP:
```text
$ kubectl get svc web-lb -n s11      # no tunnel yet
NAME     TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
web-lb   LoadBalancer   10.101.101.111   <pending>     8081:31034/TCP   10s
```
`<pending>` is normal here. A LoadBalancer Service also creates a NodePort (`31034`) and a ClusterIP underneath.

I started `minikube tunnel` in another terminal. It plays the role of the cloud load balancer:
```text
$ minikube tunnel -p devops-lab
* Tunnel successfully started
* Starting tunnel for service web-lb.

$ kubectl get svc web-lb -n s11
NAME     TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
web-lb   LoadBalancer   10.101.101.111   127.0.0.1     8081:31034/TCP   32s

$ curl http://127.0.0.1:8081       # from my Mac, 6 times
web-658885c57f-r6xc5 200
web-658885c57f-4hv8d 200
web-658885c57f-4hv8d 200
web-658885c57f-r6xc5 200
web-658885c57f-r6xc5 200
web-658885c57f-4hv8d 200
```
I used port 8081 so the tunnel didn't need `sudo`.

**Something I didn't expect:** after I stopped the tunnel, `EXTERNAL-IP` still said `127.0.0.1` and curl **still worked**. I checked port 8081 and found an `ssh -L 8081:10.101.101.111:8081` process the tunnel had started and left behind. Once I stopped that too, curl failed (exit 7). So:
- A pending or stale `EXTERNAL-IP` is not proof that a load balancer is working, and neither is a working ClusterIP.
- This is only a local stand-in. A real cloud load balancer (for example an AWS NLB) is a different thing. I'll test a real one in the EKS part of my capstone.

Full log: [`outputs/03-loadbalancer.txt`](outputs/03-loadbalancer.txt)

### 4. ExternalName – [`04-externalname/service.yaml`](04-externalname/service.yaml)

No Pods, no selector, no IP. It is just a **DNS alias (CNAME)** to a name outside the cluster.
```text
$ kubectl get svc example-site -n s11
NAME           TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
example-site   ExternalName   <none>       example.com   <none>    3s

$ kubectl exec -n s11 client -- nslookup example-site.s11.svc.cluster.local
example-site.s11.svc.cluster.local	canonical name = example.com.
Name:	example.com
Address: 104.20.23.154
Name:	example.com
Address: 172.66.147.243

$ kubectl exec -n s11 client -- curl -s -o /dev/null -w "http code %{http_code} from %{remote_ip}\n" -H "Host: example.com" http://example-site
http code 200 from 172.66.147.243

$ kubectl get endpointslices -n s11 -l kubernetes.io/service-name=example-site
No resources found in s11 namespace.
```
Apps can call `example-site` and I can later change where it points without touching the apps. Because it is only DNS, the HTTP `Host` header still has to match what the real site expects. That's why I added `-H "Host: example.com"`.

### 5. Headless – [`05-headless/`](05-headless/)

`clusterIP: None`, so there is no virtual IP. DNS returns the **Pod IPs themselves**. I used it with a StatefulSet `db` (3 Pods).
```text
$ kubectl get svc db-headless -n s11
NAME          TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
db-headless   ClusterIP   None         <none>        8080/TCP   6s

$ kubectl exec -n s11 client -- nslookup db-headless.s11.svc.cluster.local
Name:	db-headless.s11.svc.cluster.local
Address: 10.244.0.78
Name:	db-headless.s11.svc.cluster.local
Address: 10.244.0.77
Name:	db-headless.s11.svc.cluster.local
Address: 10.244.0.76

# compare with a normal Service, which returns one virtual IP
$ kubectl exec -n s11 client -- nslookup web-clusterip.s11.svc.cluster.local
Name:	web-clusterip.s11.svc.cluster.local
Address: 10.102.106.60
```
Each StatefulSet Pod also gets its **own stable name**:
```text
$ for i in 0 1 2; do curl -s db-$i.db-headless.s11.svc.cluster.local:8080; done
db-0
db-1
db-2
```
When I deleted `db-1`, it came back with the **same name but a new IP**, and DNS followed it:
```text
before:  db-1.db-headless.s11.svc.cluster.local -> 10.244.0.77
after:   db-1.db-headless.s11.svc.cluster.local -> 10.244.0.79
```
This is why databases (where you must talk to a specific member, like the primary) use headless Services.

Full log: [`outputs/05-headless.txt`](outputs/05-headless.txt)

### All 5 at a glance

| Type | Gets a ClusterIP? | Reachable from | How I tested it | Typical use |
|---|---|---|---|---|
| ClusterIP | Yes | Inside the cluster only | curl from the client Pod | Backend APIs, databases |
| NodePort | Yes | `<any-node-ip>:30000-32767` | curl to node IP; `minikube service` from the Mac | Labs, simple on-prem setups |
| LoadBalancer | Yes (+ NodePort) | An external IP from the cloud | `minikube tunnel`, curl `127.0.0.1:8081` | Public apps in the cloud |
| ExternalName | No | Inside (DNS only) | `nslookup` shows a CNAME; curl to example.com | Aliasing an outside DB or API |
| Headless | No (`None`) | Inside, straight to Pod IPs | `nslookup` returns 3 Pod IPs | StatefulSets, databases |

### Bonus – fixing a broken Service

[`troubleshooting-empty-endpoints.yaml`](troubleshooting-empty-endpoints.yaml) is broken on purpose.

| Step | What I did | What I found |
|---|---|---|
| Problem | `curl web-broken` | `command terminated with exit code 7` (connection refused) |
| Investigate | `kubectl get endpointslices ... web-broken` | `ENDPOINTS <unset>`, so no Pods behind it |
| | `kubectl describe svc web-broken` | `Selector: app=webapp` |
| | `kubectl get pods --show-labels` | Pods have `app=web` |
| Root cause | | The selector doesn't match any Pod label |
| Fix | `kubectl patch svc web-broken -p '{"spec":{"selector":{"app":"web"}}}'` | |
| Verify | endpoints and curl | `10.244.0.74,10.244.0.75,10.244.0.73`, and `web-658885c57f-xf56z 200` |

Full log: [`outputs/07-troubleshooting-empty-endpoints.txt`](outputs/07-troubleshooting-empty-endpoints.txt)

---

## Task 2 – Kubernetes object comparison

### Deployment vs ReplicaSet

| | ReplicaSet | Deployment |
|---|---|---|
| **Purpose** | Keep exactly N copies of a Pod running | Manage versions of an app over time |
| **Pod management** | Creates and deletes Pods directly to match `replicas` | Doesn't touch Pods itself; it creates and scales ReplicaSets |
| **Scaling** | `kubectl scale rs ...` works | `kubectl scale deploy ...`; it passes the number down to its current ReplicaSet |
| **Rolling updates** | None. Changing the image does not replace existing Pods | Yes. Makes a new ReplicaSet and moves Pods over step by step; supports `rollout undo` |
| **History** | None | Keeps old ReplicaSets (scaled to 0) as revisions |

**How they are related:** Deployment → owns ReplicaSets → own Pods. I saw this in Session 9 and Session 10. After `kubectl set image`, there were two ReplicaSets (`hello-app-6cc74798cd` and `hello-app-759bdf67bc`), and the old one was scaled to 0 but kept for rollback. You almost never create a ReplicaSet by hand; you use a Deployment.

### Deployment vs DaemonSet vs StatefulSet

| | Deployment | DaemonSet | StatefulSet |
|---|---|---|---|
| **Use case** | Stateless apps (web, APIs) | One Pod on every node (agents) | Stateful apps (databases, queues) |
| **Pod creation** | All at once, random names (`web-658885c57f-4hv8d`) | One per node, added automatically when a node joins | One by one, in order, fixed names (`db-0`, `db-1`, `db-2`) |
| **Scaling** | Change `replicas` | You don't set replicas; it follows the number of nodes | Change `replicas`; scales up in order and down in reverse |
| **Networking** | Pods are interchangeable behind a normal Service | Often `hostNetwork` or node ports to see node traffic | Headless Service gives each Pod a stable DNS name (`db-1.db-headless...`) |
| **Storage** | Usually none, or one shared volume | Usually `hostPath` (to read node logs, etc.) | `volumeClaimTemplates`: each Pod gets its **own** PVC that stays with it |
| **Examples** | nginx, a FastAPI backend, a React frontend | kube-proxy, kindnet (both in my `kube-system`), Fluent Bit, node-exporter | PostgreSQL, MySQL, Kafka, Elasticsearch |

In my cluster, `kube-proxy` and `kindnet` are DaemonSets, and `coredns` is a Deployment.

### ReplicaSet vs Service

| | ReplicaSet | Service |
|---|---|---|
| **Job** | Keeps N Pods **alive** | Gives those Pods **one stable address** |
| **Works on** | Pod count | Network traffic |
| **Finds Pods by** | Label selector | Label selector (the same idea, but separate) |
| **If a Pod dies** | Creates a new one (new name, new IP) | Updates its endpoints to the new IP automatically |

**Why a Service is needed:** Pod IPs change all the time. In Session 10, every update and every restart gave new IPs, and in the headless test `db-1` went from `.77` to `.79`. Clients can't keep track of that. A Service gives one name and IP that never change.

**How traffic reaches a Pod:**
1. The client calls `web-clusterip`.
2. CoreDNS turns that into the ClusterIP `10.102.106.60`.
3. The packet goes to `10.102.106.60:80`.
4. kube-proxy's iptables rules on the node pick one endpoint at random and rewrite (DNAT) the destination to, for example, `10.244.0.74:8080`.
5. The CNI (kindnet) delivers it to the Pod.

The ReplicaSet and the Service never talk to each other. They are linked only because both use the same labels. In the bonus exercise, a wrong label meant the Pods were running fine but the Service had zero endpoints.

---

## Task 3 – FQDN → [`fqdn/README.md`](fqdn/README.md)
## Task 4 – CoreDNS → [`coredns/README.md`](coredns/README.md)

## Cleanup
```bash
kubectl delete namespace s11
# make sure no tunnel or port-forward is left behind:
pkill -f "minikube tunnel"; lsof -nP -iTCP:8081 -sTCP:LISTEN
```
