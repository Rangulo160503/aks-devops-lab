#requires -Version 5.1
<#
.SYNOPSIS
    az-CLI-only bootstrap of the Terraform remote-state backend in Azure.

.DESCRIPTION
    Equivalent of `terraform apply` in `infra/bootstrap/`, for operators on
    Windows / PowerShell who prefer not to run Terraform for the bootstrap
    step. Idempotent: the storage account is discovered by tag, not by
    name, so the random suffix is preserved across reruns.

.PARAMETER Prefix
    Naming prefix. Default: pml.

.PARAMETER Location
    Azure region. Default: eastus.

.EXAMPLE
    PS> ./scripts/tf-bootstrap.ps1
    PS> ./scripts/tf-bootstrap.ps1 -Prefix pml -Location eastus

.NOTES
    Pre-conditions:
      - az CLI installed and `az login` already done.
      - Active subscription set: `az account set --subscription <id>`.
#>
[CmdletBinding()]
param(
    [string]$Prefix   = 'pml',
    [string]$Location = 'eastus'
)

$ErrorActionPreference = 'Stop'

$RgName        = "$Prefix-tfstate-rg"
$ContainerName = 'tfstate'
$TagPurpose    = 'tfstate-backend'

Write-Host "==> Verifying az CLI session"
az account show --query '{sub:name, tenant:tenantId}' -o table | Out-Null

Write-Host "==> Ensuring resource group $RgName exists in $Location"
az group create `
    --name $RgName `
    --location $Location `
    --tags "app=proyecto-ml" "cost-center=lab" "managed-by=az-cli" "purpose=$TagPurpose" `
    -o none

Write-Host "==> Looking for an existing tfstate storage account in $RgName"
$SaName = az storage account list `
    --resource-group $RgName `
    --query "[?tags.purpose=='$TagPurpose'] | [0].name" `
    -o tsv

if ([string]::IsNullOrWhiteSpace($SaName) -or $SaName -eq 'null') {
    $alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'.ToCharArray()
    $rng      = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes    = New-Object 'byte[]' 4
    $rng.GetBytes($bytes)
    $suffix   = -join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Length] })
    $SaName   = "${Prefix}tfstate$suffix"
    Write-Host "==> Creating storage account $SaName (Standard_LRS, StorageV2, AAD-only)"
    az storage account create `
        --name $SaName `
        --resource-group $RgName `
        --location $Location `
        --sku Standard_LRS `
        --kind StorageV2 `
        --access-tier Hot `
        --min-tls-version TLS1_2 `
        --https-only true `
        --allow-blob-public-access false `
        --allow-shared-key-access false `
        --public-network-access Enabled `
        --tags "app=proyecto-ml" "cost-center=lab" "managed-by=az-cli" "purpose=$TagPurpose" `
        -o none
} else {
    Write-Host "==> Reusing existing storage account $SaName"
}

Write-Host "==> Ensuring blob container '$ContainerName' exists (ARM control plane)"
az storage container-rm create `
    --storage-account $SaName `
    --resource-group $RgName `
    --name $ContainerName `
    --public-access off `
    -o none

Write-Host "==> Granting 'Storage Blob Data Contributor' to the signed-in principal"
$PrincipalId = az ad signed-in-user show --query id -o tsv 2>$null
if (-not $PrincipalId) {
    Write-Warning "Could not resolve the signed-in principal. Assign the role manually:"
    Write-Warning "  az role assignment create --role 'Storage Blob Data Contributor' --assignee <upn-or-objectid> --scope <sa-resource-id>"
} else {
    $Scope = az storage account show --name $SaName --resource-group $RgName --query id -o tsv
    az role assignment create `
        --assignee-object-id $PrincipalId `
        --assignee-principal-type User `
        --role 'Storage Blob Data Contributor' `
        --scope $Scope `
        --only-show-errors *> $null
    Write-Host "    Role assignment requested. RBAC propagation can take 1-2 minutes."
}

$RepoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
$EnvsDir = Join-Path $RepoRoot 'infra/terraform/envs'
New-Item -ItemType Directory -Force -Path $EnvsDir | Out-Null

function Write-BackendHcl {
    param([string]$Env)
    $Out = Join-Path $EnvsDir "$Env.backend.hcl"
    @"
resource_group_name  = "$RgName"
storage_account_name = "$SaName"
container_name       = "$ContainerName"
key                  = "$Env.tfstate"
use_azuread_auth     = true
"@ | Set-Content -Path $Out -Encoding UTF8 -NoNewline
    Write-Host "==> Wrote $Out"
}

Write-BackendHcl -Env 'dev'
Write-BackendHcl -Env 'prod'

Write-Host ""
Write-Host "==> Bootstrap complete."
Write-Host ""
Write-Host "    resource_group_name  = $RgName"
Write-Host "    storage_account_name = $SaName"
Write-Host "    container_name       = $ContainerName"
Write-Host ""
Write-Host "Next:"
Write-Host "    cd infra/terraform"
Write-Host "    terraform init -backend-config=envs/dev.backend.hcl"
Write-Host "    terraform plan  -var-file=envs/dev.tfvars -out=dev.tfplan"
Write-Host "    terraform apply dev.tfplan"
