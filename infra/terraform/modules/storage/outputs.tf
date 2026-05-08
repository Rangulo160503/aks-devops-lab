output "account_name"        { value = azurerm_storage_account.this.name }
output "primary_blob_endpoint" { value = azurerm_storage_account.this.primary_blob_endpoint }
output "artifacts_container" { value = azurerm_storage_container.artifacts.name }
