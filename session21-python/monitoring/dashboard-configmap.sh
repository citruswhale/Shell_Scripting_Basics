#!/usr/bin/env bash
# Loads dashboards/gearloan-overview.json into Grafana (the sidecar picks up ConfigMaps labelled grafana_dashboard=1)
set -euo pipefail
cd "$(dirname "$0")"
kubectl create configmap gearloan-dashboard -n monitoring \
  --from-file=gearloan-overview.json=dashboards/gearloan-overview.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap gearloan-dashboard -n monitoring grafana_dashboard=1 --overwrite
