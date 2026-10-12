---
name: mke-project-guardrails
description: "Non-negotiable base rules for the MKE supply-chain project — read-only prod, sandbox+Lakebase writes, no overengineering, handoff on threshold"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed081939-8656-4083-b3da-17ba19979798
---

Non-negotiable rules for the Milwaukee Electric Tool supply-chain Databricks project:

- **`prod_edw` and `prod_operations` are READ-ONLY.** No INSERT/UPDATE/DELETE/MERGE/TRUNCATE/
  CREATE OR REPLACE/ALTER/DROP and no write-capable streaming sink against them.
- **All writes go to `sandbox_operations.po_management`** (derived Delta, snapshots, exception
  outputs, QA evidence, action/outcome history) **and Lakebase** (transactional App state).
  Lakebase→Delta publication writes only into `sandbox_operations.po_management`.
- External-system writeback (Oracle Fusion/SCC/WMS/TMS) goes through a separately approved,
  typed, auditable action path — never a direct write to a Databricks production schema.
- **NO real Oracle (or any external) write-back — ever, in this engagement.** Even when we reach
  the action/PO-execution stage (Red Keychain territory: approve/reject, PO cancel/resize/expedite),
  the write-back is **simulated in `sandbox_operations.po_management` + Lakebase**, not sent to
  Oracle. Model the typed action request, approval, outbox, and result as sandbox records so the
  full loop is demonstrable and auditable; the actual external push is explicitly out of scope until
  the business stands up the approved integration lane. (User directive 2026-08-31.)
- **The guardrail overrides the requirement docs on write location.** The customer docs name
  `prod_operations` (Actuals D5) and `prod_edw.staging_flat_files.expansion_dims`/`expansion_loads`
  (Demand Events output) — but we write ALL of these to `sandbox_operations.po_management`
  (including sandbox `expansion_dims`/`expansion_loads`, keeping the doc's column contract so they
  stay publish-compatible). Oracle Demand Planning Cloud Fusion receives the `expansion_*` data via
  a governed publish step from sandbox, never a direct `prod_edw` write.
- **Do not overengineer** — minimum sufficient architecture; a one-time query stays a query.
- **Challenge yourself**; **write a handoff doc** when chat memory nears its threshold.

**Why:** the user set these as the one-and-only hard boundaries for the project; violating the
write boundary risks corrupting authoritative EDW/operations data.

**How to apply:** before any create/modify command, confirm the fully qualified destination is
permitted; label read-only source queries as such. Full operating pattern is in the
[[mke-operating-pattern]] skill and project `CLAUDE.md`.
