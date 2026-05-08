output "fqdn"           { value = azurerm_postgresql_flexible_server.this.fqdn }
output "admin_user"     { value = var.admin_user }
output "admin_password" {
  value     = random_password.admin.result
  sensitive = true
}
output "database_name"  { value = azurerm_postgresql_flexible_server_database.app.name }
