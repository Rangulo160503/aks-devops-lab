# Remote state in Azure Blob Storage. The actual values are passed via
# `terraform init -backend-config=...` from the pipeline / scripts to keep
# secrets out of source control. Bootstrap is documented in
# infra/terraform/README.md.
#
# Reference:
#   https://developer.hashicorp.com/terraform/language/settings/backends/azurerm
#   https://learn.microsoft.com/azure/developer/terraform/store-state-in-azure-storage
terraform {
  backend "azurerm" {
    use_azuread_auth = true
    # resource_group_name  = "<set via -backend-config>"
    # storage_account_name = "<set via -backend-config>"
    # container_name       = "<set via -backend-config>"
    # key                  = "<env>.tfstate"
  }
}
