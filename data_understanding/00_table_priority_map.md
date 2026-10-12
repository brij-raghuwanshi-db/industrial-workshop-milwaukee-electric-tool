# Master Table → Priority Map (live existence-verified 2026-08-30)

All names verified to EXIST via `SHOW TABLES` / `discover-schema` on profile `mke-rsc` unless marked
otherwise. "Profiled" = a subagent queried its data (see `subagent_findings/`). READ-ONLY throughout.

## Legend
- **Exists** = confirmed present in Unity Catalog (SHOW TABLES / discover-schema succeeded)
- **Profiled** = data actually queried (grain/coverage/domains characterized)
- **Deprecated** = present but doc says do not build on it
- **Missing** = named in a doc but NOT found live

## The map

| # | Table | Exists? | P1 Actuals | P2 Supply Exc | P3 Demand Events | P4 Demand Exc | Role |
|---|---|---|:--:|:--:|:--:|:--:|---|
| 1 | `prod_edw.fact.20_supply_daily` | ✅ 13.4B rows, 366 snaps | ● core | ● evidence | | | Plan snapshot (what we planned) |
| 2 | `prod_edw.dimension.supply_and_demand_plans_scd1` | ✅ | ● filter | ● | ○ | ○ | Plan-name gate (20 Global / 20 Mexico both confirmed) |
| 3 | `prod_edw.fact.purchase_receipt_line` ⭐ | ✅ 2.72M, EDW keys | ● core | ● | | | **PO receipts ACTUAL — use THIS** (item_bigint_key + inventory_organization_bigint_key native; no crosswalk). Supersedes `staging_oracle_fusion_erp.receiving_receipt_transactions` (raw Oracle ids, NO item column) per KEY_FINDING + P1 slice build 2026-08-31 |
| 4 | `prod_edw.fact.sales_order_line_transactions` | ✅ | ● core | ● | | ○ | Sales shipped ACTUAL |
| 5 | `prod_edw.fact.inventory_days_on_hand` | ✅ | ● core | ● | | | On-hand ACTUAL (point-in-time) |
| 6 | `prod_edw.fact.purchase_order_delivery` | ✅ but **DEPRECATED** | ✗ avoid | ✗ | | | Old PO-delivery fact — do NOT depend |
| 7 | `prod_edw.fact.purchase_orders` | ✅ | ● context | ● | | | PO header/line (expected dates, qty ordered) |
| 8 | `prod_edw.dimension.items_scd1` | ✅ 299,966 items | ● dim | ● dim | ● validate | ● dim | Item master + ABC/PL/COO; **status 20 = `item_status='PurchPlan'` (8,716 items)** |
| 9 | `prod_edw.dimension.date_scd1` | ✅ 36,896 days | ● dim | ● | ● dim | ● | date_key(INT yyyyMMdd) ↔ calendar; week/month bucketing |
| 10 | `prod_edw.dimension.inventory_organization_scd1` | ✅ | ● dim | ● | ● dim | ● | Org/DC codes; 2012 Olive Branch + 2120 Mexico confirmed |
| 11 | `prod_operations.edw_extension.dim_series_ext_vw` | ✅ 4.99M rows | ● cost/supplier | ● core | ○ MOQ | ○ | Supplier/planner/lead-time/std-cost/MOQ lens (VIEW) |
| 12 | `prod_edw.fact.10_demand_daily` | ✅ (digit-leading) | | | ● core | ● core | Demand fact — disaggregation weights + baseline forecast |
| 13 | `prod_edw.dimension.dg5_customer_scd1` | ✅ | | | ● core | ○ | Customer 6-level hierarchy (mkedg0..5) |
| 14 | `prod_edw.staging_flat_files.expansion_dims` | ✅ (+ _current/_effectivity/_status) | | | ● legacy output | | Legacy Excel-era event header output contract |
| 15 | `prod_edw.staging_flat_files.expansion_loads` | ✅ (+ _current/_effectivity/_status) | | | ● legacy output | | Legacy Excel-era event line-value output contract |
| 16 | `prod_edw.fact.order_line_fulfillment_accumulating_snapshot` | ✅ | ○ root-cause | ○ | | | Order lifecycle timing (accumulating snapshot) |
| 17 | `prod_edw.fact.customer_shipments` | ✅ | ○ alt shipment | ○ | | | Customer-facing shipment records |
| 18 | `prod_edw.fact.inventory_material_transaction` | ✅ | ○ root-cause | ○ core | | | Inventory movements (receipt/issue/transfer/adj) — root-cause vocab |
| 19 | `prod_edw.staging_oracle_fusion_erp.inventory_on_hand_temporal` | ✅ | ○ alt on-hand | ○ | | | Temporal on-hand w/ date_received |

● = primary/confirmed use · ○ = supporting/likely use · (blank) = not used by that priority

## Tables that span MULTIPLE priorities (the conformed backbone — build once, reuse)
- **`items_scd1`** — all four (P1/P2/P3/P4). The single item spine + ABC/PL/COO/status.
- **`date_scd1`** — all four. The ONLY safe date_key→week/month converter.
- **`inventory_organization_scd1`** — P1/P2/P3(default-org logic)/P4. Org-code semantics incl. 2012/2120.
- **`dim_series_ext_vw`** — P1(cost impact)/P2(supplier & lead-time exceptions)/P3(MOQ)/P4. Supplier/planner/cost lens.
- **`supply_and_demand_plans_scd1`** — P1/P2 primary (plan filter); also gates any plan-scoped demand read for P3/P4.
- **`20_supply_daily`** — P1 core + P2 evidence.
- **`sales_order_line_transactions`** — P1/P2 core; P4 actual-demand signal.
- **`10_demand_daily`** — P3 core (disaggregation) + P4 core (baseline/forecast exceptions).

## BONUS tables discovered live that the docs did NOT name (candidates to raise with owner)
- `prod_edw.fact.21_supply_daily`, `22 SS DOC`, `22 SS Stat`, `23 Transition SKU` supply plans — the plan
  family is richer than just "20". **23 Transition SKU Supply Plan** is directly relevant to P2 transition
  exceptions (#9–11). `11_demand_daily` also exists alongside `10_demand_daily`.
- `prod_edw.fact.frozen_planned_purchase_orders` — likely the **frozen-zone** signal for P2 exception #17
  (frozen-zone violation) and requested-vs-confirmed (Red Keychain NEW-1). Not in the requirement docs.
- `prod_edw.fact.supply_and_demand_planned_purchase_order` — planned PO detail; candidate for PO-timing (M4).
- `prod_edw.fact.purchase_order_schedule` / `purchase_order_change_orders` — PO schedule & change history;
  candidate for lead-time-drift (#13) and requested-vs-confirmed.
- `prod_edw.staging_flat_files.expansion_attributes` / `expansion_rollout` / `expansion_runs` (+ each with
  `_current`/`_effectivity`/`_status`) — the legacy Expansion/Events output is a **Data-Vault-style family**,
  not just two flat tables. P3 must understand this before reproducing the contract.
- `prod_edw.staging_oracle_fusion_erp.dg5_customer_levels` / `hub_dg5_customer` — raw customer-hierarchy
  source behind `dg5_customer_scd1`.

## Missing (named in docs, not found live)
- None so far. Every doc-named table has been confirmed to exist. (Cluster B/D/E subagents will confirm the
  transactional ones are not just present but populated & aligned.)
