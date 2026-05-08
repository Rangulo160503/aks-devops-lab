variable "prefix" {
  description = "Naming prefix for resources (e.g. 'pml')."
  type        = string
  default     = "pml"
}

variable "env" {
  description = "Environment short name (dev, staging, prod)."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default = {
    app         = "proyecto-ml"
    cost-center = "lab"
    managed-by  = "terraform"
  }
}

# AKS
variable "aks_node_count" {
  type    = number
  default = 2
}

variable "aks_node_size" {
  type    = string
  default = "Standard_B2s"
}

variable "aks_kubernetes_version" {
  type    = string
  default = "1.30"
}

# Postgres
variable "pg_admin_user" {
  type    = string
  default = "proyectoml"
}

variable "pg_sku_name" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "pg_storage_mb" {
  type    = number
  default = 32768
}

# Storage account (for Blob artifacts)
variable "storage_account_tier" {
  type    = string
  default = "Standard"
}

variable "storage_replication" {
  type    = string
  default = "LRS"
}
