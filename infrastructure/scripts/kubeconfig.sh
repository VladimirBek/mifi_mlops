#!/usr/bin/env bash
set -euo pipefail

CLUSTER_ID="${1:-}"
FOLDER_ID="${2:-}"
SA_KEY_PATH="${3:-}"

if [ -z "$CLUSTER_ID" ] || [ -z "$FOLDER_ID" ] || [ -z "$SA_KEY_PATH" ]; then
  echo "Usage: kubeconfig.sh <cluster_id> <folder_id> <service_account_key.json>"
  exit 1
fi

yc config set service-account-key "$SA_KEY_PATH"
yc managed-kubernetes cluster get-credentials "$CLUSTER_ID" --folder-id "$FOLDER_ID" --external

kubectl get nodes
