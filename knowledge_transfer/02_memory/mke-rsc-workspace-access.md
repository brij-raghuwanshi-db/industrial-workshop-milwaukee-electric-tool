---
name: mke-rsc-workspace-access
description: "How to access the mke-rsc Azure Databricks workspace (OAuth U2M profile), and M2M status"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ece56b9e-b854-41db-b23e-6affa632c669
---

The target Azure Databricks workspace is accessed via the `mke-rsc` CLI profile.

- Host: `https://adb-4482605715640778.18.azuredatabricks.net`
- workspace_id: `4482605715640778`, account_id: `b623bce4-4061-4e08-8bcc-e167459ea675`
- `auth_type = databricks-cli` → genuine **OAuth U2M** (browser login, cached token auto-refreshes; no re-login needed).
- Authenticated identity: Brijendra Singh Raghuwanshi (brijendra.raghuwanshi@databricks.com).

Use it directly — do not re-run auth setup or ask which profile for this workspace:
- CLI: `databricks current-user me --profile mke-rsc`
- SDK: `WorkspaceClient(profile="mke-rsc")`
- databricks-v2 MCP: also connected to this workspace — see [[databricks-v2-mcp-connection]].

**M2M (machine-to-machine): parked, not set up.** User chose "just U2M for now". When wanted later: needs an account-admin to create a service principal + OAuth secret, then a profile with `client_id`/`client_secret` (Databricks-managed SP) or `azure_client_id`/`azure_client_secret`/`azure_tenant_id` (Entra ID SP). See [[databricks-agent-skills-install]].
