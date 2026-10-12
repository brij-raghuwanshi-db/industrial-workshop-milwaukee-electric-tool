# Data Understanding — MKE Supply Chain (P1–P4)

**Purpose:** Build a *queried, evidence-backed* understanding of the underlying datasets behind the
four project priorities — NOT to build pipelines or joined queries yet. We characterize each table's
grain, keys, real value distributions, coverage, and *unique standing* (what only this table can
tell us), so we can reason about scenarios and deliverables.

**Method:** Every claim here is backed by a query run live against the workspace, not assumed from
the requirement docs. Where a doc-named table is missing or a column differs, that is recorded
explicitly.

## Workspace / connection (validated 2026-08-30)
- **Profile:** `mke-rsc` → `https://adb-4482605715640778.18.azuredatabricks.net` (OAuth U2M, valid)
- **User:** brijendra.raghuwanshi@databricks.com
- **Default warehouse id:** `7bd33a82f4e92206`
- **Catalogs present:** `prod_edw`, `prod_operations`, `sandbox_operations`, `main`, `samples`, `system`

## GUARDRAIL (non-negotiable)
`prod_edw` and `prod_operations` are **READ-ONLY**. This activity is **SELECT / DESCRIBE / profiling
only**. No INSERT/UPDATE/DELETE/MERGE/CREATE/ALTER/DROP against any prod schema. Findings files are
written to the **local filesystem only** (this folder), never to a Databricks table.

## Folder layout
- `README.md` — this file
- `_recipe.md` — the exact, copy-paste query recipe + profiling conventions handed to each subagent
- `00_table_priority_map.md` — master map: every doc-named table → which priorities use it, status
- `subagent_findings/` — one markdown file per table cluster, written by parallel subagents
- `SYNTHESIS.md` — the consolidated P1/P2/P3/P4 understanding (written after subagents complete)
- `data_stories/` — **query-driven data journeys & scenario coverage** (Phase 2): 39 files tracing real
  anchor IDs through the tables. **Start at `data_stories/INDEX.md`**; scenario→priority tags in
  `data_stories/PRIORITY_MAP.md`; out-of-scope signals in `data_stories/BEYOND_P1P4_scenarios.md`; the
  narrative of the extraction pain in `data_stories/THE_SEARCH_PAIN_JOURNEY.md`.
- `solution_architecture/` — **how Databricks removes the documented pain** (Phase 3). **Start at
  `solution_architecture/00_CAPSTONE.md`**; then 01 medallion foundation, 02 analytical+transactional,
  03 AI/decision products (Genie/AI-Functions/Agent-Bricks/Lakebase-Search-BM25/MLflow-eval),
  04 complete landscape + financials. Maps each pain → the medallion + semantic + serving + AI cure.

## Table → priority coverage (planned; confirmed live in 00_table_priority_map.md)
| Cluster | Tables | Priorities | Subagent |
|---|---|---|---|
| A. Supply plan snapshot + plans dim | `20_supply_daily`, `supply_and_demand_plans_scd1` | P1, P2 | A |
| B. Actuals transactional sources | `receiving_receipt_transactions`, `sales_order_line_transactions`, `inventory_days_on_hand`, `purchase_order_delivery`(dep), `purchase_orders` | P1, P2 | B |
| C. Shared dimensions | `items_scd1`, `date_scd1`, `inventory_organization_scd1`, `dim_series_ext_vw` | P1, P2, P3, P4 | C |
| D. Demand side | `10_demand_daily`, `dg5_customer_scd1`, `expansion_dims`, `expansion_loads` | P3, P4 | D |
| E. Supporting / root-cause | `order_line_fulfillment_accumulating_snapshot`, `customer_shipments`, `inventory_material_transaction`, `inventory_on_hand_temporal` | P1, P2 | E |

Status legend used throughout: **Profiled** (queried live) / **Exists-not-profiled** / **Missing**
(named in docs, not found) / **Deprecated**.
