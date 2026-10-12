---
name: mke-workspace-dev-location
description: Where to do Databricks workspace development for the MKE project
metadata: 
  node_type: memory
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

For the MKE supply-chain project, do Databricks **workspace development** (notebooks, SQL assets, the P1
vertical slice and beyond) under a folder in **`/Workspace/Users/brijendra.raghuwanshi@databricks.com/`**
(create a project subfolder there, e.g. `.../mke_supply_chain/`). User-directed 2026-08-31.

Still holds: local repo folder `data_understanding/` holds the analysis/story/architecture markdown + the
HTML dashboard; the Databricks *runnable* assets live in the workspace folder above. Guardrail unchanged —
`prod_edw`/`prod_operations` READ-ONLY; all writes to `sandbox_operations.po_management` (verified writable;
slice tables namespaced `p1slice_*`). See [[mke-data-profiling-facts]] and [[mke-project-guardrails]].
