# Terraform

## Layout

```
infra/terraform/
  versions.tf          required_version + providers (~> azurerm 4.5)
  providers.tf         azurerm provider with feature flags
  backend.tf           azurerm remote backend, configured at init time
  variables.tf         top-level inputs
  main.tf              wires modules together
  outputs.tf           values consumed by the deploy pipeline
  envs/{dev,prod}.tfvars
  modules/{acr,aks,postgres,storage}/
```

## Remote state bootstrap

Use the dedicated bootstrap root (recommended):

```bash
cd infra/bootstrap
terraform init
terraform apply -auto-approve
terraform output -raw backend_config_dev  > ../terraform/envs/dev.backend.hcl
terraform output -raw backend_config_prod > ../terraform/envs/prod.backend.hcl
```

Fallback (az CLI only): `scripts/tf-bootstrap.sh` or `scripts/tf-bootstrap.ps1`.
Full guide: [`docs/terraform-bootstrap.md`](terraform-bootstrap.md).

State key per environment:

| env  | key            |
|------|----------------|
| dev  | `dev.tfstate`  |
| prod | `prod.tfstate` |

## Init / plan / apply

```bash
cd infra/terraform

terraform init \
  -backend-config="envs/dev.backend.hcl"

terraform plan  -var-file=envs/dev.tfvars -out=dev.tfplan
terraform apply dev.tfplan
```

## Outputs

| Output                       | Used by                                 |
|------------------------------|-----------------------------------------|
| `aks_kube_config_command`    | Operator setting up `KUBECONFIG`        |
| `acr_login_server`           | AzDO variable group `pml-common`        |
| `aks_cluster_name`           | AzDO variable groups `pml-{env}`        |
| `postgres_fqdn`              | App `DATABASE_URL`                      |
| `postgres_admin_user/password` (sensitive) | App `DATABASE_URL`        |
| `blob_account_name`          | Optional artifact-storage wiring        |

The CD pipeline reads them via `terraform output -json` and feeds them into
the Kubernetes Secret applied to the `proyecto-ml` namespace.

## Lab simplifications

- Public Postgres + admin password (lab). Production should use a Private
  Endpoint + delegated subnet.
- ACR Basic SKU (lab). Production should be Premium with geo-replication.
- Single AKS node pool (system). Real clusters split system / user pools.
- No Key Vault module. Secrets are passed directly to K8s. A future iteration
  should add KV + Secrets Store CSI Driver.

## References

- [HashiCorp – azurerm backend](https://www.terraform.io/language/settings/backends/azurerm)
- [MS Learn – Store Terraform state in Azure Storage](https://learn.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage)
- [MS Learn – AKS + ACR integration](https://learn.microsoft.com/en-us/azure/aks/cluster-container-registry-integration)
