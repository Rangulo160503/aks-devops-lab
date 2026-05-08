locals {
  base_name = "${var.prefix}-${var.env}"
  tags      = merge(var.tags, { env = var.env })
}

resource "azurerm_resource_group" "main" {
  name     = "${local.base_name}-rg"
  location = var.location
  tags     = local.tags
}

module "acr" {
  source              = "./modules/acr"
  name                = replace("${local.base_name}acr", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

module "aks" {
  source              = "./modules/aks"
  name                = "${local.base_name}-aks"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  dns_prefix          = local.base_name
  kubernetes_version  = var.aks_kubernetes_version
  node_count          = var.aks_node_count
  node_size           = var.aks_node_size
  acr_id              = module.acr.id
  tags                = local.tags
}

module "storage" {
  source              = "./modules/storage"
  name                = replace("${local.base_name}st", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  account_tier        = var.storage_account_tier
  replication         = var.storage_replication
  tags                = local.tags
}

module "postgres" {
  source              = "./modules/postgres"
  name                = "${local.base_name}-pg"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  admin_user          = var.pg_admin_user
  sku_name            = var.pg_sku_name
  storage_mb          = var.pg_storage_mb
  tags                = local.tags
}
