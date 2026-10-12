<div align="center">

# 🗺️ Supply Day-3 → Source-Data Mapping

### Which workspace tables back each Day-3 requirement — and which have no source found

**Companion to:** [`supply_day3_requirements.md`](supply_day3_requirements.md)
**Method:** live `SHOW TABLES` / `discover-schema` / read-only profiling on Databricks profile **`mke-rsc`**, one activity at a time (sub-agent per activity), anchored on [`data_understanding/00_table_priority_map.md`](data_understanding/00_table_priority_map.md) but **free to search beyond it**.
**Guardrail:** all reads are READ-ONLY against `prod_edw` / `prod_operations`. No writes.

</div>

---

## Status legend

✅ **Found** — a live table/column set clearly satisfies the need
🟡 **Partial** — something exists but is missing grain, columns, or needs a derived layer
❌ **Not found** — no source located in the workspace (or known to live outside Databricks)
🔍 **Pending** — not yet investigated

---

## Activity scoreboard

| # | Activity | Backs requirements | Status |
|---|----------|-------------------|:------:|
| 1 | Top-missing-items / weekly plan review | R3, R4, C.5·1 | ✅ |
| 2 | Demand surprise / consumption + type-of-demand | R14, R15, R16, D | ✅ |
| 3 | Priors / forecast-evolution (late 1–6) | R15, C.6, D | ✅ |
| 4 | Safety stock at lead time (waterfall North Star) | R6, R7, D, R26 | ✅ |
| 5 | Supply/PO delay — requested vs promise/ETA | C.5·5, Pareto-supply, R27 | ✅ |
| 6 | Holds / inventory adjustments / quality | C.2·3, Pareto-tail, R4 | ✅ |
| 7 | Network/org rollup + transfers | R5, C.4 | ✅ |
| 8 | Supplier production plans + PO status report | C.8, R27 | ❌ |
| 9 | Action/outcome log + escalation email output | R18–R20, R23, R24 | 🟡 |

**All 9 activities complete (2026-09-02).** 6 ✅ Found · 2 🟡 Partial · 1 ❌ Not found.

---

## ⭐ Executive summary — what to tell the room

- **The demand P1 slice is fully sourced.** Demand surprise, consumption, customer(DG5), promo/base/run-rate, monthly buckets, and the whole priors/late-1–6 matrix are all **queryable directly from `prod_edw.fact.10_demand_daily` (254 columns, 371 daily snapshots)** — no analytics-only layer needed. Answers Part I Q3 & Q6.
- **Two transcript assumptions were wrong — in our favor:**
  1. *"There's no place to roll an item up across orgs."* → There **is** a native `designated_org_code` that pools the Olive Branch cluster (1080+2012+2014), already denormalized into `20_supply_daily`. R5 is a GROUP BY, not a rebuild.
  2. *"We can't tell if a planner or the supplier moved a PO date."* → `purchase_order_change_orders.change_order_originator_type` records BUYER vs SUPPLIER vs REQUESTER vs SYSTEM.
- **The two real gaps are exactly where the transcript said:** supplier-published plans + the SharePoint PO-status file are **not in Databricks** (external), and the **action-log / escalation-email write targets** aren't built yet (Lakebase App schema exists; Delta publication + email template don't).
- **One thing to chase down with a person:** Sarah's safety-stock reconstruction (R26) is **not a live table** anywhere reachable — the North Star waterfall works without it today, but reuse needs its real location.

---

## ❌ / 🟡 Requirements with NO source found (or only partial)

*The list you asked for — every requirement whose data is missing or incomplete, and why.*

| Requirement | Gap | Verdict | What's needed |
|---|---|:--:|---|
| **R27** — ingest PO status report | SharePoint spreadsheet **not ingested**; no supplier-plan table anywhere | ❌ | Build SharePoint→Delta ingestion into `sandbox_operations.po_management` + template normalizer (~70% consistent + long tail) |
| **C.8** — supplier weekly production plans | Suppliers publish in **Excel; no live share**; nothing in Databricks | ❌ | External; future live-data-exchange follow-up |
| **R23** — action/outcome log | No `action_outcome_history` Delta table yet | 🟡 | Create table + Lakebase→Delta publication Job |
| **R18** — structured escalation email | No email artifact/template exists | 🟡 | Create `escalation_email_output` + template |
| **R20** — edit-in-app writeback | Lakebase fields exist; **no Delta publication Job** | 🟡 | Build idempotent Lakebase→Delta MERGE Job |
| **R26** — reuse Sarah's safety-stock reconstruction | Not a live table anywhere reachable | 🟡 | Get real location from Sarah *(candidate lead: `prod_operations.supply_staging.dim_safety_stock`)* |
| **Type-of-demand (Act. 2c)** — initially looked analytics-only | **Resolved ✅ by Activity 3** — promo/base columns DO exist in `10_demand_daily` | — | none |
| **22 SS Stat / 22 SS DOC** safety-stock plans | Registered in dimension, **0 rows in fact** | 🟡 | Await plan activation, or use `dim_series_ext_vw.safety_stock_planning_method` |

