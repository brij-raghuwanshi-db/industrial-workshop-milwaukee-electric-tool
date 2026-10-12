---
name: mke-data-profiling-facts
description: Workspace-verified facts about MKE P1-P4 source tables (profiled live 2026-08-30)
metadata: 
  node_type: memory
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

Live-profiled the MKE source tables on profile `mke-rsc` (warehouse `7bd33a82f4e92206`) on
2026-08-30. Findings live in `data_understanding/` (README, 00_table_priority_map.md, SYNTHESIS.md,
subagent_findings/A–E). Key verified facts (supersede doc assumptions):

- **`prod_edw.fact.20_supply_daily`**: 13.4B rows, 366 daily snapshots (process_date 20250628→20260829,
  yyyyMMdd INT). Within one snapshot, `date_key` buckets are **WEEKLY, Monday-aligned**, forward
  horizon ~**111 weeks (~2 yrs)** — NOT 55 years (subagent A miscalc; my direct query is authoritative).
  True grain = plan_id × date_key × product_bigint_key × inventory_organization_bigint_key ×
  series_bigint_key × order_type_bigint_key (41M rows/snapshot vs 27.5M for the 4-col key). on_hand/
  PAB/safety_stock are point-in-time (semi-additive; never sum across date_key). Plans `20 Global
  Supply Plan` + `20 Mexico Supply Plan` confirmed (plan_type 2). Plan filter column = `plan_name`.
- **Item "Status 20"** (P3/P4 validation): literal is **`item_status = 'PurchPlan'`** (= `item_status_name`
  '20.Ready to Purchase or Plan Production'); 8,716 of 299,966 items. The doc's `item_status_description`
  is truncated ("Productio") — filter on `item_status`, not the description. Resolves open-item #1.
- **Orgs**: `inventory_organization_scd1` has org_code; 2012 = Olive Branch (US), 2120 = Mexico both confirmed.
- **`receiving_receipt_transactions`** (PO receipts actual) uses **RAW Oracle ids** (organization_id ~3e14,
  po_header_id, item_id) NOT EDW bigint keys → **crosswalk required** before joining to plan/dims.
  transaction_type RECEIVE 49.7% + DELIVER 49.7% (pick ONE to avoid double count). 72.8% null po_header_id.
- **`inventory_days_on_hand`**: 2.73B rows, item×org×date_key, 699 daily dates, ZERO negatives (clean);
  point-in-time. **`inventory_material_transaction`** = the 27-type root-cause ledger (Sales Order Issue,
  Subinventory Transfer, PO Receipt, Cycle Count Adj, Scrap…) — P0 for P1 variance categories + P2.
- **`10_demand_daily`**: 17.8B rows; measure column is **`planner_baseline`** (doc said `planner_baseline_forecast`)
  + `working_final_forecast`; already carries `expansions_loadin`/`expansions_runrate`/`non_repeating_events`.
  `dg5_customer_scd1` = 56 mkedg5 customers, mkedg0=4→mkedg5=56. `expansion_loads` populated (8.09M rows),
  `expansion_dims` (19,594). See [[mke-project-scope-sources]] and [[mke-project-guardrails]].

Data-story walkthrough findings (data_understanding/data_stories/, 2026-08-30):
- **Clean PO-receipt fact exists: `prod_edw.fact.purchase_receipt_line`** (2.72M rows, 69,871 items, 2023–2026,
  0 null item keys) — has item_bigint_key + purchase_order_number/line + received/shipped/accepted_quantity +
  expected/receipt dates. **Use this for P1 receipts, NOT the raw-id `receiving_receipt_transactions`** (which
  has NO item column). Resolves the crosswalk blocker. Joins purchase_orders on (po_number, line).
- **P3 item validation = dash-normalization**: expansion_loads.item_number is dashed (`49-56-0507`),
  items_scd1.item_id is dash-less; `REPLACE(item_number,'-','')` join → 98.7% match vs 4.8% raw.
- **P4 `frozen_*` columns in 10_demand_daily are 100% NULL** → use process_date day-over-day deltas for drift;
  reason/audit lives in Lakebase not the warehouse.
- **P2 raw unit-miss over-ranks cheap parts**: top "breach" was a $0.0134 carbide component at a plant (org
  1019), ~$235K real impact → must weight by applied_standard_cost + ABC + org-role.
- inventory_material_transaction transfer rows double-count across subinventories → net inter-org before tie-out.
- Hero item for P1/P2 tracing: item_bigint_key 3879620845706693458 / item_id 48111850 (M18 XC5.0 Battery).
