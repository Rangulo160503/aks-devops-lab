#!/usr/bin/env bash
# scripts/tf-bootstrap.sh
#
# az-CLI-only bootstrap of the Terraform remote-state backend in Azure.
# Equivalent of `terraform apply` in `infra/bootstrap/`, for operators who
# prefer not to run Terraform for the bootstrap step.
#
# Idempotent: re-running on an already-bootstrapped subscription is a
# no-op. The storage account is discovered by tag, not by name, so the
# random suffix is preserved across runs.
#
# Pre-conditions:
#   - az CLI installed and `az login` already done.
#   - Active subscription set: `az account set --subscription <id>`.
#
# Usage:
#   scripts/tf-bootstrap.sh                 # all defaults
#   PREFIX=pml LOCATION=eastus scripts/tf-bootstrap.sh
#
# Output: writes infra/terraform/envs/{dev,prod}.backend.hcl on success.

set -euo pipefail

PREFIX="${PREFIX:-pml}"
LOCATION="${LOCATION:-eastus}"
RG_NAME="${PREFIX}-tfstate-rg"
CONTAINER_NAME="tfstate"
SA_TAG_PURPOSE="tfstate-backend"

echo "==> Verifying az CLI session"
az account show --query '{sub:name, tenant:tenantId}' -o table >/dev/null

echo "==> Ensuring resource group ${RG_NAME} exists in ${LOCATION}"
az group create \
  --name "${RG_NAME}" \
  --location "${LOCATION}" \
  --tags app=proyecto-ml cost-center=lab managed-by=az-cli purpose="${SA_TAG_PURPOSE}" \
  -o none

echo "==> Looking for an existing tfstate storage account in ${RG_NAME}"
SA_NAME="$(az storage account list \
  --resource-group "${RG_NAME}" \
  --query "[?tags.purpose=='${SA_TAG_PURPOSE}'] | [0].name" \
  -o tsv 2>/dev/null || true)"

if [ -z "${SA_NAME}" ] || [ "${SA_NAME}" = "null" ]; then
  SUFFIX="$(head -c 16 /dev/urandom | tr -dc 'a-z0-9' | head -c 4)"
  SA_NAME="${PREFIX}tfstate${SUFFIX}"
  echo "==> Creating storage account ${SA_NAME} (Standard_LRS, StorageV2, AAD-only)"
  az storage account create \
    --name "${SA_NAME}" \
    --resource-group "${RG_NAME}" \
    --location "${LOCATION}" \
    --sku Standard_LRS \
    --kind StorageV2 \
    --access-tier Hot \
    --min-tls-version TLS1_2 \
    --https-only true \
    --allow-blob-public-access false \
    --allow-shared-key-access false \
    --public-network-access Enabled \
    --tags app=proyecto-ml cost-center=lab managed-by=az-cli purpose="${SA_TAG_PURPOSE}" \
    -o none
else
  echo "==> Reusing existing storage account ${SA_NAME}"
fi

echo "==> Ensuring blob container '${CONTAINER_NAME}' exists (ARM control plane)"
az storage container-rm create \
  --storage-account "${SA_NAME}" \
  --resource-group "${RG_NAME}" \
  --name "${CONTAINER_NAME}" \
  --public-access off \
  -o none

echo "==> Granting 'Storage Blob Data Contributor' to the signed-in principal"
PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"
if [ -z "${PRINCIPAL_ID}" ]; then
  # Service-principal sessions can't query signed-in-user; fall back.
  PRINCIPAL_ID="$(az account show --query user.name -o tsv)"
  PRINCIPAL_ID="$(az ad sp list --display-name "${PRINCIPAL_ID}" --query '[0].id' -o tsv 2>/dev/null || true)"
fi

if [ -n "${PRINCIPAL_ID}" ]; then
  SCOPE="$(az storage account show \
    --name "${SA_NAME}" \
    --resource-group "${RG_NAME}" \
    --query id -o tsv)"
  # `--only-show-errors` keeps the script quiet on the "already exists" path.
  az role assignment create \
    --assignee-object-id "${PRINCIPAL_ID}" \
    --assignee-principal-type User \
    --role "Storage Blob Data Contributor" \
    --scope "${SCOPE}" \
    --only-show-errors >/dev/null 2>&1 || true
  echo "    Role assignment requested. RBAC propagation can take 1-2 minutes."
else
  echo "    WARNING: could not resolve current principal; assign the role manually:"
  echo "      az role assignment create --role 'Storage Blob Data Contributor' \\"
  echo "        --assignee <upn-or-objectid> \\"
  echo "        --scope /subscriptions/<sub>/resourceGroups/${RG_NAME}/providers/Microsoft.Storage/storageAccounts/${SA_NAME}"
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENVS_DIR="${REPO_ROOT}/infra/terraform/envs"
mkdir -p "${ENVS_DIR}"

write_backend_hcl() {
  local env="$1"
  local out="${ENVS_DIR}/${env}.backend.hcl"
  cat > "${out}" <<EOT
resource_group_name  = "${RG_NAME}"
storage_account_name = "${SA_NAME}"
container_name       = "${CONTAINER_NAME}"
key                  = "${env}.tfstate"
use_azuread_auth     = true
EOT
  echo "==> Wrote ${out}"
}

write_backend_hcl dev
write_backend_hcl prod

cat <<EOT

==> Bootstrap complete.

    resource_group_name  = ${RG_NAME}
    storage_account_name = ${SA_NAME}
    container_name       = ${CONTAINER_NAME}

Next:
    cd infra/terraform
    terraform init -backend-config=envs/dev.backend.hcl
    terraform plan  -var-file=envs/dev.tfvars -out=dev.tfplan
    terraform apply dev.tfplan
EOT