**Everything else (R1–R17 data needs, R6/R7, R25) has a confirmed live source.** R19/R24 are already built in the Lakebase App schema.

---

*(Each section below is the per-activity detail, filled in as each sub-agent completed.)*

---

## Activity 1 · Top-missing-items / weekly plan review — ✅ Found

**Backs:** R3 (identify likely cause), R4 (root-cause categories), C.5 step 1 (find the problem — the planner's entry point).

**Primary table:** `prod_edw.fact.20_supply_daily` — 13.4B rows, 366 daily snapshots (2025-06-28 → 2026-08-29).
**Plan gate:** `prod_edw.dimension.supply_and_demand_plans_scd1` → filter `plan_name IN ('20 Global Supply Plan','20 Mexico Supply Plan')`.

**Column mapping:**

| Planner concept | Column | Stored / derived |
|---|---|---|
| Projected position (PAB) | `projected_available_balance` | stored (goes negative = stockout) |
| Demand | `total_demand` (= independent + dependent), `gross_forecast`, `net_forecast` | stored |
| Supply | `total_supply`, `scheduled_receipts` | stored |
| On-hand (projected) | `on_hand` | stored (99.6% sparse — only where applicable) |
| Safety stock | `safety_stock` | stored, **per date_key** ← feeds Activity 4 |
| **Projected miss / shortfall** | — | **DERIVED**: `CASE WHEN projected_available_balance < 0 THEN ABS(projected_available_balance) END`, or vs safety stock: `safety_stock − projected_available_balance` |
| **Low point / risk period** | — | **DERIVED**: `MIN(projected_available_balance)` over the date_key window |
| Item | `product_bigint_key` → `items_scd1` | stored |
| Org | `inventory_organization_bigint_key` → `inventory_organization_scd1` | stored |
| Week bucket | `date_key` (INT yyyyMMdd) | stored — **weekly, Monday-aligned**, ~111 weeks forward |
| Snapshot vintage | `process_date` (INT yyyyMMdd) | stored — daily snapshots |

**Snapshot semantics (confirms transcript):** daily snapshots, **weekly Monday horizon buckets** — matches the demo's "risk running through October" forward view. Take latest `process_date`, filter `date_key` across the risk window, rank by `MIN(PAB)` for "top missing items."

**Gaps carried to other activities:**
- Demand granularity (customer / promo / base) is **not** in this table → **Activity 2/3** (`10_demand_daily`).
- Actual receipts/shipments (plan-vs-actual) live in separate facts → already mapped in P1 slice.
- Root-cause *why* (PO delay, holds) → **Activities 5, 6, 8**.

**Evidence:** `DESCRIBE` + filtered `SELECT` on `20_supply_daily`; plan-name counts (Global 39.1M / Mexico 2.0M rows per snapshot); PAB range incl. negatives. READ-ONLY.

**Note:** a live Databricks App `48111850-supply-root-cause` (ACTIVE/SUCCEEDED) already exists in the workspace — likely the Day-3 concept build for this SKU family.

---

## Activity 2 · Demand surprise / consumption + type-of-demand — 🟡 Partial (P1 slice)

**Backs:** R14 (demand first slice), R15 (breakdown), R16 (consumption ↔ priors story), Part D (demand surprise, consumption, sub-buckets).

**Sub-verdicts:**

| Sub-need | Verdict | Where |
|---|---|---|
| (a) Consumption / demand surprise (actual vs forecast) | ✅ Found | forecast in `10_demand_daily`; actual from `sales_order_line_transactions` (shipped) + `inventory_days_on_hand` (ending on-hand) |
| (b) Customer at DG5 | ✅ Found | `dg5_customer_scd1` (56 mkedg5 customers); `10_demand_daily` carries `dg5_customer_bigint_key` natively |
| (c) Type of demand = **promo vs base vs run-rate** | 🟡 **Unconfirmed** | see caveat below |
| (d) Monthly bucket | ✅ Found | `10_demand_daily` weekly Monday `date_key`; roll to month via `date_scd1.planning_month` |

**Primary tables:**
- `prod_edw.fact.10_demand_daily` — 17.8B rows, 368 snapshots. Grain: item × org × **customer(DG5)** × week. Native `dg5_customer_bigint_key`.
- `prod_edw.fact.sales_order_line_transactions` (144M) — actual shipments (`shipped_quantity`; filter `order_type='Standard'`, status Invoiced/Closed).
- `prod_edw.fact.inventory_days_on_hand` (2.73B) — ending on-hand actual (point-in-time; never SUM).
- `prod_edw.dimension.dg5_customer_scd1` — mkedg0..mkedg5 hierarchy; join `dg5_customer_bigint_key`.

**Forecast columns:** `working_final_forecast`, `planner_baseline` *(note: actual column is `planner_baseline`, not `planner_baseline_forecast` as some docs say)*.
**Consumption %** = actual shipped ÷ forecast × 100 (LEFT JOIN plan baseline to shipped actuals on item+org+week).

> 🔑 **CORRECTION (2026-09-02, from scenario probing) — demand plan names are PRODUCT-LINE-SPLIT, not "20 Global."**
> `10_demand_daily` does **not** use the supply plan names. Its `plan_name` values are split by product line:
> **`10 TOL Demand Plan`** (tools, ~16.1M rows/snap), **`10 PRT`** (parts, ~13.8M), **`10 ACC`** (accessories, ~12.7M),
> **`10 HND`** (hand tools, ~11.3M), **`10 QP`** (quoted products, ~82k). **Every demand query must filter the
> correct `10 *` plan(s)** — filtering `'20 Global Supply Plan'` on the demand fact returns **0 rows** (verified).
> This affects Activity 2, Activity 3, and every demand-side serving query. The bias columns
> (`shipments_history`, `final_demand_forecast_3_month_ago`) are well-populated within these plans
> (455k+ rows on `10 ACC` alone).

> ✅ **Type-of-demand (c) RESOLVED by Activity 3.** Initially it looked like only the P3 event-overlay columns existed. Activity 3's full `DESCRIBE` (254 columns) found **explicit promo and baseline columns in `10_demand_daily`** — `planner_promo`, `promo_total`, `promo_pce_units`, … and `planner_baseline`, `baseline_statistical_forecast`, `locked_statistical_baseline`, … plus `expansions_runrate`/`expansions_loadin` for run-rate. **Promo vs base vs run-rate is queryable directly in the EDW — NOT analytics-only.** (Answers Part I Q6.) The demand type is column-based (which measure is non-zero), not a single categorical flag.

**Gaps:** no pre-built consumption % column (derive it); no categorical demand-type field; `11_demand_daily` not yet profiled (candidate for prior-version comparison).

> 🎯 **Transcript re-read finds (2026-09-02) — two GOVERNED tables we can reuse instead of building (DK-7/DK-8):**
> - **`prod_operations.demand.fact_forecast_accuracy`** — MKE's own forecast-accuracy fact (the transcript's
>   "forecast accuracy dashboard, fixed to lake-3"). Columns: **`planner_bias`, `system_bias`** (bias split!),
>   `positive_error`/`negative_error` (+`_cost`), `working_final_forecast_lag3_units/_cost`, `rolling_6_*`, by
>   `dg5_customer_bigint_key` × `item_bigint_key` × `date_key`. **Use this for forecast bias instead of
>   recomputing empirically** — it's governed and already splits planner vs system bias. *(Upgrades the bias
>   measure to ✅-sourced.)*
> - **`prod_operations.demand.dim_forecast_accuracy_reason_codes`** — a **12-value governed taxonomy** of *why*
>   forecasts miss (Incorrect POS assumptions, NPD/Transition, Promo strategy change, Business Decision,
>   Constrained Ordering, Make-to-Order, Timing, Seasonality, Expansion, E&O, Customer Opportunity, Conversion),
>   each with a definition. **This is the categorical taxonomy the feedback loop + `ai_classify` should target**
>   — not invented categories. Make-side equivalent: `prod_edw.dimension.work_order_root_cause_scd1`.
> ⚠ Known limitation to *fix* (DK-10): the accuracy fact is locked to **lag-3**; planners need lag-1..6
> flexibility — the priors view should improve on it, not replicate the lock.

