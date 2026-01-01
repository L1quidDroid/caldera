#!/bin/bash
set -euo pipefail
LOCATION=${1:-}
if [[ -z "$LOCATION" ]]; then
  echo "Usage: $0 <location>" >&2
  exit 1
fi

echo "Checking quotas in $LOCATION..."
az vm list-usage --location "$LOCATION" \
  --query "[?localName=='vCPUs'].{Name:localName,Current:currentValue,Limit:limit}" -o table
az provider list --query "[?namespace=='Microsoft.Compute'].registrationState" -o table
