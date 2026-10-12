---
name: mcp-servers-status
description: Which MCP servers are connected/usable in this project (probed 2026-08-30)
metadata: 
  node_type: memory
  type: reference
  originSessionId: ece56b9e-b854-41db-b23e-6affa632c669
---

MCP servers available in this project, all probed live on 2026-08-30 (9 total, all non-blocking):

- **confluence** — live (Databricks Confluence: Universe, Field Engineering, KB, etc.)
- **github** — live; PR read/write + CI/CD. Org defaults to `databricks-eng` for universe/runtime.
- **jira** — live; user is allow-listed for issue create ops. JQL search; ADF required for rich-text writes.
- **slack** — live; channels, messages, Lists, batch ops.
- **safe** — live; feature-flag read/write/merge (SAFE).
- **google** — live; Gmail/Calendar/Drive/Docs/Sheets/Slides/Tasks as brijendra.raghuwanshi@databricks.com.
- **storage-console** — live; DB-infra tooling.
- **web-search** — live; via Databricks AI Gateway.
- **databricks-v2** — live and connected to `mke-rsc`; see [[databricks-v2-mcp-connection]].

Note: databricks-v2 was the only one that needed wiring (was 0 workspaces connected); now pointed at mke-rsc.