**Evidence:** DESCRIBE + small filtered SELECTs on `10_demand_daily`; distinct mkedg5 = 56; plan names confirmed; actuals row counts. READ-ONLY.

---

## Activity 3 · Priors / forecast-evolution (late 1–6) — ✅ Found *(EDW-native)*

**Backs:** R15 (lag dimension), C.6 (priors mechanics), Part D (lates), **Part I Q3** (priors location) + **Part I Q6** (promo/base).

**Headline:** the **entire priors matrix is reconstructable directly from `prod_edw.fact.10_demand_daily`** — no analytics-only semantic model required. The table has **254 columns** (far richer than docs implied).

**The two time axes coexist in one table:**

| Axis | Column | Meaning |
|---|---|---|
| Forecast **period** (matrix rows) | `date_key` (INT yyyyMMdd) | which month is being forecast |
| Snapshot **vintage** (matrix cols) | `process_date` (INT yyyyMMdd) | when the forecast was captured — **371 daily snapshots, 20250621→20260902 (~14.5 mo)** |

**Late-N computation:** `N = (year_P − year_S)×12 + (month_P − month_S)`, where P = forecast period (`date_key`), S = snapshot month (`process_date`). Pick one snapshot per month. Depth confirmed: **~16 monthly vintages → late 1 through late 6 all achievable** (standard = late 3). Bonus: pre-computed lag columns already exist — `final_demand_forecast_lag3`, `final_demand_forecast_3_month_ago`.

**Red vs white (actualized vs open):** derivable from `shipments_history` (>0 = actualized/red; null/0 = open/white). Note actuals also reachable via `sales_order_line_transactions` (Activity 2) — two paths.

