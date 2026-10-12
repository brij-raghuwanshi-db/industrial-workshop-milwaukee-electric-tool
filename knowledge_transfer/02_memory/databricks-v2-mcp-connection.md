---
name: databricks-v2-mcp-connection
description: databricks-v2 MCP is connected to the mke-rsc workspace; caveats on default + warehouse
metadata: 
  node_type: memory
  type: reference
  originSessionId: ece56b9e-b854-41db-b23e-6affa632c669
---

The **databricks-v2 MCP** server is connected to the working workspace `mke-rsc` (`https://adb-4482605715640778.18.azuredatabricks.net`). It reused the existing OAuth creds — no separate auth needed. Don't re-run `connect_to_workspace` unless it dropped.

Caveats:
- **Always pass the host/workspace explicitly** to databricks-v2 tools. The server's `default_workspace` still reports `central-logfood-prodtools-azure-westus` (a built-in fallback label), NOT mke-rsc. mke-rsc is the only connected workspace so calls resolve to it, but be explicit to be safe.
- Connection is **session-only** (dynamic host-based alias; lost if the MCP server restarts). The OAuth token is cached on disk, so reconnecting needs no re-auth.
- **No default SQL warehouse set** (`warehouse_id: null`). Anything running SQL through this MCP (Genie, ad-hoc queries) needs an explicit warehouse ID until one is chosen.

This is a SEPARATE auth surface from the `mke-rsc` CLI profile ([[mke-rsc-workspace-access]]) — the CLI/skills path and the MCP path are independent.
