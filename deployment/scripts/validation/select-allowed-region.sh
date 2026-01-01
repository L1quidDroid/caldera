#!/usr/bin/env bash
set -euo pipefail
# Discover an allowed region from policy and write bicep/parameters/homelab-allowed.json

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PARAM_SRC="$ROOT/bicep/parameters/homelab.parameters.json"
PARAM_OUT="$ROOT/bicep/parameters/homelab-allowed.json"
DEFAULT_FALLBACK="westus2"

pick_allowed_region() {
  local region
  # Try policy allowed locations first
  region=$(az policy state list \
    --query "[?contains(policyDefinitionName,'Allowed locations')].policyAssignmentParameters.allowedLocations.value | []" \
    -o tsv 2>/dev/null | tr '\t' '\n' | sort -u | head -n1 || true)

  if [[ -z "${region:-}" ]]; then
    # Fallback to common student-safe US regions
    region=$(az account list-locations \
      --query "[?contains(name,'eastus') || contains(name,'centralus') || contains(name,'westus')].name | [0]" \
      -o tsv 2>/dev/null || true)
  fi

  if [[ -z "${region:-}" ]]; then
    region="$DEFAULT_FALLBACK"
  fi

  echo "$region"
}

REGION=$(pick_allowed_region)

python3 - "$PARAM_SRC" "$PARAM_OUT" "$REGION" <<'PY'
import json, sys, pathlib
src, dst, region = sys.argv[1:]
data = json.loads(pathlib.Path(src).read_text())
data["parameters"]["location"]["value"] = region
pathlib.Path(dst).write_text(json.dumps(data, indent=2))
print(f"wrote {dst} with location={region}")
PY

echo "Using region: ${REGION}" >&2
echo "Updated file: ${PARAM_OUT}" >&2
echo "Deploy with:" >&2
echo "az deployment sub create \\
  --location ${REGION} \\
  --template-file ${ROOT}/bicep/main.bicep \\
  --parameters @${PARAM_OUT}" >&2
