output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "acr_login_server" {
  value = module.acr.login_server
}

output "aks_cluster_name" {
  value = module.aks.name
}

output "aks_kube_config_command" {
  value       = "az aks get-credentials -g ${azurerm_resource_group.main.name} -n ${module.aks.name}"
  description = "Run this to populate ~/.kube/config."
}

output "postgres_fqdn" {
  value = module.postgres.fqdn
}

output "postgres_admin_user" {
  value = module.postgres.admin_user
}

output "postgres_admin_password" {
  value     = module.postgres.admin_password
  sensitive = true
}

output "blob_account_name" {
  value = module.storage.account_name
}

output "blob_artifacts_container" {
  value = module.storage.artifacts_container
}
