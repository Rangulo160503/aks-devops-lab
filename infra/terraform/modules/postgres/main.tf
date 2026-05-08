resource "random_password" "admin" {
  length      = 24
  special     = true
  min_special = 2
}

resource "azurerm_postgresql_flexible_server" "this" {
  name                          = var.name
  resource_group_name           = var.resource_group_name
  location                      = var.location
  version                       = "16"
  sku_name                      = var.sku_name
  storage_mb                    = var.storage_mb
  administrator_login           = var.admin_user
  administrator_password        = random_password.admin.result
  zone                          = "1"
  public_network_access_enabled = true
  backup_retention_days         = 7

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "proyectoml"
  server_id = azurerm_postgresql_flexible_server.this.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

# Lab-only: allow Azure-internal traffic. In a hardened deployment use a
# private endpoint + delegated subnet.
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
