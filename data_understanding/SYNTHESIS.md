# SYNTHESIS — What the data actually says, by priority (P1–P4)

**As-of:** 2026-08-30 · **Workspace:** `mke-rsc` (adb-4482605715640778) · **Method:** live queries, not
assumption. Backed by `subagent_findings/A–E`, `00_table_priority_map.md`, and the lead's own probes.
**READ-ONLY** throughout — nothing was written to any prod schema.

This is a *data understanding* document. It deliberately does **not** design pipelines or write joined
production queries. It captures grain, coverage, domains, and — most important — each dataset's **unique
standing** and the **scenarios** the data can and cannot support, so we can decide what to build.

---

## 0. The three things that change how we build (read first)

1. **`20_supply_daily` is snapshot-daily but forecast-WEEKLY, Monday-aligned.** Within one
   `process_date`, the `date_key` values are Monday week-starts (20260824, 20260831, …) out ~**111 weeks
   (~2 years)**, not daily and not 55 years. So P1's "aggregate to weekly" is *already the source grain* on
   the plan side — we select a snapshot and read its weekly buckets; we don't bucket days. The first
   `date_key` (= the snapshot's own week) is an oversized catch-all (~1.65M rows vs ~365K/week) holding
   current + past-due. **Implication:** the D2 "Monday–Sunday week" decision matches the source natively;
   the real design choice is *which daily snapshot represents each week* (e.g. the Monday one).

2. **The actuals receipts table speaks a different key language.**
   `receiving_receipt_transactions` carries **raw Oracle ids** (`organization_id` ≈ 3×10¹⁴, `po_header_id`,
   `item_id`) — not the EDW `*_bigint_key` surrogates every other fact/dim uses. **A crosswalk is
   mandatory** before receipts can join to the plan, items, or org. This is the biggest hidden P1 task and
   the docs never mention it. (Irony: the *deprecated* `purchase_order_delivery` already uses clean EDW
   keys and has 9 years of history — see P1 open items.)

3. **"Status 20" is not a 20.** The P3/P4 item filter is literally `item_status = 'PurchPlan'`
   (8,716 of 299,966 items); the doc's `item_status_description` column is even truncated in the data.
   Filter on `item_status` (or `item_status_name = '20.Ready to Purchase or Plan Production'`), never the
   description. This resolves requirements open-item #1 with evidence.

---

## P1 — Actuals Supply Plan (plan vs actual, weekly, item × org)

**What we're comparing:** the plan we *made* (a prior snapshot's forward view of a week) vs what *actually
happened* that week — across PO receipts, shipments, and ending on-hand — to explain week-over-week change.

### Which data has what (P1)
| Need | Table | What it uniquely gives | Verified facts |
|---|---|---|---|
| **The plan (what we expected)** | `prod_edw.fact.20_supply_daily` | Point-in-time forward plan *vintages*; each snapshot = a frozen weekly forward view | 13.4B rows; 366 daily snapshots 20250628→20260829; weekly Monday `date_key` horizon ~111 wks; measures on_hand, purchase_orders, planned_orders, sales_orders, shipped_sales_orders, total_demand, total_supply, projected_available_balance, safety_stock all present |
| Plan gate | `supply_and_demand_plans_scd1` | Which plan a row belongs to | `20 Global Supply Plan` (plan_id 300000016337941) + `20 Mexico Supply Plan` (…991), both plan_type 2, active. Filter col = **`plan_name`** |
| **PO receipts (actual)** | `receiving_receipt_transactions` | Transaction-level inbound truth, sub-PO-line | 11.1M rows, 3-yr history; grain = receipt event; **raw Oracle ids**; RECEIVE 49.7% / DELIVER 49.7% — pick one; 0.24% negatives (returns) |
| **Shipments (actual)** | `sales_order_line_transactions` | Independent fulfillment ledger | 144M rows, fulfillment-line grain; order_type Standard 81%; status Invoiced 73% + Closed 20%; **shipped_quantity 87% NULL** → must filter to shipped/invoiced lines; EDW bigint keys |
| **Ending on-hand (actual)** | `inventory_days_on_hand` | Daily point-in-time stock position | 2.73B rows, item×org×date_key, 699 daily dates, **zero negatives**; point-in-time (never sum across dates) |
| PO context (ordered qty, expected dates) | `purchase_orders` | Committed PO master; qty ordered, promised/requested dates | 3.8M rows, SCD2 (2.27 rows/line); no txn_date column |
| **Root-cause of on-hand change** | `inventory_material_transaction` | The 27-type movement ledger — WHY on-hand moved | 13.3M rows/90d; Sales Order Issue 44.6%, Subinv Transfer 13.8%, PO Receipt, Cycle Count Adj, Scrap, Rework, RMA…; clean EDW keys |
| Cost impact ($ variance, thresholds) | `dim_series_ext_vw` | applied_standard_cost, lead time, MOQ, planner, supplier | 4.99M rows, 1/series; has domain-violation marker rows to filter |
| Time bucketing | `date_scd1` | date_key→week/month safely | INT yyyyMMdd; week_of_year + week_start_date (Monday). Avoid buggy `date_calendar_week_year` for 53-wk years |
| Item/org enrichment | `items_scd1`, `inventory_organization_scd1` | ABC/PL/COO; org codes 2012/2120 | items 299,966; org dim 126 rows |

