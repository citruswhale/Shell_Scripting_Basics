# Ingress vs Ingress Controller

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

## What is an Ingress?

An **Ingress** is a Kubernetes object (a YAML file) that holds **routing rules** for HTTP/HTTPS traffic coming into the cluster. For example:
- `gearloan.local/api` → Service `api`
- `gearloan.local/` → Service `frontend`
- `admin.gearloan.local` → Service `admin`
- use TLS certificate `X` for `gearloan.local`

It is only a description. On its own, an Ingress does **nothing**: no Pod, no port, no process.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gearloan
spec:
  ingressClassName: nginx
  rules:
    - host: gearloan.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service: { name: api, port: { number: 80 } }
```

## What is an Ingress Controller?

An **Ingress Controller** is the actual **program running in the cluster**: a reverse proxy or load balancer. It watches Ingress objects through the API server and **turns those rules into real config**. Then it receives the traffic and forwards it to the right Pods.

In my lab it is **ingress-nginx**:
```text
$ kubectl get pods,svc -n ingress-nginx
pod/ingress-nginx-controller-d7cd8c989-n5khv   1/1     Running
service/ingress-nginx-controller   NodePort   10.110.179.74   80:32082/TCP,443:30227/TCP

$ kubectl get ingressclass
NAME              CONTROLLER             PARAMETERS   AGE
nginx (default)   k8s.io/ingress-nginx   <none>       3m28s
```
When I created my Ingress, the controller logged an event for it, generated its nginx config, and started routing. Its access log showed each request going to `[s12-api-80]` or `[s12-frontend-80]`.

## Difference

| | Ingress | Ingress Controller |
|---|---|---|
| What it is | A Kubernetes **resource** (rules) | A **running app** (Pods + Service) |
| Who writes it | Me, the app developer | Installed once by the cluster admin (Helm, addon, cloud) |
| What it does | Says *where* traffic should go | Actually *moves* the traffic |
| Comes with Kubernetes? | Yes, the API type is built in | **No**, you must install one |
| How many | One per app or team, many in total | Usually one or two per cluster |
| Linked by | `spec.ingressClassName: nginx` | the `IngressClass` named `nginx` |

A simple way to think of it: the Ingress is the **map**, the controller is the **driver** who reads the map.

## Why both are required

- **Only an Ingress, no controller:** the object is accepted, but nothing ever reads it. `ADDRESS` stays empty and every request fails.
- **Only a controller, no Ingress:** the proxy runs but has no rules, so it answers everything with its default `404`. I saw that for the unknown host `something-else.local`.

Keeping them separate means app teams can change routes with a small YAML file without touching the proxy. It also means you can swap the proxy (nginx → Traefik → AWS ALB) and keep the same Ingress files.

## Examples of Ingress Controllers

| Controller | Notes |
|---|---|
| **ingress-nginx** | The one I used. Community project, built on NGINX |
| **AWS Load Balancer Controller** | Creates a real AWS ALB for each Ingress (EKS) |
| GKE Ingress | Creates a Google Cloud HTTP(S) Load Balancer |
| Traefik | Default in k3s; auto config, Let's Encrypt |
| HAProxy Ingress, Kong, Contour (Envoy), Istio gateway | Other common choices |

Newer clusters can also use the **Gateway API** (`Gateway` + `HTTPRoute`). It is the follow-up to Ingress with the same idea, rules vs implementation, but more flexible.
