provider "azurerm" {
  features {
    resource_group {
      # The bootstrap RG must NOT be deleted casually -- it holds remote state
      # for every other Terraform stack in the project.
      prevent_deletion_if_contains_resources = true
    }
  }
}
