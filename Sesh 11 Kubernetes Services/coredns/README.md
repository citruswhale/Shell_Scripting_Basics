# CoreDNS

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

Outputs below are from my Minikube cluster. Raw log: [`../outputs/06-dns-and-coredns.txt`](../outputs/06-dns-and-coredns.txt).

## What is CoreDNS?

CoreDNS is a small DNS server written in Go, built out of **plugins**. Each plugin does one job: answer for Kubernetes names, forward to the internet, cache, log, and so on. You turn plugins on in a config file called the **Corefile**.

In Kubernetes it runs as a normal Deployment in `kube-system`, behind a Service that is still named `kube-dns` for historical reasons:
```text
$ kubectl get svc kube-dns -n kube-system
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   34m

$ kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
NAME                       READY   STATUS    RESTARTS   AGE   IP
coredns-559f6c778d-qhjsr   1/1     Running   0          34m   10.244.0.2
```
Port 53 is DNS. Port 9153 is Prometheus metrics.

## Why Kubernetes uses CoreDNS

- Pods and Services are created and deleted all the time, with new IPs every time. Nobody can keep a hosts file up to date by hand.
- CoreDNS **watches the API server** and answers with the latest Services and endpoints. In my headless test, `db-1` got a new IP and DNS was right within seconds.
- It replaced the older `kube-dns` (dnsmasq + sidecars) as the default from Kubernetes 1.13, because it is one process, simpler, and easier to extend.
- It has caching, metrics and health checks built in.

## How service discovery works

1. The kubelet writes `/etc/resolv.conf` into every Pod and points it at the CoreDNS Service:
   ```text
   search s11.svc.cluster.local svc.cluster.local cluster.local
   nameserver 10.96.0.10
   options ndots:5
   ```
2. CoreDNS's `kubernetes` plugin keeps a live copy of all Services and EndpointSlices from the API server.
3. When a Pod asks for `web-clusterip`, CoreDNS answers from that copy.

So a new Service can be found by name almost right away, and nothing has to be restarted.

## How a DNS query is resolved

Example: Pod `client` in namespace `s11` runs `curl web-clusterip`.

```text
client Pod
  | 1. "web-clusterip" has fewer than 5 dots -> try the search list
  | 2. ask 10.96.0.10: web-clusterip.s11.svc.cluster.local ?
  v
kube-dns Service (10.96.0.10) --kube-proxy--> CoreDNS Pod (10.244.0.2)
  | 3. kubernetes plugin: matches cluster.local -> look it up
  | 4. answer A 10.102.106.60 (TTL 30)
  v
client connects to 10.102.106.60:80 -> kube-proxy -> a web Pod
```
For a name outside the cluster (like `example.com`), the `kubernetes` plugin doesn't match. `forward . /etc/resolv.conf` sends it to the node's upstream DNS, which here is Docker Desktop's resolver. The ExternalName test showed the full chain: CNAME `example.com` → `104.20.23.154`, `172.66.147.243`.

Logs from CoreDNS (the `log` plugin is on in Minikube):
```text
[INFO] 10.244.0.72:56189 - "AAAA IN 10-244-0-72.s11.pod.cluster.local. udp 51 false 512" NOERROR
[INFO] 10.244.0.72:59076 - "A IN does-not-exist.s11.svc.cluster.local. udp 54 false 512" NXDOMAIN
```

## CoreDNS configuration

The Corefile is stored in the ConfigMap `coredns` in `kube-system`:
```bash
kubectl get configmap coredns -n kube-system -o jsonpath='{.data.Corefile}'
```
```text
.:53 {
    log
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    hosts {
       192.168.65.254 host.minikube.internal
       fallthrough
    }
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30 {
       disable success cluster.local
       disable denial cluster.local
    }
    loop
    reload
    loadbalance
}
```

| Plugin | What it does |
|---|---|
| `.:53` | Serve every zone (`.`) on port 53 |
| `log` / `errors` | Log every query / log errors |
| `health` / `ready` | Liveness (`:8080/health`) and readiness (`:8181/ready`) endpoints used by the Pod's probes |
| `kubernetes cluster.local ...` | Answer for Services and Pods. `pods insecure` lets `10-244-0-72.s11.pod...` work. `ttl 30` = answers are valid for 30 s |
| `prometheus :9153` | Metrics for Prometheus |
| `hosts` | Minikube adds `host.minikube.internal` here so Pods can reach my Mac |
| `forward . /etc/resolv.conf` | Anything else goes to the upstream DNS |
| `cache 30` | Cache answers for 30 s (Minikube turns it off for `cluster.local` so changes show up right away) |
| `loop` | Stop if a forwarding loop is detected |
| `reload` | Pick up Corefile changes without restarting |
| `loadbalance` | Shuffle the order of A records in each answer |

To change it: `kubectl -n kube-system edit configmap coredns`. The `reload` plugin applies it after a short delay.

## How to troubleshoot DNS issues

Steps I'd follow, and the ones I tried:

1. **Check from inside a Pod, not from your laptop.** Cluster names only resolve inside the cluster.
   ```bash
   kubectl exec -n s11 client -- nslookup web-clusterip
   ```
2. **Check the Pod's resolver config.** The nameserver should be `10.96.0.10`, with the correct search list.
   ```bash
   kubectl exec -n s11 client -- cat /etc/resolv.conf
   ```
3. **Is CoreDNS itself healthy?**
   ```bash
   kubectl get pods -n kube-system -l k8s-app=kube-dns
   kubectl get endpointslices -n kube-system -l kubernetes.io/service-name=kube-dns
   kubectl logs -n kube-system -l k8s-app=kube-dns
   ```
4. **Is it a DNS problem or a Service problem?**
   - `NXDOMAIN` means the name is wrong: a typo, the wrong namespace, or the Service doesn't exist. For example, `does-not-exist.s11.svc.cluster.local` gave `NXDOMAIN`.
   - The name resolves but the connection fails: DNS is fine, so look at the Service's endpoints and selector. That was my `web-broken` case, where DNS was fine but the selector was wrong.
   - A timeout (no answer at all): the problem is reaching CoreDNS. Check the CoreDNS Pods, NetworkPolicies, and kube-proxy.
5. **Check the namespace.** `kube-dns` alone fails from `s11`; `kube-dns.kube-system` works.
6. **Test the API server name** as a known-good name: `nslookup kubernetes.default` should give `10.96.0.1`.
7. **External names fail but internal ones work:** look at the `forward` line and the node's own DNS.
8. **Slow lookups:** too many search-list attempts because of `ndots:5`. Use full names with a trailing dot, or lower `ndots` in the Pod's `dnsConfig`.

Common errors and what they usually mean:

| Error | Likely cause |
|---|---|
| `NXDOMAIN` | Wrong name or namespace; Service not created |
| `connection timed out; no servers could be reached` | CoreDNS down, or traffic to port 53 blocked |
| Name resolves, but `curl` gets exit code 7 | DNS OK; the Service has no endpoints (selector/label mismatch) |
| CoreDNS in `CrashLoopBackOff` with `loop detected` | The node's `/etc/resolv.conf` points back at CoreDNS itself |
