variable "name"                { type = string }
variable "resource_group_name" { type = string }
variable "location"            { type = string }
variable "admin_user"          { type = string }
variable "sku_name"            { type = string }
variable "storage_mb"          { type = number }
variable "tags"                { type = map(string) }
