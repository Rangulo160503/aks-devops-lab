variable "prefix" {
  description = "Naming prefix used for the tfstate resource group and storage account."
  type        = string
  default     = "pml"
}

variable "location" {
  description = "Azure region for the bootstrap resources."
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags applied to every bootstrap resource."
  type        = map(string)
  default = {
    app         = "proyecto-ml"
    cost-center = "lab"
    managed-by  = "terraform"
    purpose     = "tfstate-backend"
  }
}

variable "extra_principal_object_ids" {
  description = <<EOT
Optional extra Azure AD principal object IDs (users, groups, or service
principals) that should also receive the 'Storage Blob Data Contributor'
role on the tfstate storage account. The principal running this bootstrap
is added automatically.
EOT
  type        = list(string)
  default     = []
}
