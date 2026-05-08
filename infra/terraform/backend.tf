# Remote state in Azure Blob Storage.
#
# This is a partial backend configuration: storage_account_name,
# container_name, key and resource_group_name are supplied at init time
# via a per-environment backend-config file:
#
#   terraform init -backend-config=envs/dev.backend.hcl
#   terraform init -backend-config=envs/prod.backend.hcl
#
# Backend authentication: Microsoft Entra ID (use_azuread_auth = true).
# No access keys, no SAS tokens, no client secrets in source. The
# bootstrap step grants the operator / pipeline principal the role
# `Storage Blob Data Contributor` on the storage account.
#
# How to produce the backend-config files:
#   - Terraform bootstrap (canonical): infra/bootstrap/  ->
#       `terraform output -raw backend_config_dev > envs/dev.backend.hcl`
#   - az-CLI fallback:                  scripts/tf-bootstrap.{sh,ps1}
#
# References:
#   https://developer.hashicorp.com/terraform/language/backend/azurerm
#   https://learn.microsoft.com/azure/developer/terraform/store-state-in-azure-storage
#   docs/terraform-bootstrap.md (in this repo)
terraform {
  backend "azurerm" {
    use_azuread_auth = true
  }
}
