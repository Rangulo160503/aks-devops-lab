# Terraform — Azure infrastructure

Lab-grade Terraform that provisions: Resource Group, ACR (Basic), AKS
(Workload-Identity ready, AcrPull-bound to ACR), PostgreSQL Flexible Server
(B-series), Storage Account + `artifacts` Blob container.

```
infra/terraform/
  versions.tf          required_version + providers
  providers.tf         azurerm provider with feature flags
  backend.tf           azurerm remote-state backend (configured at init time)
  variables.tf         top-level inputs
  main.tf              wires modules together
  outputs.tf           exported values consumed by pipelines
  envs/
    dev.tfvars         dev sizing
    prod.tfvars        prod sizing
  modules/
    acr/               Azure Container Registry
    aks/               AKS + AcrPull role assignment
    postgres/          PostgreSQL Flexible Server + lab firewall + DB
    storage/           Storage account + 'artifacts' container
```

## Bootstrap (once per subscription)

The remote-state storage account must exist before `terraform init`. One
bootstrap command:

```bash
az group create -n tfstate-rg -l eastus
az storage account create -n pmlstate$RANDOM -g tfstate-rg -l eastus --sku Standard_LRS
az storage container create -n tfstate --account-name <account>
```

## Init / plan / apply

```bash
cd infra/terraform

terraform init \
  -backend-config="resource_group_name=tfstate-rg" \
  -backend-config="storage_account_name=<account>" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=dev.tfstate"

terraform plan  -var-file=envs/dev.tfvars -out=dev.tfplan
terraform apply dev.tfplan
```

## Outputs

After `apply`, useful values are emitted:

- `aks_kube_config_command` — `az aks get-credentials ...` to wire kubectl.
- `acr_login_server` — used by the CI to push images.
- `postgres_fqdn`, `postgres_admin_user`, `postgres_admin_password` (sensitive).
- `blob_account_name`, `blob_artifacts_container`.

The CI pipeline reads these via `terraform output -json` and feeds them into
the K8s deploy stage.

## Lab simplifications

- Public Postgres (locked-down with admin password); production should use a
  Private Endpoint + delegated subnet.
- ACR is Basic; production should be Premium with geo-replication.
- AKS uses the system-assigned identity for ACR pull and a single `system`
  node pool. A real cluster splits system / user pools.
- Key Vault is intentionally not provisioned — secrets are passed as K8s
  Secrets directly. Wiring KV + the Secrets Store CSI Driver is a stretch.
