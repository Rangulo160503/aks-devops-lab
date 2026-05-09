locals {
  rg_name        = "${var.prefix}-tfstate-rg"
  container_name = "tfstate"
}

data "azurerm_client_config" "current" {}

# Storage account names must be globally unique, lowercase alphanumeric,
# 3-24 chars. We append 4 random digits to a fixed stem so reruns don't
# clash and the name remains predictable in tags / outputs.
resource "random_string" "suffix" {
  length  = 4
  upper   = false
  special = false
  numeric = true
}

resource "azurerm_resource_group" "tfstate" {
  name     = local.rg_name
  location = var.location
  tags     = var.tags
}

# Cheapest reasonable configuration for a lab tfstate backend:
#   Standard_LRS  -- 1x local replication, lowest-cost redundancy.
#   StorageV2     -- general-purpose v2, supports Blob features the
#                    azurerm backend relies on (lease-based locking).
#   Hot           -- tfstate is small but frequently rewritten; Hot has
#                    the cheapest write cost.
# Shared access keys are enabled intentionally for this lab bootstrap flow.
# This keeps Terraform backend initialization simple and reliable.
# The configuration can be hardened later if needed.
#                    `use_azuread_auth = true` on the main backend.
# Refs:
#   https://developer.hashicorp.com/terraform/language/backend/azurerm
#   https://learn.microsoft.com/azure/storage/common/storage-redundancy
resource "azurerm_storage_account" "tfstate" {
  name                = "${var.prefix}tfstate${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.tfstate.name
  location            = azurerm_resource_group.tfstate.location

  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Hot"

  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  public_network_access_enabled   = true
  shared_access_key_enabled       = true

  blob_properties {
    versioning_enabled = false

    delete_retention_policy {
      days = 7
    }

    container_delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

# storage_account_id (ARM control plane) avoids the data-plane chicken-
# Lab compatibility note:
# shared_access_key_enabled = true simplifies the bootstrap process
# and avoids AzureRM backend authentication issues during initial setup.
# created via ARM, no AAD data-plane role needed yet.
resource "azurerm_storage_container" "tfstate" {
  name                  = local.container_name
  storage_account_id    = azurerm_storage_account.tfstate.id
  container_access_type = "private"

  lifecycle {
    prevent_destroy = true
  }
}

# Grant the principal that ran `terraform apply` (operator via az CLI,
# or a service principal in CI) the data-plane role required by the
# main stack's azurerm backend with `use_azuread_auth = true`.
resource "azurerm_role_assignment" "tfstate_current_principal" {
  scope                = azurerm_storage_account.tfstate.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
  description          = "Bootstrap-granted access for the principal running Terraform."
}

# Optional: hand the same role to additional users / groups / SPs.
resource "azurerm_role_assignment" "tfstate_extra_principals" {
  for_each             = toset(var.extra_principal_object_ids)
  scope                = azurerm_storage_account.tfstate.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = each.value
  description          = "Additional principal granted access at bootstrap time."
}
