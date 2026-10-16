# k8s/

Plain manifests that sit next to the Helm chart in `../helm/gearloan`.

| File | What it is | Where |
|---|---|---|
| `namespace.yaml` | `gearloan` namespace with Pod Security `restricted` labels | minikube and EKS |
| `bootstrap/storageclass-gp3.yaml` | gp3 EBS StorageClass (EBS CSI driver), default class | EKS only |
| `argocd/application.yaml` | Argo CD Application for the chart with `values-eks.yaml` | EKS only |

## Apply order

### Minikube

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install gearloan helm/gearloan -n gearloan -f helm/gearloan/values-local.yaml --wait
```

### EKS

1. Cluster add-ons first: EBS CSI driver, ingress-nginx, metrics-server,
   kube-prometheus-stack (for the ServiceMonitor) and Argo CD.
2. Storage class (the old `gp2` default should lose its default annotation):

   ```bash
   kubectl apply -f k8s/bootstrap/storageclass-gp3.yaml
   kubectl annotate storageclass gp2 storageclass.kubernetes.io/is-default-class=false --overwrite
   ```

3. Namespace and the DB password Secret (made once, never committed):

   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl create secret generic gearloan-db -n gearloan \
     --from-literal=postgres-password="$(openssl rand -hex 16)"
   ```

4. Hand the chart to Argo CD:

   ```bash
   kubectl apply -n argocd -f k8s/argocd/application.yaml
   ```

Argo CD then syncs `session21-python/helm/gearloan` from `master` on its own
(prune + self-heal). Replica counts are left to the HPA.