**Promo / base / run-rate columns (resolves Part I Q6):**
- Promo: `planner_promo`, `promo_total`, `promo_pce_units`, `promo_pce_amount`, `actualized_promo`, `unconfirmed_promo`, … (+ `frozen_*` variants)
- Base: `planner_baseline`, `baseline_statistical_forecast`, `locked_statistical_baseline`, `dampened_statistical_baseline`, …
- Run-rate / events: `expansions_runrate`, `expansions_loadin`, `non_repeating_events`

**Also found:** `frozen_*` columns (~24) and `frozen_measures_snapshot_date` embedded in each row — an in-row frozen-snapshot mechanism, sparse; not a separate table.

**Gaps / notes:**
- No **month-start/month-end snapshot designator** — daily snapshots; the priors view must *choose* one snapshot per calendar month (e.g., last business day). A small business-rule decision, not a data gap.
- No dedicated priors/frozen/vintage **table** (`SHOW TABLES IN prod_edw.fact` = 298 tables; **no `11_demand_daily`** found here, no `*frozen*`/`*prior*`/`*snapshot*` table; `prod_edw.supply_chain_analytics` schema exists but is **empty**). Priors is a **query/pivot over the raw fact**, not a prebuilt object.
- Demand type is **column-based** (which measure is non-zero), not one categorical flag — the pivot must decide how to split promo vs baseline.

**Evidence:** `DESCRIBE 10_demand_daily` (254 cols); forecast-evolution proof for one item across 3 process_dates (late_2=9.77 → late_1=7.60 → late_0=7.60); monthly-vintage count = 16; `shipments_history` null-check; `SHOW TABLES IN prod_edw.fact` (298, no dedicated snapshot table). READ-ONLY.

---

## Activity 4 · Safety stock at lead time (waterfall North Star) — ✅ Found *(derivable today)*

