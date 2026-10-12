# Milwaukee Electric Tool — Supply Chain on Databricks

This is a Databricks supply-chain project for Milwaukee Electric Tool (Milwaukee Tool / TTI).
How development is done here is defined by the **`mke-supply-chain-fde`** skill
(`.claude/skills/mke-supply-chain-fde/`). Load it for any development, design, or analysis work
and pull its matching reference file. The base rules below are non-negotiable and always apply.

## Non-negotiable data-write boundary

- **`prod_edw` and `prod_operations` are READ-ONLY.** Read, profile, query, reconcile, derive
  from, document. NEVER `INSERT / UPDATE / DELETE / MERGE / TRUNCATE / CREATE OR REPLACE /
  ALTER / DROP`, and no write-capable streaming sink, against these schemas.
- **All project writes go to `sandbox_operations.po_management`** (derived Delta tables,
  snapshots, exception outputs, projections, QA evidence, action/outcome history) **and to
  Lakebase** (transactional App state: drafts, locks, comments, approvals, action requests,
  outbox, statuses, saved searches, idempotency records).
- Lakebase→Delta publication writes only into `sandbox_operations.po_management`.
- External-system writeback (Oracle Fusion / SCC / WMS / TMS) uses a separately approved, typed,
  auditable action path — never a direct write to a Databricks production schema.
- Before any create/modify command, confirm the fully qualified destination is permitted, and
  label read-only source queries as such in implementation notes.

Example writable names: `sandbox_operations.po_management.actuals_weekly_summary`,
`…plan_vs_actual`, `…supply_exceptions`, `…demand_events_published`, `…action_outcome_history`,
`…qa_reconciliation_results`. Lakebase entities: `action_request`, `action_audit_event`,
`approval`, `exception_case`, `event_draft`, `event_lock`, `planner_comment`, `saved_search`,
`notification_delivery`, `integration_outbox`, `integration_result`.

## Base working rules

- **Learn everything, but do not overengineer where it is not needed.** Minimum sufficient
  architecture. A one-time exploration stays one well-designed query; don't inflate it into a
  framework. Equally, don't leave a production-bound workload as an unmanaged notebook.
- **Business-outcome-first, not language-first or product-first.** Don't open with "Python,
  PySpark, or SQL?" — open with the workload, grain, consumers, freshness, source-of-truth, and
  whether it's one-time / reusable / production. Reuse Databricks-managed & declarative
  capabilities before building custom. Choose products fit-for-purpose on evidence, not fashion.
- **Workspace-first, promotion-ready.** Explore in place; promote to Git / DABs / CI-CD only when
  an asset becomes reusable, scheduled, shared, governed, SLA-backed, or production-impacting.
- **Know the gotchas** for everything used (Apps SP/resource wiring, iframe/CORS/auth,
  Lakebase-UC read-only, federation pushdown, SDP limits, ResponsesAgent) — see the skill.
- **Challenge yourself** — state assumptions, weigh alternatives, name what you did not pick, and
  distinguish general industry patterns from facts verified against Milwaukee's actual systems.
- **Handoff on threshold** — when chat memory nears its limit, write a detailed handoff document
  capturing designs and decisions before continuing.

## Databricks tooling

Route Databricks work through the installed skills: load `databricks-core` (parent) plus the
matching product skill (`databricks-aibi-dashboards`, `databricks-genie-agents`,
`databricks-apps`, `databricks-lakebase`, `databricks-dabs`, `databricks-ml-training`,
`databricks-mlflow-evaluation`, etc.) — the `mke-supply-chain-fde` skill sits above them as the
project operating pattern. Never auto-select a `.databrickscfg` profile; pass `--profile <name>`
and let the user choose.

## Requirement documents

Business/requirement material and the operating-pattern discussions live in
`development_pattern/`. Treat requirement docs as domain input; don't jump straight to
developer-style analysis unless asked — understand the terms and domain first.
