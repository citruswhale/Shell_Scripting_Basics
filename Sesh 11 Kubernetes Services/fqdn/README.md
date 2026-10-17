# FQDN in Kubernetes

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

All examples below are real lookups from my Minikube cluster (namespace `s11`). Raw output: [`../outputs/06-dns-and-coredns.txt`](../outputs/06-dns-and-coredns.txt).

## What is an FQDN?

FQDN means **Fully Qualified Domain Name**: the complete name of something, all the way up to the root, so it can only mean one thing.
- `www.example.com.` is fully qualified. The final dot is the root and is usually left out.
- `www` alone is *not*. It only works if something adds the rest for you.

In Kubernetes the "rest" is added through the search list in each Pod's `/etc/resolv.conf`.

## Kubernetes Service DNS

Every Service gets a DNS name automatically. CoreDNS watches the API server, so new Services can be looked up within seconds of being created.

| Service type | DNS answer |
|---|---|
| ClusterIP / NodePort / LoadBalancer | An **A record** with the ClusterIP |
| Headless (`clusterIP: None`) | One **A record per ready Pod** |
| ExternalName | A **CNAME** to the outside name |

## The naming convention

```text
<service>.<namespace>.svc.<cluster-domain>
   |          |        |        |
web-clusterip.s11    .svc  .cluster.local
```
- `svc` means "this is a Service".
- `cluster.local` is the default cluster domain (my Corefile says `kubernetes cluster.local ...`).

Other forms:

| What | Format | Real example from my cluster |
|---|---|---|
| Service | `<svc>.<ns>.svc.cluster.local` | `web-clusterip.s11.svc.cluster.local` → `10.102.106.60` |
| StatefulSet Pod (via headless Service) | `<pod>.<headless-svc>.<ns>.svc.cluster.local` | `db-1.db-headless.s11.svc.cluster.local` → `10.244.0.77` |
| Any Pod by IP | `<ip-with-dashes>.<ns>.pod.cluster.local` | `10-244-0-72.s11.pod.cluster.local` → `10.244.0.72` |
| API server | `kubernetes.default.svc.cluster.local` | → `10.96.0.1` |
| Cluster DNS itself | `kube-dns.kube-system.svc.cluster.local` | → `10.96.0.10` |

## Namespace-based DNS

This is the `/etc/resolv.conf` inside my client Pod:
```text
search s11.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```
Because of the `search` line, a short name is tried with each suffix in turn:

| I type (from a Pod in `s11`) | Works? | Why |
|---|---|---|
| `web-clusterip` | Yes | becomes `web-clusterip.s11.svc.cluster.local` |
| `web-clusterip.s11` | Yes, from any namespace | becomes `web-clusterip.s11.svc.cluster.local` |
| `kubernetes.default` | Yes | becomes `kubernetes.default.svc.cluster.local` |
| `kube-dns` | **No** | it is in `kube-system`, not `s11` |

So **inside the same namespace the short name is enough. For another namespace, add `.<namespace>`.** The same Service name can exist in two namespaces (for example `api` in `dev` and `api` in `prod`) without clashing.

`ndots:5` means: if a name has fewer than 5 dots, try the search list first. That's why my lookup of `does-not-exist.s11.svc.cluster.local` showed up in the CoreDNS log as 4 queries:
```text
A IN does-not-exist.s11.svc.cluster.local.s11.svc.cluster.local.   NXDOMAIN
A IN does-not-exist.s11.svc.cluster.local.svc.cluster.local.       NXDOMAIN
A IN does-not-exist.s11.svc.cluster.local.cluster.local.           NXDOMAIN
A IN does-not-exist.s11.svc.cluster.local.                         NXDOMAIN
```
Tip: writing a trailing dot (`web-clusterip.s11.svc.cluster.local.`) skips the search list, which saves those extra lookups.

## Pod-to-Service communication

1. My app in Pod `client` calls `http://web-clusterip`.
2. The Pod's resolver adds the search suffix and asks `10.96.0.10` (CoreDNS).
3. CoreDNS answers `web-clusterip.s11.svc.cluster.local → 10.102.106.60`.
4. The request goes to `10.102.106.60:80`, and kube-proxy forwards it to one Pod (`10.244.0.7x:8080`).

```text
$ kubectl exec -n s11 client -- nslookup web-clusterip
Server:		10.96.0.10
Name:	web-clusterip.s11.svc.cluster.local
Address: 10.102.106.60

$ kubectl exec -n s11 client -- curl -s http://web-clusterip.s11.svc.cluster.local
web-658885c57f-4hv8d
```

## More examples of Kubernetes FQDNs

```text
web-clusterip.s11.svc.cluster.local          # Service in my namespace
example-site.s11.svc.cluster.local           # ExternalName -> CNAME example.com
db-headless.s11.svc.cluster.local            # headless -> 3 Pod IPs
db-0.db-headless.s11.svc.cluster.local       # one StatefulSet Pod
kube-dns.kube-system.svc.cluster.local       # Service in another namespace
kubernetes.default.svc.cluster.local         # the API server
```
Services with a **named** port also get SRV records like `_<port-name>._tcp.<svc>.<ns>.svc.cluster.local`. My test Services used unnamed ports, so I didn't use these.