### Scenarios P1 can support (evidence-backed)
- **Receipt attainment** (M1): planned PO qty for week W (from snapshot at W-1) vs SUM(receipts where transaction_type='RECEIVE' in W). *Blocked until the receipt→EDW-key crosswalk exists.*
- **Shipment attainment** (M2): planned shipped vs actual shipped (filter Invoiced/Closed, non-null shipped_quantity).
- **Ending on-hand variance** (M3): planned PAB vs actual `on_hand_qty` at week-end date_key (point-in-time, don't sum).
- **PO timing** (M4, weeks early/late): expected receipt week (plan/PO promised date) vs actual receipt week.
- **Root-cause categorization** (2.3.7): map `inventory_material_transaction` types → the doc's 5 variance categories (Supply Timing / Supply Quantity / Demand Change / Inventory Adjustment / Plan Change). Cycle Count + Scrap + Rework reason codes = the "Inventory Adjustment" evidence.
- **Plan accuracy / bias trending** (2.4.2/2.4.3): same future week across many `process_date` snapshots shows forecast convergence and systematic over/under-planning.
- **$ impact & ABC-stratified thresholds** (O8): `applied_standard_cost × variance_units`, tighter for A-items.

### Scenarios P1 **cannot** support yet (data gaps)
- Joining receipts to plan/dims **without building the raw-Oracle-id → bigint crosswalk**.
- Trusting `sales_order_line_transactions.shipped_quantity` blindly (87% null; must use status filter).
- Sub-daily plan precision — the plan is weekly; don't imply daily plan accuracy.

### P1 open items (carry forward)
- **O10 (resolved by profiling):** `process_date` covers 366 days (2025-06-28→2026-08-29) — 180-day backfill is comfortably available. All three actuals sources also cover ≥180 days.
- **O9 (open):** confirm `receiving_receipt_transactions` is the long-term receipt source *and* resolve the **key crosswalk**. Note `purchase_order_delivery` (deprecated) has clean EDW keys + 9-yr history — decide: crosswalk the recommended table, or negotiate keeping/replacing the deprecated one. Build the silver layer behind the `(item_id, org, week, qty_received)` interface either way.
- Confirm the RECEIVE-vs-DELIVER semantics (which one = "received into inventory") with the owner before counting.

---

## P2 — Supply Exceptions (prioritized queue; case state to Lakebase; NO PO writes in this scope)

**What it is:** detect meaningful supply conditions, prioritize by *largest unit miss*, investigate with
evidence, dispose, track. Reuses P1's plan + actuals + root-cause tables as the *evidence* layer.

### Which data has what (P2)
| Exception family (from the 18-type list) | Primary data evidence | Verified support |
|---|---|---|
| Demand exceeds supply / stockout (#1), Excess vs target (#2), Safety-stock violation (#8) | `20_supply_daily` PAB, total_demand, total_supply, safety_stock | All present; PAB goes negative (stockout signal is real in data) |
| Supplier late / lead-time risk (#7), Lead-time drift (#13) | `dim_series_ext_vw.complete_lead_time` vs actual receipt timing from `receiving_receipt_transactions` / `purchase_orders` promised dates | Lead-time fields present; actual timing needs the receipt crosswalk |
| Plan-vs-actual receipt variance (#18) | = P1 M1 output | Directly reuses P1 |
| DC imbalance / rebalance (#15) | `inventory_days_on_hand` (same item, on_hand across orgs) + `inventory_material_transaction` transfer types | on-hand dense by item×org; transfer txns (Subinv Transfer 13.8%, Interorg ship/receipt) present |
| MOQ waste (#16) | `dim_series_ext_vw.minimum_order_quantity`, `fixed_lot_multiplier` | Present |
| Transition risks (#9–11) | **`23 Transition SKU Supply Plan`** (found live, not in docs) + items PL/status | Plan exists; worth pulling in |
| Frozen-zone violation (#17) | **`frozen_planned_purchase_orders`** (found live, not in docs) + `dim_series_ext_vw` time-fence fields | Table exists; release/planning/demand time-fence columns present in series ext |
| Demand-forecast volatility (#14) | `10_demand_daily` working_final_forecast vs frozen_* | Frozen snapshots present (see P4) |

### Boundary to confirm (important)
The 18-type list **interleaves PO-action exceptions** (pull-in #3, push-out #4, new PO #5, cancel #6,
past-due #12) that belong to the **excluded** PO/ordering scope. **Confirm the exact supply-vs-PO split
with the owner** before detection is built. P2 writes *case state to Lakebase*; it must **not modify POs**.

### Unique standing / scenarios
- P2's differentiator is not new data — it's **turning P1's evidence into a prioritized, dispositioned
  queue**. Prioritization = *largest unit miss* = projected inventory vs demand gap (computable from
  `20_supply_daily` PAB/total_demand). Financial impact (via `applied_standard_cost`) is bookmarked.
- Bonus tables (`frozen_planned_purchase_orders`, `purchase_order_schedule`, `purchase_order_change_orders`,
  `23 Transition SKU Supply Plan`) materially strengthen exceptions #9–13,17,18 — raise with owner.

---

## P3 — Demand Events App (replace Excel; output = mkedg5 customer × item × month)

**What it is:** planners capture incremental demand *events* (non-repeating load-in / repeating run-rate)
above baseline; the app disaggregates hierarchy-level input down to mkedg5 and publishes.

### Which data has what (P3)
| Need | Table | Verified facts / unique standing |
|---|---|---|
| **Customer hierarchy (6 levels)** | `dg5_customer_scd1` | **56 mkedg5 customers**; mkedg0=4 (3rd Party/Intercompany), mkedg1=8 (DOM/CAN/LAG/…), mkedg2=7 (OTD/THD/CAN THD/…), mkedg3=14, mkedg4=29, mkedg5=56. ACE & BLAINS present. The *only* source of the roll-up P3 collapses to mkedg5. Case inconsistency ("3rd Party" vs "3RD PARTY") — normalize. |
| **Disaggregation weights + baseline** | `10_demand_daily` | 17.8B rows. Measures **`working_final_forecast`** + **`planner_baseline`** (NOT `planner_baseline_forecast` as doc says); 40+ active measures, 60+ deprecated. Ratio weight = each mkedg5's measure ÷ group total. Joins via `dg5_customer_bigint_key`. **Already carries `expansions_loadin`, `expansions_runrate`, `non_repeating_events`** — the event increments round-trip back into this fact. |
| **Item validation** | `items_scd1` | Rule = `item_status='PurchPlan'` (8,716 items), non-blocking warning. |
| **Default org logic** | `inventory_organization_scd1` | 2012 default (US), 2120 Mexico/THD MEX — both confirmed. |
| Lot constraints (Forecast Builder) | `dim_series_ext_vw` | MOQ, fixed_lot_multiplier present. |
| **Legacy output contract** | `expansion_dims` (19,594 rows) + `expansion_loads` (**8.09M rows**, populated) | Real Excel-era shape: file_name "EXP001655 …xlsx", expansion_name, item_number, customer, `variable` (month bucket), load_value. **Richer than 2 flat tables** — a Data-Vault family (`_current`/`_effectivity`/`_status`, plus `expansion_attributes`/`rollout`/`runs`). |

### Scenarios / decisions the data informs
- **Disaggregation** (§3.3): ratio method is directly supported — but the team must pick the **4–5 extra
  measures** (open-item #3) from the 40+ active in `10_demand_daily` (candidates: final_demand_forecast,
  live_planner_baseline_forecast, promo_total, bookings_history, frozen_working_final_forecast).
- **Baseline comparison** (§9.3): `planner_baseline` shown alongside event input — supported.
- **Output grain** = mkedg5 × item × month — supported by hierarchy + monthly bucketing (`date_scd1.planning_month`).
- **Write target:** per guardrail, write the **sandbox** equivalents (`sandbox_operations.po_management.
  expansion_dims/…loads`) keeping the doc §8.1 column contract; publish to Oracle via a governed step —
  **never** write `prod_edw`.

### P3 gaps / open items
- **Customer-code reconciliation:** `expansion_loads` shows codes like "FASTENAL"; the dim has 56 mkedg5
  values. Must confirm expansion customer codes map 1:1 to mkedg5 (a mapping layer may exist).
- Which extra disaggregation measures (open-item #3); tagging taxonomy (#6); truncate/reload vs merge (#4).
- `expansion_dims.ship_date` is 88% null in legacy data — understand whether that's metadata-only rows.

---

## P4 — Demand Exceptions (queue over baseline/events/overrides/finals/actual-demand)

**What it is:** a focused queue of material demand problems; ML **only after** deterministic rules +
historical evidence prove a measurable need.

### Which data has what (P4)
| Candidate exception | Data evidence | Verified support |
|---|---|---|
| Significant forecast change / volatility | `10_demand_daily`: working_final_forecast vs `frozen_working_final_forecast`; planner_baseline vs `frozen_planner_baseline` | Frozen snapshot columns present → drift is directly measurable |
| Actual materially ≠ plan | `10_demand_daily` (plan) vs actual demand signal from `sales_order_line_transactions` | Both present; join via item/org keys |
| Persistent bias | Same future period across `10_demand_daily` process_dates | 368 process_dates available |
| Unusually large override | planner_baseline vs planner_baseline_ovrd / _adj | Override columns present |
| Active event w/ no demand · expired/invalid event · overlapping events · wrong repeating/non-repeating pattern · disaggregation anomaly | P3 event state (Lakebase) + `expansions_loadin`/`expansions_runrate` in `10_demand_daily` | Event measures live in the fact → P4 can cross-check P3 output |
| New-item signal gap | `items_scd1` new-item flags + `10_demand_daily` new_item_forecast/channel_npd_forecast | Present |

### Unique standing / notes
- P4's data spine is **`10_demand_daily` + its frozen_* twins** — the freeze snapshots are what make
  "changed since last plan" measurable without building our own history first.
- **Deep link to P3:** when an exception is a bad event, P4 routes back to the P3 app to correct it.
- ML (baseline model, drift monitoring, champion/challenger) is **deferred** until deterministic rules +
  evidence justify it — consistent with the operating pattern.

---

## Tables that span MULTIPLE priorities (build once, reuse — the conformed backbone)

| Table | P1 | P2 | P3 | P4 | Why shared |
|---|:--:|:--:|:--:|:--:|---|
| `items_scd1` | ✅ | ✅ | ✅ | ✅ | Item spine + status-20 gate + ABC/PL/COO |
| `date_scd1` | ✅ | ✅ | ✅ | ✅ | Only safe date_key→week/month converter |
| `inventory_organization_scd1` | ✅ | ✅ | ✅ | ✅ | Org codes incl. 2012/2120 |
| `dim_series_ext_vw` | ✅ | ✅ | ✅(MOQ) | ○ | Supplier/planner/lead-time/std-cost lens |
| `supply_and_demand_plans_scd1` | ✅ | ✅ | ○ | ○ | Plan-name gate |
| `20_supply_daily` | ✅ | ✅ | | | Plan + exception evidence |
| `sales_order_line_transactions` | ✅ | ✅ | | ✅ | Shipment actual = supply actual & demand actual |
| `10_demand_daily` | | ○ | ✅ | ✅ | Disaggregation weights + baseline + freeze twins |
| `inventory_material_transaction` | ✅ | ✅ | | | Root-cause movement ledger (both supply priorities) |

**Design consequence:** the five dimensions + the two "actual" fact families are shared infrastructure.
Model them once (conformed), and P1–P4 become mostly *different questions over the same spine* — which is
exactly the "minimum sufficient architecture" the operating pattern calls for.

---

## Tables named in docs but NOT found / different than described

| Doc reference | Live reality |
|---|---|
| `planner_baseline_forecast` (measure in `10_demand_daily`) | Actual column is **`planner_baseline`** (+ `planner_baseline_adj/_ovrd`, `live_planner_baseline_forecast`). |
| Validate item on `item_status_description` = "Status 20" | Use **`item_status='PurchPlan'`**; the `_description` column is truncated in data. |
| `expansion_dims` / `expansion_loads` as 2 flat tables | Exist and populated, but part of a **Data-Vault family** (`_current`/`_effectivity`/`_status` + `expansion_attributes`/`rollout`/`runs`). |
| `20_supply_daily` "day-0 / daily" mental model | Snapshot is daily, but forecast buckets are **weekly Monday**; horizon ~2 yrs. |
| Everything else in the docs (all P1 sources, dims, transactional actuals) | **Confirmed to exist.** No doc-named table was missing. |

**Nothing was Missing.** Two were mis-described (measure name, status literal) and several are richer than
documented. The only true *access* gap is semantic: `receiving_receipt_transactions` raw-id crosswalk.

---

## Consolidated open questions to put to the business/EDW owner
1. **Receipt key crosswalk (P1/P2, blocking):** confirm the raw-Oracle-id → EDW-bigint mapping table for
   `receiving_receipt_transactions`; or decide whether to use clean-keyed `purchase_order_delivery` despite
   its deprecation flag. Also: RECEIVE vs DELIVER — which is "received into inventory"?
2. **Shipment measure (P1):** is 87% null `shipped_quantity` purely unfulfilled lines? Confirm the exact
   `sales_fulfillment_line_status` set that counts as "shipped".
3. **P2 supply-vs-PO split:** which of the 18 exception types are in P2 vs the excluded ordering scope?
4. **P3 disaggregation measures (#3):** pick the 4–5 extra measures from `10_demand_daily`'s 40+ active.
5. **P3 customer mapping:** do `expansion_loads` customer codes (e.g. FASTENAL) map 1:1 to the 56 mkedg5?
6. **Bonus plans/tables:** should P2 use `23 Transition SKU Supply Plan`, `frozen_planned_purchase_orders`,
   `purchase_order_schedule/change_orders`? (Strongly relevant to #9–13,17,18 but not in the docs.)
7. **`order_line_fulfillment_accumulating_snapshot`:** validate milestone-date coverage (>80%) before
   relying on it for lead-time/on-time — else use `customer_shipments` (carrier + actual_ship_date 99.96%).

## What is NOT built here (by design)
No pipelines, no joined production queries, no dimensional build. This is the understanding layer that lets
us choose the vertical slice next (recommended: one P1 SKU-org-week reconciliation once the receipt
crosswalk question is answered).
