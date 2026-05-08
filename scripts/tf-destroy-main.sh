#!/usr/bin/env bash
# scripts/tf-destroy-main.sh
#
# Safe destroy for the MAIN Terraform stack (`infra/terraform/`). Refuses
# to run if it sees any bootstrap resource in the current state, so a
# stray `terraform destroy` cannot ever take out the remote-state
# storage account.
#
# Usage:
#   scripts/tf-destroy-main.sh <env>
#   scripts/tf-destroy-main.sh dev
#
# Pre-conditions:
#   - `terraform init` has already been run with the right backend-config.
#   - `infra/terraform/envs/<env>.tfvars` exists.

set -euo pipefail

ENV="${1:?usage: $0 <env>   (e.g. dev, prod)}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TF_DIR="${REPO_ROOT}/infra/terraform"
TFVARS="${TF_DIR}/envs/${ENV}.tfvars"
BACKEND_HCL="${TF_DIR}/envs/${ENV}.backend.hcl"

if [ ! -f "${TFVARS}" ]; then
  echo "ERROR: tfvars not found: ${TFVARS}" >&2
  exit 2
fi
if [ ! -f "${BACKEND_HCL}" ]; then
  echo "ERROR: backend-config not found: ${BACKEND_HCL}" >&2
  echo "       Run scripts/tf-bootstrap.sh (or terraform apply in infra/bootstrap/) first." >&2
  exit 2
fi

cd "${TF_DIR}"

echo "==> Sanity check: state must not contain any bootstrap resource"
STATE_DUMP="$(terraform state list 2>/dev/null || true)"

# These tokens identify the bootstrap stack. If any of them appear in the
# main stack's state, something is very wrong and we must NOT destroy.
forbidden_patterns=(
  "tfstate-rg"
  "tfstate"
  "azurerm_role_assignment.tfstate"
  "purpose=tfstate-backend"
)
for pat in "${forbidden_patterns[@]}"; do
  if echo "${STATE_DUMP}" | grep -qi "${pat}"; then
    echo "ABORT: main-stack state contains a token matching '${pat}'." >&2
    echo "       This looks like a bootstrap resource leaked into the main stack." >&2
    echo "       Investigate before destroying. State dump:" >&2
    echo "${STATE_DUMP}" >&2
    exit 3
  fi
done

echo "==> State is clean (no bootstrap resources). Proceeding with destroy of env '${ENV}'."
read -r -p "Type the env name '${ENV}' to confirm destroy: " CONFIRM
if [ "${CONFIRM}" != "${ENV}" ]; then
  echo "Confirmation mismatch; aborting." >&2
  exit 4
fi

terraform destroy -var-file="envs/${ENV}.tfvars" -auto-approve

echo "==> Done. The bootstrap stack (pml-tfstate-rg + storage account) is untouched."
echo "    Verify with: az group show -n pml-tfstate-rg -o table"
