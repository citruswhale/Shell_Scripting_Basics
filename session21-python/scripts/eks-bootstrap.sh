#!/usr/bin/env bash
# Sets up the EKS cluster made by terraform/ so Argo CD can run GearLoan on it.
# Run from session21-python/ after `terraform apply`.
#   ./scripts/eks-bootstrap.sh
# Needs: aws (profile devops-lab), kubectl, helm. Secrets are generated here and never written to git.
set -euo pipefail

REGION="${REGION:-ap-south-1}"
CLUSTER="${CLUSTER:-gearloan-eks}"
PROFILE="${AWS_PROFILE:-devops-lab}"
CTX="gearloan-eks"                         # kubeconfig context name (keeps Minikube's context separate)
INGRESS_NGINX_VERSION="4.15.1"             # helm chart versions, pinned
METRICS_SERVER_VERSION="3.14.0"
KPS_VERSION="92.10.1"
ARGOCD_VERSION="v3.5.5"
# AWS Free plan accounts can't create load balancers. Then run with INGRESS_SERVICE_TYPE=NodePort and
# reach the app through the ingress controller with kubectl port-forward (see README).
INGRESS_SERVICE_TYPE="${INGRESS_SERVICE_TYPE:-LoadBalancer}"

k() { kubectl --context "$CTX" "$@"; }
h() { helm --kube-context "$CTX" "$@"; }

echo "== kubeconfig"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER" --profile "$PROFILE" --alias "$CTX"
k get nodes -o wide

echo "== storage: gp3 as the default StorageClass (EBS CSI driver add-on is installed by Terraform)"
k apply -f k8s/bootstrap/storageclass-gp3.yaml
if k get storageclass gp2 >/dev/null 2>&1; then
  k annotate storageclass gp2 storageclass.kubernetes.io/is-default-class=false --overwrite
fi

echo "== helm repos"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null 2>&1 || true
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null 2>&1 || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null

echo "== metrics-server (needed by the HPA and kubectl top)"
h upgrade --install metrics-server metrics-server/metrics-server --version "$METRICS_SERVER_VERSION" \
  -n kube-system --wait --timeout 5m

echo "== ingress-nginx (creates one AWS Network Load Balancer)"
h upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version "$INGRESS_NGINX_VERSION" \
  -n ingress-nginx --create-namespace \
  --set controller.service.type="$INGRESS_SERVICE_TYPE" \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"=nlb \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-scheme"=internet-facing \
  --wait --timeout 10m

echo "== kube-prometheus-stack (Prometheus, Alertmanager, Grafana)"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-$(openssl rand -hex 12)}"
h upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version "$KPS_VERSION" \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml \
  --set grafana.adminPassword="$GRAFANA_PASSWORD" --wait --timeout 15m
k apply -f monitoring/gearloan-alerts.yaml
kubectl config use-context "$CTX" >/dev/null && ./monitoring/dashboard-configmap.sh

echo "== Argo CD $ARGOCD_VERSION"
k create namespace argocd --dry-run=client -o yaml | k apply -f -
k apply -n argocd --server-side --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml" >/dev/null
k wait -n argocd --for=condition=Available deploy --all --timeout=10m

echo "== GearLoan namespace + DB password Secret (made once, not in git)"
k apply -f k8s/namespace.yaml
if ! k get secret gearloan-db -n gearloan >/dev/null 2>&1; then
  k create secret generic gearloan-db -n gearloan --from-literal=postgres-password="$(openssl rand -hex 16)"
fi

echo "== hand the chart to Argo CD"
k apply -n argocd -f k8s/argocd/application.yaml

echo
echo "Done. Grafana admin password: kept only in this shell (GRAFANA_PASSWORD)."
LB=$(k get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ -n "$LB" ]; then echo "App URL: http://$LB"; else echo "No load balancer. Open the app with: kubectl --context $CTX port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80  ->  http://localhost:8080"; fi
