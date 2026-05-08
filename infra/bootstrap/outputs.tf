output "resource_group_name" {
  description = "Resource group containing the tfstate storage account."
  value       = azurerm_resource_group.tfstate.name
}

output "storage_account_name" {
  description = "Storage account holding the tfstate blobs."
  value       = azurerm_storage_account.tfstate.name
}

output "container_name" {
  description = "Blob container for *.tfstate files."
  value       = azurerm_storage_container.tfstate.name
}

# Ready-to-paste backend-config files for the main stack. Run:
#   terraform output -raw backend_config_dev  > ../terraform/envs/dev.backend.hcl
#   terraform output -raw backend_config_prod > ../terraform/envs/prod.backend.hcl
output "backend_config_dev" {
  description = "Drop into infra/terraform/envs/dev.backend.hcl"
  value       = <<EOT
resource_group_name  = "${azurerm_resource_group.tfstate.name}"
storage_account_name = "${azurerm_storage_account.tfstate.name}"
container_name       = "${azurerm_storage_container.tfstate.name}"
key                  = "dev.tfstate"
use_azuread_auth     = true
EOT
}

output "backend_config_prod" {
  description = "Drop into infra/terraform/envs/prod.backend.hcl"
  value       = <<EOT
resource_group_name  = "${azurerm_resource_group.tfstate.name}"
storage_account_name = "${azurerm_storage_account.tfstate.name}"
container_name       = "${azurerm_storage_container.tfstate.name}"
key                  = "prod.tfstate"
use_azuread_auth     = true
EOT
}

# Human-friendly init command line for the dev environment.
output "terraform_init_dev_command" {
  description = "Copy/paste init command for the dev main stack."
  value = format(
    "terraform -chdir=../terraform init -backend-config=envs/dev.backend.hcl"
  )
}