**Backs:** R6 (waterfall start = projected safety stock at lead time), R7 (variance buckets vs that reference), Part D (safety-stock definitions), R26 (reuse Sarah's reconstruction).

**Headline:** the North Star — *"projected safety stock at lead time vs current projected gap"* — is **fully computable today** from existing columns. No new table needed to start.

**Tables & columns:**

| Purpose | Table | Column |
|---|---|---|
| Safety-stock target (per future week) | `prod_edw.fact.20_supply_daily` | `safety_stock` (also `safety_stock_calculated`, `safety_stock_override`, `safety_stock_doc_override`, `percentage_safety_stock` — population/hierarchy TBD) |
| Projected position | `prod_edw.fact.20_supply_daily` | `projected_available_balance` |
| **Lead time (days)** | `prod_operations.edw_extension.dim_series_ext_vw` | `complete_lead_time` (+ `preprocessing_/processing_/postprocessing_lead_time`) |
| SS method flag | `dim_series_ext_vw` | `safety_stock_planning_method`; `days_of_cover` (DOC metric) |

**Gap-at-lead-time computation:**
1. Read item's `complete_lead_time` (days) from `dim_series_ext_vw`.
2. Target week = latest `process_date` + `ceil(lead_time_days / 7)` weekly `date_key`s forward.
3. At that future `date_key`: **gap = `safety_stock` − `projected_available_balance`** (>0 = deficit to target; ≤0 = above SS).
- Verified live: e.g. week 20260907 → ss=12, PAB=5, gap=7. ✅

> ⭐ **`complete_lead_time` also powers recoverability (DK-15/V13):** `recoverability_class` = forward first-cross
> week vs `today + complete_lead_time` (inside the fence = UNRECOVERABLE). Live: 98% UNRECOVERABLE, $372.5M.
> ⚠️ **Lead time is BIMODAL** — median **2 days**, average **122 days** (99,678 series >8wk). **Never use an
> average lead time; always per-SKU** — an average mis-classifies the long-lead tail, which *is* the flagged
> population.

> ⚠️ **Finding 1 — statistical vs DOC safety stock is dimension-only, not yet in the fact.**
> `supply_and_demand_plans_scd1` lists **"22 SS DOC Supply Plan"** and **"22 SS Stat Supply Plan"** (and "23 Transition SKU"), but `20_supply_daily` contains **only "20 Global" + "20 Mexico"** — a `plan_name LIKE '22 SS%'` filter returns **0 rows**. So the newer statistical/DOC safety-stock split is *registered* but **not yet populated in queryable fact data.** The live plan uses whatever method 20 Global/Mexico embed. Distinguishing statistical-vs-DOC per the transcript needs those plans activated (or `dim_series_ext_vw.safety_stock_planning_method`).

> ⚠️ **Finding 2 — Sarah's safety-stock reconstruction is NOT a live table yet (R26).**
> Searched all schemas in `prod_edw`, `prod_operations`, `sandbox_operations`. The schema `sandbox_operations.sara_grether` **does** exist and is not empty — but its only table, `trial_data_for_supply_dataverse` (**4 rows, mostly null**), is a **project/initiative-tracking sheet** (columns: Problem Statement, Objective/Goal, Impact, Prioritization, Owner, Tasks, % Complete; rows tagged Foundation/Ordering, Reporting/SPX, Apps, Ai). It contains **no safety-stock data or reconstruction logic** — not useful for any Day-3 requirement. No `safety_stock_reconstruction` / `ss_recon_*` table found anywhere reachable. So R26's "complete reconstruction, on Databricks" is **not yet available to build on** — likely still in a dev notebook. **Open action: get the real location from Sarah.** *(Directly verified 2026-09-02.)*

**Gaps:** which of the 5 safety-stock columns is authoritative (override vs calculated vs base — population unknown); lead-time-days → weekly-bucket rounding rule to confirm; 22 SS plans await activation; Sarah's recon location unknown.

**Evidence:** `DESCRIBE 20_supply_daily` (161 cols) + `dim_series_ext_vw` (150+ cols, incl. `complete_lead_time`); `DISTINCT plan_name` in fact (2) vs dimension (50+, incl. 22 SS DOC/Stat); `COUNT WHERE plan_name LIKE '22 SS%'` = 0; live gap sample. READ-ONLY.

---

## Activity 5 · Supply / PO delay — requested vs promise/ETA — ✅ Found *(rich)*

**Backs:** C.5 step 5 (supply check), Pareto supply bucket (~20-25%), R27 (PO status — EDW side), Red Keychain requested-vs-confirmed.

**Headline:** ✅ strong — the EDW has **more** PO-timing signal than the planner uses today, **including who changed the date** (which the transcript assumed was *not* in the EDW).

**Requested vs promise/ETA — `prod_edw.fact.purchase_orders`:**

| Column | Meaning |
|---|---|
| `ordered_date_key` | when PO was placed |
| `requested_delivery_date_key` | requested delivery (at creation) |
| `promised_delivery_date_key` | **current supplier promise / ETA** |
| `original_promised_delivery_date_key` | initial promise (unchanged baseline) |
| `last_acceptable_delivery_date_key` | latest acceptable date |

**Gap** = `promised_delivery_date_key − requested_delivery_date_key`. **Date slip** = `promised − original_promised` (or `DATEDIFF` via `date_scd1`). Verified live on PO 380020278.

**Date-change history — `prod_edw.fact.purchase_order_change_orders`:**
- `change_order_date_key`, `change_order_number`, and crucially **`change_order_originator_type`** with live distribution: **BUYER 2,409,314 · SUPPLIER 1,465 · REQUESTER 8,660 · SYSTEM 993**, plus `change_order_originator` (name/id).

> 💡 **Resolves a transcript assumption.** Day-3 said you *can't* reliably tell whether a PO date change was made by a **planner vs a supplier**. **You can** — `change_order_originator_type` captures BUYER vs SUPPLIER vs REQUESTER vs SYSTEM. The SUPPLIER signal is rare (~1,465) and high-value for root-cause ("supplier jacking POs around"). *(Recommend confirming completeness with the data owner before relying on it operationally.)*

**Also available:**
- `prod_edw.fact.purchase_order_schedule` — SCD2 (`valid_from`/`valid_to`) per PO line/schedule → full date-change timeline (date_keys stored as STRING here).
- `prod_edw.fact.frozen_planned_purchase_orders` (17.5M, `supply_plan_source='Planning application'`) — frozen commitment zone.
- `prod_edw.fact.supply_and_demand_planned_purchase_order` — planned PO detail incl. `old_dock_date_key`/`old_due_date_key` (prior values for change detection), `firm_status`, `release_status`.
- `prod_edw.fact.purchase_order_delivery` — **DEPRECATED, avoid.**

**Supplier join:** `purchase_orders.supplier_bigint_key` → `dim_series_ext_vw` (naive join returned null in one sample — join path needs confirming; a clean supplier-dim lookup may be needed). 🟡 minor.

**Gaps:** supplier-name join path to confirm; `change_order_reason` populated? (would enrich root-cause); originator-completeness to validate with owner.

**Evidence:** DESCRIBE of all 5 PO tables; live PO date sample; originator-type distribution counts. READ-ONLY.

---

## Activity 6 · Holds / inventory adjustments / quality — ✅ Found *(all 3 sub-causes)*

**Backs:** C.2 step 3 (long-tail triage), Pareto tail, R4 (root-cause categories → build-status). *Two of these tables were discovered live beyond the anchor list.*

| Sub-cause | Verdict | Table | How to identify |
|---|---|---|---|
| (a) Inventory adjustment / lost | ✅ Found | `prod_edw.fact.inventory_material_transaction` | `transaction_type_description LIKE '%Adjustment%'` → `Cycle Count Adjustment`, `Physical Inventory Adjustment`, `Purchase Order Receipt Adjustment`; `reason_name` gives reason; signed `transaction_quantity` (− = lost). ~70.6K adj rows. |
| (b) On hold / not available to ship | ✅ Found *(new tables)* | `prod_edw.fact.sales_fulfillment_hold_transactions` (+ lookup `prod_edw.staging_oracle_fusion_erp.hold_codes_vl`) | join on `hold_code_bigint_key`; currently-held = `hold_release_date_key`/`hold_released_timestamp IS NULL`; `hold_comments`, `hold_apply_date_key`. |
| (c) Quality | ✅ Found | `prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions` | `inspection_status_code='REJECTED'` and/or `inspection_quality_code` (10–60; 60 = reject); `from_/to_subinventory` shows move to quality-hold. ~11.2M rows. |

**Transaction-type column** on `inventory_material_transaction` = `transaction_type_description` (47 distinct types: receipt / issue / transfer / the 3 adjustment types above / etc.).

> 💡 **New tables found (beyond anchor list):** `sales_fulfillment_hold_transactions` and `hold_codes_vl` — these are the proper "on hold, not shippable" source the transcript describes. Not previously catalogued.

**Gaps / by-design notes:**
- ⚠️ **No available-vs-on-hold split at the balance level.** `inventory_days_on_hand` has `on_hand_qty` but **no `available_qty`/`on_hold_qty` columns** — on-hold must be reconstructed by joining the holds fact to the balance. (This matches a "Partial" build-status in the transcript's coverage chart.)
- Holds are modeled at **sales-order** level (`sales_fulfillment_hold_transactions`), not as an inventory-balance attribute — fine for "what's blocked," but the item-level pooled on-hold view needs a join.
- `inspection_quality_code` is numeric with no descriptive lookup exposed; reason narratives live in Oracle only.
- Some adjustment `reason_name` = "None" (system-driven, no explicit reason).

**Evidence:** DESCRIBE + DISTINCT type values on `inventory_material_transaction`; sample adjustment rows; hold-table schema + sample held SO; inspection-code sample. READ-ONLY.

---

## Activity 7 · Network / org rollup + transfers — ✅ Found *(overturns a transcript assumption)*

**Backs:** R5 (roll up an item across orgs), C.4 (pooled-inventory problem).

> 🎯 **Big finding — the transcript said this is impossible today; the data actually supports it.**
> Planners said there is *no place* to roll an item up across orgs. But `inventory_organization_scd1` has a native **`designated_org_code`** grouping attribute that pools the Olive Branch cluster into one network key — and it's **already denormalized into `20_supply_daily` as `designated_organization_bigint_key`.** So R5 is a **native GROUP BY, not a hand-built org enumeration.** The gap is a *product/surface* gap (no UI/dashboard exposes it), not a *data* gap.

**Orgs confirmed (with the grouping attribute):**

| Code | Name | Type | `designated_org_code` |
|---|---|---|---|
| 1080 | Byhalia, MS | US Distribution / mfg | **2012** |
| 2012 | Olive Branch | US Distribution | **2012** |
| 2014 | Byhalia DC | US Distribution | **2012** |
| 2120 | Mexico | MEX Distribution | **2120** |

Olive Branch cluster (`designated_org_code='2012'`) = 19 member orgs incl. 1080/2012/2014. Mexico (2120) and Canada roll up separately — matches the transcript.

**Pooled rollup mechanism:** `GROUP BY designated_org_code` (or `designated_organization_bigint_key`) on `inventory_days_on_hand` or `20_supply_daily`. Proven live: one item, date 20260901 → pooled on-hand 669 units across the OB cluster; Mexico 6 units separate.

**Transfers / in-transit (`prod_edw.fact.transfer_orders` — new table):**
- `source_inventory_organization_bigint_key` → `destination_inventory_organization_bigint_key`. Live: **14,772 transfer orders 1080→2014** (mfg→DC).
- Plus 13 transfer transaction types in `inventory_material_transaction` (Interorg/Intraorg shipment/receipt, Direct Org Transfer, Subinventory Transfer, …).

**Stranded / in-transit visibility (`inventory_days_on_hand`):** separate cost/qty components — `on_hand_qty` (available), `in_transit_cost` (shipped, not received), `received_not_put_away_cost`, `work_order_wip_cost` (in mfg). So "stuff stuck in 1080 mfg vs arrived in 2014 DC vs in-transit-not-actualized" is all distinguishable. Live snapshot: 1080=13.8M, 2012=41.0M, 2014=2.2M on-hand.

**Gaps:** none material for the data. The real gap is **no existing UI/dashboard/Genie surface exposes the pooled view** (the transcript's actual complaint) — that's a build item, not a missing source. Subinventory/location drill-down bridges via `inventory_organization_subinventory_location`.

**Evidence:** DESCRIBE org dim + `designated_org_code` distinct values; live pooled SUM proof; `transfer_orders` schema + 1080→2014 count; on-hand-by-org snapshot. READ-ONLY.

---

## Activity 8 · Supplier production plans + PO status report — ❌ Not found *(external, as expected)*

**Backs:** C.8 (supplier data exchange today), R27 (ingest PO status report — future).

**Verdict confirms the transcript:** neither the **supplier-published weekly production plans** (Excel) nor the **SharePoint PO status report** is ingested into Databricks today.

| Sub-need | Verdict | Detail |
|---|---|---|
| Supplier-published production plans (weekly Excel) | ❌ Not found | No supplier-plan / vendor-schedule / production-plan / capacity-commit table in any schema. Supplier tables that exist are master-data/invoice/receipt only. |
| SharePoint PO status report ingested | ❌ Not found | `staging_flat_files` (83 tables — CPF, sales_forecast, expansion_*, pce_*) has **no** po_status / supplier / production_plan upload. `information_schema` search for `%sharepoint%`/`%po_status%`/`%production_plan%` → nil. |

**Closest EDW substitutes (from Activity 5, not the real thing):** `purchase_order_change_orders` + `purchase_order_schedule` give Oracle-native requested/promised/ETA dates and change history — but **lack** the supplier-published ship dates and the ~70% vendor template. Also found: `prod_operations.procurement.dim_purchase_order_status` (14-row status *dimension*, not the report).

> 💡 **Adjacent find worth noting:** `prod_operations.supply_staging.dim_safety_stock` exists — a candidate lead for **Activity 4 / R26** (Sarah's safety-stock work) that this search surfaced. Flag to profile if pursuing the statistical-vs-DOC safety-stock split.

> ⚠️ **DQ for supplier-level analysis (DK-13b, from validation V11):** `origin_supplier_name` has **multiple
> variants for one entity** — e.g. `TTI (TECHTRONIC CORDLESS GP) LIMITED` / `LTD` / `LMTD`, and
> `TECHTRONIC CORDLESS GP (OUTSRCD PRDCTN)` vs `(OUTSRC SVPT)`. Any **supplier-level aggregation** (the
> constraint-convergence pivot behind 3,035 SKUs, the supplier scorecard) must **canonicalize supplier names
> first** — or concentration is understated and the "one constraint" action fragments across name variants.
> Prefer `origin_supplier_number` when a clean id exists.

**What R27 needs (future build):** a SharePoint→Delta ingestion (connectors exist per transcript; not wired) landing the PO status file into `sandbox_operations.po_management`, plus a normalizer for the ~70% consistent supplier template + long-tail variants. Live supplier data-exchange is a separate follow-up (C.8).

> 🤖 **AI unblock path (with vs without):** *without AI* this stays ❌ (a rigid parser breaks on the long-tail
> templates). *With AI* — **`ai_parse_document` / `ai_extract`** reads the heterogeneous supplier Excel /
> SharePoint files and pulls structured fields (item, promised ship date, qty/week, capacity) into Delta,
> handling the variants a fixed parser can't. Extracted values are **🟡 (AI-parsed)** — label + keep the raw
> file linked for audit; the parsed dates then feed the **deterministic** PO-slip formula. This is the single
> highest-value AI use in the whole design — it converts the one ❌ into a live feed. See
> [`supply_day3_ai_functions_opportunities.md`](supply_day3_ai_functions_opportunities.md).

**Evidence:** `SHOW SCHEMAS` prod_edw (80) / prod_operations (36); `SHOW TABLES` in staging_flat_files, procurement, procurement_staging, supply_staging; `information_schema.tables` LIKE searches for supplier/vendor/po_status/production_plan/sharepoint. READ-ONLY.

---

## Activity 9 · Action/outcome log + escalation email output — 🟡 Partial *(write targets, not prod sources)*

**Backs:** R18 (structured email), R19 (app-drafts email), R20 (edit-in-app writeback), R23 (action/outcome log), R24 (record how assembled).
**Note:** these are **WRITE targets** — they live in `sandbox_operations.po_management` (Delta) + **Lakebase** (App state), never in `prod_edw`. The existing `mke-po-actions` App already scaffolds most of the Lakebase side.

| Req | What it needs | Status | Where |
|---|---|:--:|---|
| R19 app-drafts email | draft text field | ✅ built | Lakebase `action_request.drafted_note` |
| R24 record-how-assembled | decision-assembly log (recommended vs final + forecast context + MLflow link) | ✅ built | Lakebase `decision_eval` |
| R20 edit-in-app writeback | `final_action`, `final_qty`, `override_reason` fields | 🟡 partial | Lakebase `action_request` built; **Delta publication Job missing** |
| R23 action/outcome log | append-only outcome history in Delta | ❌ not yet | must CREATE `sandbox_operations.po_management.action_outcome_history` |
| R18 structured escalation email | two-bullet email artifact + template | ❌ not yet | must CREATE `…po_management.escalation_email_output` + template |

**Lakebase entities already defined** (from `mke-po-actions/server/db/schema-sql.ts` + `mke-po-actions-st/lib/schema.py`): `action_request`, `action_audit_event`, `decision_eval`, `integration_outbox`, `integration_result`, read-only mirrors (`mirror_exceptions`/`mirror_trajectory`/`mirror_kpi`), conversations/messages. Demand app adds `event_audit_event`, `bulk_edit_batch`. → **R19/R24 map directly; R20 fields exist.**

**Delta side already built** in `sandbox_operations.po_management`: `p1slice_planned_weekly` / `_actuals_weekly` / `_plan_vs_actual`, `p1flow_*` (transfer/PO/order-stage timing), `sdp_*` (~35 MVs), `rootcause_plant`. **Not yet built:** `action_outcome_history`, `escalation_email_output`, `decision_eval_history`, `qa_reconciliation_results`.

**The missing piece (closes the loop for R20/R23/R24):** a **Lakebase→Delta publication Job** (idempotent MERGE on `action_id`) that lands App action/decision state into `sandbox_operations.po_management`. Per WORKLOG this is a known open item (Phase 7 / NEW-18).

**Escalation email (R18):** no artifact or template exists yet — only the format spec in the requirements doc. `action_request.drafted_note` can hold the draft; a dedicated output table + a template (params: DG5, customer set, over-consumption qty, horizon/lag, risk units, risk period) must be created.

**Gaps / to build:** (1) create `action_outcome_history` Delta table; (2) create `escalation_email_output` Delta table + email template; (3) build the Lakebase→Delta publication Job; (4) wire the app UI to draft/edit the email. All within the write boundary (`sandbox_operations.po_management` + Lakebase).

**Evidence:** read local App schemas (`mke-po-actions`, `mke-po-actions-st`, `demand_events_app`); WORKLOG/CLAUDE.md write-boundary; `SHOW TABLES IN sandbox_operations.po_management` inventory. READ-ONLY (inspection only — no writes).

---

## Activity 10 · Classifier-axis & adjacent sources (N1–N7, DK-16–20) — how we grab them

*Validated V15–V26. All off the existing conformed spine — **including returns** (a conformed item-keyed warranty
fact was found 2026-09-03, correcting the earlier cross-system verdict). This is the "how the
serving Job grabs the new signals" reference.*

| Signal (req) | Verdict | Source & grab | Notes |
|---|:--:|---|---|
| **Lifecycle** — transition/NPD (V15/N1) | ✅ | `items_scd1.transition_sku_flag`, `is_npd_item`, `npd_launch_date` — join on `item_bigint_key` | 71,484 transition / 4,038 NPD; **use item master, NOT demand-fact flag (NULL)** |
| **Criticality** — ABC (V22/DK-16) | ✅ | `dim_series_ext_vw.inventory_abc_class` — join on `series_bigint_key` | A-class $67.8k/SKU (2.1× C); 37% Unclassified → fallback |
| **Demand-class** — intermittent (V24/DK-18) | ✅ derived | ADI proxy over `10_demand_daily.shipments_history` (share of periods with demand) | ~24% intermittent → low-confidence measures |
| **Dormant / E&O** (V23/DK-17) | ✅ derived | last-ship recency = `MAX(date_key WHERE shipments_history>0)` per item | **NOT `obsolete_date` (sparse, $0.9M)**; $545M never-shipped, $16M dormant |
| **Found-inventory** (V18/N4) | ✅ | `inventory_material_transaction.transaction_quantity` **signed** | +81.9M found / 25,089 events → heal signal |
| **Intentional-hold** (V26/DK-20) | 🟡 partial | `dim_series_ext_vw.safety_stock_managed_flag='Yes'` + `inventory_planning_method` | $450M managed; no explicit reserve flag |
| **Alignment / health / Sankey** (V26/DK-20) | ✅ derived | `20_supply_daily` gap + `inventory_days_on_hand.on_hand_cost` × `inventory_abc_class` | 54% aligned; Sankey Total$→ABC→health |
| **Parameter recommendation** (V25/DK-19) | 🟡 gated | current: `safety_stock`, order min/max, `complete_lead_time` — **no ROP/MAX** (projection-based) | recommender blocked (SS method); proposal-queue workflow reusable now |
| **Returns / warranty** (V17/N3) | ✅ **conformed** | `prod_edw.fact.warranty_transaction` — join `item_bigint_key`→`items_scd1` (+ `replacement_reason_code`, `problem_description`, `part_quantity`, `material_cost`/`labor_cost`/`freight_cost`, `warranty_claim_id`, `serial_number`, `posting_date_key`). Whole governed `domain_service` schema behind it. | **Crosswalk found 2026-09-03** — raw JDE/AX staging (`tool_nbr`) is upstream only; the conformed fact is item-keyed. 60 real IDs pulled. Corrects the earlier ❌. |
| **Non-standard demand** (V19/N5) | 🟡 hygiene | tag `dg5_customer_scd1.mkedg5 IN (NO CHARGE, OTHER NA, …)` | 1.1% of volume → weight ranking by $ |

> **Serving-layer impact:** the Job adds these as columns on `rc_serving_sku_week` (per ADR §7.1a). Lifecycle,
> criticality, intentional-hold are cheap dim joins; demand-class, dormant, found-inventory are derived
> aggregations over demand/transaction history. **Returns also lands on the conformed spine** via
> `fact.warranty_transaction.item_bigint_key` — no new cross-system pipeline needed (the JDE/AX integration
> already happened upstream into `domain_service`).
