# `infra/bootstrap/` — Terraform remote-state bootstrap

A tiny Terraform root that creates the Azure resources the **main** stack
(`infra/terraform/`) needs as its `azurerm` remote-state backend.

This stack uses **local state** on purpose. It is the only stack in the
repo that does — every other stack stores its state in the storage
account this stack creates. Without this split, `terraform init` of the
main stack would prompt for backend values that do not exist yet.

## What it creates

| Resource         | Name                          | Notes                                  |
|------------------|-------------------------------|----------------------------------------|
| Resource Group   | `pml-tfstate-rg`              | Region: `eastus`                       |
| Storage Account  | `pmltfstate<random4>`         | `Standard_LRS`, `StorageV2`, Hot, AAD-only |
| Blob Container   | `tfstate`                     | Private; holds `dev.tfstate`, `prod.tfstate` |
| Role Assignment  | `Storage Blob Data Contributor` | Granted to the principal running Terraform |

Cost target: ~USD 0.02 / month for tfstate-sized blobs.

## Safety properties

- **Separate root**, separate Resource Group, **`prevent_destroy = true`**
  on the storage account and container. A `terraform destroy` of the
  main stack cannot touch any of this.
- **AAD-only data plane** (`shared_access_key_enabled = false`) — matches
  the main stack's `backend.tf` which has `use_azuread_auth = true`.
- **Container created via ARM** (`storage_account_id`), so creation does
  not depend on a data-plane role being already in place.

## Prerequisites

- Azure CLI logged in: `az login`
- Active subscription set: `az account set --subscription <sub-id>`
- Terraform >= 1.7.0

## Usage

```bash
cd infra/bootstrap

terraform init
terraform plan  -out=bootstrap.tfplan
terraform apply bootstrap.tfplan
```

The plan creates 5 resources and finishes in ~30 seconds. After apply:

```bash
# Generate the backend-config files the main stack consumes.
terraform output -raw backend_config_dev  > ../terraform/envs/dev.backend.hcl
terraform output -raw backend_config_prod > ../terraform/envs/prod.backend.hcl
```

## Running it again

`terraform apply` is **idempotent**. Re-running it is a no-op as long as
nothing drifts. The random suffix is stored in local state, so the
storage account name does not change across runs.

## Destroying

You almost never want to destroy this stack — doing so erases the remote
state for every environment. The `prevent_destroy` lifecycle flags will
block a casual `terraform destroy` and force you to remove them
intentionally first. See `docs/terraform-bootstrap.md` for the full
intentional-destroy procedure.

## References

- [Backend Type: azurerm](https://developer.hashicorp.com/terraform/language/backend/azurerm)
- [Azure Storage redundancy options](https://learn.microsoft.com/azure/storage/common/storage-redundancy)
- [Store Terraform state in Azure Storage](https://learn.microsoft.com/azure/developer/terraform/store-state-in-azure-storage)
