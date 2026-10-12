<div align="center">

# 🔗 Join Model & ER Diagram — Supply Root-Cause Workbench

### How every table joins, on which keys, per screen — plus the conformed backbone and grain reconciliation

**Companions:** [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) · [`supply_day3_gap_tables.md`](supply_day3_gap_tables.md) · [`supply_day3_ux_design_v2.md`](supply_day3_ux_design_v2.md) · [`supply_day3_data_architecture_adr.md`](supply_day3_data_architecture_adr.md)
**All join keys verified live** on `mke-rsc` (warehouse `7bd33a82f4e92206`, READ-ONLY, 2026-09-02) via `information_schema`. Also weaves in the **industry research** done this session (control towers, demand FVA, MEIO, supplier OTIF) — see §9.

</div>

---

> ## 🎯 The single most important fact about these joins
> **Every fact in this model shares one conformed key set** — item, org, customer, series, date, plan —
> so the whole workbench is **star-joined to five conformed dimensions**. Two naming gotchas to burn in:
>
> 1. **Plan facts call the item `product_bigint_key`; transactional facts call it `item_bigint_key`.** Both
>    resolve to `items_scd1.item_bigint_key`. (verified)
> 2. **`series_bigint_key` is the hidden hero** — the item×org×supplier *planning entity* — present on the
>    plan facts, POs, on-hand, and `dim_series_ext_vw`. It's how you attach supplier / lead-time / MOQ / cost
>    to any row **without** a fragile multi-column join. (verified)

---

## 📑 Contents
1. [The conformed key backbone (the join spine)](#1--the-conformed-key-backbone)
2. [Master ER diagram](#2--master-er-diagram)
3. [The join-key dictionary (exact columns)](#3--the-join-key-dictionary)
4. [Grain reconciliation — the hard part](#4--grain-reconciliation-the-hard-part)
5. [Per-screen join graphs + table counts](#5--per-screen-join-graphs--table-counts)
6. [Table inventory & count](#6--table-inventory--count)
7. [Canonical join SQL (copy-ready skeletons)](#7--canonical-join-sql)
8. [Join hazards & rules](#8--join-hazards--rules)
9. [How industry research shaped these joins](#9--how-industry-research-shaped-these-joins)

---

## 1 · The conformed key backbone

Five dimensions conform across **every** fact. Learn these six keys and you can join anything here.

| Conformed entity | Dimension (PK) | Fact-side column(s) — **verified** |
|---|---|---|
| **Item / SKU** | `items_scd1` (`item_bigint_key`) | plan facts: `product_bigint_key`; txn facts: `item_bigint_key` |
| **Organization / DC** | `inventory_organization_scd1` (`inventory_organization_bigint_key`) | `inventory_organization_bigint_key`; sales: `fulfillment_organization_bigint_key`; rollup: `designated_organization_bigint_key` |
| **Customer** | `dg5_customer_scd1` (`dg5_customer_bigint_key`) | `dg5_customer_bigint_key` |
| **Planning entity (item×org×supplier)** | `dim_series_ext_vw` (`series_bigint_key`) | `series_bigint_key` |
| **Date** | `date_scd1` (`date_key`) | any `*_date_key` (INT yyyyMMdd) |
| **Plan version** | `supply_and_demand_plans_scd1` (`plan_id`) | `plan_id` / `plan_name` — ⚠ **supply facts use `20 Global`/`20 Mexico`; demand fact uses product-line `10 TOL`/`10 PRT`/`10 ACC`/`10 HND`/`10 QP` (see Hazard 10)** |

**Non-conformed natural keys** (used for fact→fact joins, not dims):
- `purchase_order_number` (+ `purchase_order_line_number`) — links `purchase_orders` ↔ `purchase_order_change_orders`.
- `process_date` (INT yyyyMMdd) — the **snapshot vintage**; the second half of every plan-fact grain.

---

## 2 · Master ER diagram

```
                          ╔═══════════════════════ CONFORMED DIMENSIONS ═══════════════════════╗
                          ║                                                                     ║
   ┌──────────────────┐   ║  ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────┐  ║
   │  date_scd1        │◄──╫──│ items_scd1        │  │ inventory_organization│  │ dg5_customer │  ║
   │  PK date_key      │   ║  │ PK item_bigint_key│  │ _scd1                 │  │ _scd1        │  ║
   │  date_value,      │   ║  │ item_id,          │  │ PK inventory_org_     │  │ PK dg5_      │  ║
   │  first_date_of_mo │   ║  │ selling_item_no   │  │    bigint_key         │  │  customer_   │  ║
   └──────┬────────────┘   ║  └───────┬───────────┘  │ organization_code,    │  │  bigint_key  │  ║
          │ date_key       ║          │ item /        │ designated_org_code   │  │ mkedg0..5    │  ║
          │ (all *_date_key)║          │ product_      └───────┬───────────────┘  └──────┬───────┘  ║
          │                ║          │ bigint_key            │ inventory_org_           │ dg5_     ║
          │   ┌────────────╫──────────┤                       │ bigint_key /             │ customer ║
          │   │ series_    ║  ┌────────▼───────────┐          │ designated_org_          │ _bigint  ║
          │   │ bigint_key ║  │ dim_series_ext_vw   │          │ bigint_key /             │ _key     ║
          │   │            ║  │ PK series_bigint_key│          │ fulfillment_org_         │          ║
          │   │            ║  │ origin_supplier_no, │          │ bigint_key               │          ║
          │   │            ║  │ complete_lead_time, │          │                          │          ║
          │   │            ║  │ MOQ family, std cost│          │                          │          ║
          │   │            ║  └────────┬────────────┘          │                          │          ║
          ║   ╚════════════╩═══════════╪═══════════════════════╪══════════════════════════╪══════════╝
          │                            │ series_bigint_key     │                          │
   ┌──────┴──────────────────────────────────────────────────────────────────────────────┴─────────┐
   │                                    FACTS (all star-join to the dims above)                       │
   │                                                                                                  │
   │  ┌───────────────────────┐   ┌───────────────────────┐   ┌────────────────────────────────┐    │
   │  │ 20_supply_daily        │   │ 10_demand_daily        │   │ inventory_days_on_hand          │    │
   │  │ GRAIN: item×org×week   │   │ GRAIN: item×org×cust   │   │ GRAIN: item×org×date (point-in) │    │
   │  │   ×snapshot ×plan      │   │   ×week ×snapshot ×plan│   │ on_hand_qty (NEVER sum across   │    │
   │  │ PAB, safety_stock,     │   │ working_final_forecast,│   │   dates)                        │    │
   │  │ total_demand           │   │ planner_baseline, promo│   │                                 │    │
   │  └───────────────────────┘   └───────────────────────┘   └────────────────────────────────┘    │
   │                                                                                                  │
   │  ┌───────────────────────┐   ┌───────────────────────┐   ┌────────────────────────────────┐    │
   │  │ purchase_orders        │──►│ purchase_order_change_ │   │ sales_order_line_transactions   │    │
   │  │ GRAIN: PO line×schedule│PO#│ orders                 │   │ GRAIN: SO fulfillment line      │    │
   │  │ requested/promised/    │   │ change_order_originator│   │ shipped_quantity, order_type,   │    │
   │  │ original_promise dates │   │ _type (BUYER/SUPPLIER) │   │ requested_ship_date_key         │    │
   │  └───────────────────────┘   └───────────────────────┘   └────────────────────────────────┘    │
   │                                                                                                  │
   │  ┌───────────────────────┐   ┌───────────────────────┐   ┌────────────────────────────────┐    │
   │  │ inventory_material_    │   │ sales_fulfillment_hold_│   │ transfer_orders                 │    │
   │  │ transaction (adjust)   │   │ transactions (holds)   │   │ source_org → destination_org    │    │
   │  │ transaction_type_desc  │   │ + hold_codes_vl lookup │   │ (both → inventory_org_scd1)     │    │
   │  └───────────────────────┘   └───────────────────────┘   └────────────────────────────────┘    │
   │                                                                                                  │
   │  ┌───────────────────────┐   ┌───────────────────────┐   ┌────────────────────────────────┐    │
   │  │ fact_sop_commitment    │   │ ops_scorecard_fill_    │   │ receiving_receipt_transactions  │    │
   │  │ (prod_operations.demand)│   │ rate_vw (prod_ops.sales)│  │ (quality: inspection_status)    │    │
   │  │ committed value/cost   │   │ SupplyFR, SupplyMiss,  │   │                                 │    │
   │  │ by DG5×item×org         │   │ supplier_number        │   │                                 │    │
   │  └───────────────────────┘   └───────────────────────┘   └────────────────────────────────┘    │
   │  ┌───────────────────────────────────┐   ┌─────────────────────────────────────────────────┐   │
   │  │ fact_forecast_accuracy (DK-7)      │   │ transfer_orders (DK-9/DK-11)                     │   │
   │  │ (prod_operations.demand)           │   │ Open status = IN-TRANSIT (240k open);           │   │
   │  │ planner_bias, system_bias,         │   │ src→dst org, scheduled_ship_date, item          │   │
   │  │ +/-error(_cost), lag3, rolling_6   │   │ (in-transit cost cols on on-hand fact are EMPTY)│   │
   │  │ by DG5×item×series×date            │   └─────────────────────────────────────────────────┘   │
   │  └───────────────────────────────────┘                                                          │
   │  ┌───────────────────────────────────────────────────────────────────────────────────────┐    │
   │  │ warranty_transaction (V17/N3 — prod_edw.fact, governed domain_service)                    │    │
   │  │ GRAIN: warranty claim × service-order line.  item_bigint_key = RETURNED TOOL →items_scd1  │    │
   │  │ part_bigint_key = REPLACED PART (2nd item FK — pick grain deliberately).                  │    │
   │  │ replacement_reason_code, problem_description, part_quantity, material/labor/freight_cost,  │    │
   │  │ posting_date_key→date_scd1, warranty_claim_id, serial_number.  (raw JDE/AX staging is      │    │
   │  │ upstream only — the conformed fact is a clean star spoke, NOT cross-system)               │    │
   │  └───────────────────────────────────────────────────────────────────────────────────────┘    │
   │  ┌───────────────────────────────────────────────────────────────────────────────────────┐    │
   │  │ REFERENCE LISTS (standalone controlled vocabularies — NO fact FK, do NOT join):          │    │
   │  │  dim_forecast_accuracy_reason_codes (DK-8): 12 governed reasons (Buckets +               │    │
   │  │    reason_code_description) — a picklist for the UI / ai_classify TARGET, not a join      │    │
   │  │  work_order_root_cause_scd1 (DK-8, make side): root_cause_name + definition              │    │
   │  └───────────────────────────────────────────────────────────────────────────────────────┘    │
   └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │ Job (weekly, Monday snapshot)
                                              ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
   │   SERVING (sandbox_operations.po_management) — the UI reads THESE, denormalized                 │
   │   rc_serving_sku_week · rc_forward_risk · rc_snapshot_history · rc_pattern_rollup · rc_supplier… │
   └──────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │ app reads serving; writes state
                                              ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
   │   LAKEBASE (Postgres) — action_request · action_audit_event · scenario · event_draft · outbox   │
   └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Read it as:** every fact is a spoke; the five conformed dims are the hub; `series_bigint_key` is a second
hub that carries supplier/lead-time/cost. Fact→fact joins are rare and explicit (`purchase_order_number`;
snapshot self-joins on `process_date`).

---

## 3 · The join-key dictionary

*Exact column-to-column joins. Every row verified against `information_schema`.*

### 3.1 · Fact → conformed dimension (the star joins)

| Fact | → Dimension | ON (fact col = dim col) |
|---|---|---|
| `20_supply_daily` | `items_scd1` | `product_bigint_key = item_bigint_key` |
| `20_supply_daily` | `inventory_organization_scd1` | `inventory_organization_bigint_key = inventory_organization_bigint_key` |
| `20_supply_daily` | `inventory_organization_scd1` (rollup) | `designated_organization_bigint_key = inventory_organization_bigint_key` |
| `20_supply_daily` | `dg5_customer_scd1` | `dg5_customer_bigint_key = dg5_customer_bigint_key` |
| `20_supply_daily` | `dim_series_ext_vw` | `series_bigint_key = series_bigint_key` |
| `20_supply_daily` | `date_scd1` | `date_key = date_key` (and `process_date = date_key` for vintage calendar) |
| `20_supply_daily` | `supply_and_demand_plans_scd1` | `plan_id = plan_id` (or filter `plan_name`) |
| `10_demand_daily` | *(same as above)* | `product_bigint_key`, `inventory_organization_bigint_key`, `dg5_customer_bigint_key`, `series_bigint_key`, `date_key`, `plan_id` — **identical key set** |
| `purchase_orders` | `items_scd1` | `item_bigint_key = item_bigint_key` |
| `purchase_orders` | `inventory_organization_scd1` | `inventory_organization_bigint_key = inventory_organization_bigint_key` |
| `purchase_orders` | `dim_series_ext_vw` | `series_bigint_key = series_bigint_key` |
| `purchase_orders` | `date_scd1` (×4 roles) | `requested_delivery_date_key` / `promised_delivery_date_key` / `original_promised_delivery_date_key` / `ordered_date_key` = `date_key` |
| `inventory_days_on_hand` | `items_scd1` / `inventory_organization_scd1` / `date_scd1` / `dim_series_ext_vw` | `item_bigint_key`, `inventory_organization_bigint_key`, `date_key`, `series_bigint_key` |
| `sales_order_line_transactions` | `items_scd1` | `item_bigint_key = item_bigint_key` |
| `sales_order_line_transactions` | `inventory_organization_scd1` | `fulfillment_organization_bigint_key = inventory_organization_bigint_key` ⚠ different col name |
| `sales_order_line_transactions` | `date_scd1` | `order_date_key` / `requested_ship_date_key` = `date_key` |
| `fact_forecast_accuracy` (DK-7) | `items_scd1` / `dg5_customer_scd1` / `dim_series_ext_vw` / `date_scd1` | `item_bigint_key`, `dg5_customer_bigint_key`, `series_bigint_key`, `date_key` — **same conformed spine** (clean star) |
| `transfer_orders` (DK-9/11) | `items_scd1` / `inventory_organization_scd1` ×2 / `dim_series_ext_vw` | `item_bigint_key`; `source_inventory_organization_bigint_key` & `destination_inventory_organization_bigint_key` → org dim; `series_bigint_key` |
| `warranty_transaction` (V17/N3) | `items_scd1` (returned tool) | `item_bigint_key = item_bigint_key` — **clean star join** (crosswalk found 2026-09-03; conformed `prod_edw.fact`, NOT the staging `tool_nbr` keys) |
| `warranty_transaction` (V17/N3) | `items_scd1` (replaced part — 2nd role) | `part_bigint_key = item_bigint_key` ⚠ **dual item FK** — returned-tool vs replaced-part are different grains; pick per lens, never both silently |
| `warranty_transaction` (V17/N3) | `date_scd1` | `posting_date_key = date_key` (and `last_posting_date_key`) |
| `warranty_transaction` (V17/N3) | `customer_site` dims | `bill_to_customer_site_bigint_key` / `ship_to_customer_site_bigint_key` (end-user geography: `end_user_state`/`end_user_zip` also inline) |

### 3.2 · Fact → fact (explicit, non-dim)

| From | → To | ON | Purpose |
|---|---|---|---|
| `purchase_orders` | `purchase_order_change_orders` | `purchase_order_number = purchase_order_number` | attach "who moved the date" (`change_order_originator_type`) |
| `20_supply_daily` (t1) | `20_supply_daily` (t2) | `product_bigint_key`, `inventory_organization_bigint_key`, `date_key` equal; `t1.process_date <> t2.process_date` | **gap decomposition / priors / chronic** — compare the *same target week* across snapshot vintages |
| `10_demand_daily` (t1) | `10_demand_daily` (t2) | same item/org/cust/`date_key`; different `process_date` | **priors / late 1–6** forecast evolution |
| `transfer_orders` | `inventory_organization_scd1` (×2) | `source_inventory_organization_bigint_key` = dim, `destination_inventory_organization_bigint_key` = dim | interorg transfer lanes |
| `sales_fulfillment_hold_transactions` | `hold_codes_vl` | `hold_code_bigint_key = hold_code_bigint_key` | hold reason text |

### 3.3 · The supplier bridge (two paths — pick per context)

| Need | Path | Keys |
|---|---|---|
| Supplier for a **plan/PO/on-hand row** | via series | fact.`series_bigint_key` → `dim_series_ext_vw.series_bigint_key` → `origin_supplier_number` / `supplier_number` |
| Supplier for a **change order** | direct | `purchase_order_change_orders.supplier_bigint_key` (+ `supplier_site_bigint_key`) |
| Supplier **fill-rate/OTIF** | via number | `dim_series_ext_vw.origin_supplier_number` = `ops_scorecard_fill_rate_vw.supplier_number` |

---

## 4 · Grain reconciliation — the hard part

The facts do **not** share a grain. Joining them naively double-counts or misaligns. The rules:

| Fact | Native grain | Time key | Reconcile to the UI's week/month by… |
|---|---|---|---|
| `20_supply_daily` | item×org×**week**×snapshot×plan | `date_key` = **Monday** of the week | already weekly — the UI's canonical grain |
| `10_demand_daily` | item×org×**customer**×week×snapshot×plan | `date_key` (weekly), **planned monthly** | roll weekly→month via `date_scd1.first_date_of_month` for demand-surprise (default monthly) |
| `inventory_days_on_hand` | item×org×**day** (point-in-time) | `date_key` | pick the **week-end** date_key; **never SUM across dates** (it's a level, not a flow) |
| `sales_order_line_transactions` | **event** (fulfillment line) | `order_date_key` / `requested_ship_date_key` | SUM `shipped_quantity` grouped into the week/month bucket |
| `purchase_orders` | **PO line × schedule** | 4 date roles | bucket by `promised_delivery_date_key` into the risk week |
| `purchase_order_change_orders` | **change event** | `change_order_date_key` | count/aggregate per PO or per supplier over a window |

> ⚠️ **The two cardinal grain sins to avoid:**
> 1. **Summing `on_hand_qty` across dates** — it's a snapshot level (semi-additive over time). Aggregate only across item/org at a *single* date.
> 2. **Joining plan (weekly) to demand-surprise (monthly) at weekly grain** — a weekly demand number is just a
>    monthly average / N (the transcript flagged this). Default demand comparisons to **month**; only offer
>    week behind the toggle with a caveat.

**Snapshot discipline (the backbone of half these screens):** always pin `process_date` first. The *same target
week* (`date_key`) read at *different* `process_date` vintages = plan movement (priors, gap-decomposition,
chronic). The *latest* `process_date` = the current picture (watchlist, waterfall, forward-risk). Mixing
vintages without pinning is the #1 way to get a wrong number.

---

## 5 · Per-screen join graphs + table counts

*For each UI screen: how many source tables, the join graph, and the exact keys. "Serving" = the pre-built
`rc_*` table the UI actually reads (per the ADR); the graph shows what the **Job** joins to build it.*

### 5.1 · Watchlist (Now / Coming-Risk / Patterns) — **7 source tables**
```
   20_supply_daily ──product_bigint_key──► items_scd1
        │  ├──inventory_organization_bigint_key──► inventory_organization_scd1 (+designated_org_code rollup)
        │  ├──series_bigint_key──► dim_series_ext_vw (std_cost, lead_time)
        │  ├──date_key──► date_scd1
        │  └──(self-join on process_date)──► chronic / forward-risk
        │
        └──item×org──► fact_sop_commitment (dg5_customer_bigint_key, committed value)  ⭐stakes
   → rc_serving_sku_week + rc_forward_risk + rc_snapshot_history + rc_pattern_rollup
```
Joins on: `product_bigint_key`, `inventory_organization_bigint_key` / `designated_organization_bigint_key`,
`series_bigint_key`, `date_key`, `process_date` (self), + `fact_sop_commitment` on item×org×`dg5_customer_bigint_key`.

### 5.2 · Root-cause investigation / Waterfall (hero) — **~9 source tables**
```
   20_supply_daily (position, PAB, safety_stock) ──┐
   10_demand_daily (demand_variance) ──────────────┤ item×org×week (+ dg5 for demand)
   purchase_orders (supply_variance) ──────────────┤
   sales_fulfillment_hold_transactions (holds_var) ┤
   inventory_material_transaction (adjustments) ───┘
        + dims: items_scd1, inventory_organization_scd1, dg5_customer_scd1, date_scd1, dim_series_ext_vw
        + self-join 20_supply_daily on process_date → two-tone gap (consumption vs target-refresh)
   → rc_serving_sku_week (all buckets + SS-at-lead-time + likely_cause pre-computed)
```
The three variance buckets each come from a different fact, **aligned on item×org×week** (demand also on
`dg5_customer_bigint_key`); SS-at-lead-time = `safety_stock` at `date_key = snapshot + complete_lead_time`
(lead time from `dim_series_ext_vw`).

### 5.3 · Demand drill (consumption + priors) — **5 tables**
```
   10_demand_daily ──dg5_customer_bigint_key──► dg5_customer_scd1   (who + promo/base cols)
        ├──product_bigint_key──► items_scd1
        ├──date_key──► date_scd1  (bucket to month)
        └──self-join on process_date (fixed date_key, varying vintage) ──► priors / late 1–6
   + sales_order_line_transactions (actual shipped) ──item×org, bucketed to month──► consumption %
```
Consumption % join: demand forecast (`10_demand_daily`) LEFT JOIN actual (`sales_order_line_transactions`)
on `item_bigint_key` + org + month-bucket(`date_scd1`).

### 5.4 · Supply drill + supplier scorecard — **5 tables**
```
   purchase_orders ──purchase_order_number──► purchase_order_change_orders (originator_type)
        ├──series_bigint_key──► dim_series_ext_vw (supplier, lead time)
        └──*_date_key──► date_scd1 (slip = promised − requested)
   dim_series_ext_vw.origin_supplier_number = ops_scorecard_fill_rate_vw.supplier_number  (fill rate)
   → rc_supplier_scorecard
```

### 5.5 · Holds drill — **4 tables**
```
   sales_fulfillment_hold_transactions ──hold_code_bigint_key──► hold_codes_vl
   inventory_material_transaction (transaction_type_description LIKE '%Adjustment%')
   receiving_receipt_transactions (inspection_status_code = 'REJECTED')   quality
        all ──item×org──► items_scd1 / inventory_organization_scd1
```

### 5.6 · Scenario Studio — **3 tables** (seed) + Lakebase
```
   20_supply_daily (overrideable component cols) ──series_bigint_key──► dim_series_ext_vw (MOQ/lead constraints)
        + supply_and_demand_planned_purchase_order (flex PO lines)
   recompute IN-APP → save scenario → Lakebase.scenario
```

### 5.7 · Recommended-Action panel — **4 tables** (rules inputs)
```
   dim_series_ext_vw (MOQ family, make/buy, supplier, lead time)
   + work_center_scd1 / domain_work_order.* (add-shift capacity)
   + inventory_days_on_hand + transfer_orders (transfer feasibility, pooled avail)
   → deterministic rules → action options → Lakebase.action_request
```

### 5.8 · Escalation, Action Log, Value & Impact — **Lakebase + serving**
No new source joins; read `rc_*` + Lakebase (`action_request`→`action_outcome_history`). Value page self-joins
`20_supply_daily` snapshots (gap at send vs +2wk) for outcome proof.

---

## 6 · Table inventory & count

**Distinct source tables across the whole workbench: 19** (17 read-only source + 2 read-only prod_operations
views) + **2 reference lists** + **5 serving tables** (`sandbox_operations.po_management`) + **Lakebase** entities.
*(+1 vs prior: `fact_forecast_accuracy` added from the transcript re-read; `transfer_orders` role expanded to in-transit.)*

| # | Table | Schema | Role | Screens |
|---|---|---|---|---|
| 1 | `20_supply_daily` | prod_edw.fact | plan snapshot (position/SS/demand) | Watchlist, Waterfall, Coming-Risk, Chronic, Gap-decomp, Scenario, Value |
| 2 | `10_demand_daily` | prod_edw.fact | demand + promo/base + priors | Waterfall, Demand drill, Priors |
| 3 | `purchase_orders` | prod_edw.fact | PO requested/promised dates | Waterfall, Supply drill |
| 4 | `purchase_order_change_orders` | prod_edw.fact | who moved the date | Supply drill |
| 5 | `inventory_days_on_hand` | prod_edw.fact | on-hand actual | Waterfall (position), Actions (transfer) |
| 6 | `sales_order_line_transactions` | prod_edw.fact | actual shipped (consumption) | Demand drill |
| 7 | `inventory_material_transaction` | prod_edw.fact | adjustments | Holds drill |
| 8 | `sales_fulfillment_hold_transactions` | prod_edw.fact | holds | Holds drill |
| 9 | `hold_codes_vl` | prod_edw.staging_oracle_fusion_erp | hold reason lookup | Holds drill |
| 10 | `receiving_receipt_transactions` | prod_edw.staging_oracle_fusion_erp | quality inspection | Holds drill |
| 11 | `transfer_orders` | prod_edw.fact | interorg transfers | Actions, org rollup |
| 12 | `supply_and_demand_planned_purchase_order` | prod_edw.fact | planned PO lines | Scenario |
| 13 | `work_center_scd1` (+ `domain_work_order.*`) | prod_edw.dimension | make capacity | Actions |
| 14 | `fact_sop_commitment` | prod_operations.demand | committed value (stakes) | Watchlist, Escalation |
| 15 | `ops_scorecard_fill_rate_vw` | prod_operations.sales | supplier fill rate/OTIF | Supply drill |
| 16 | `dim_series_ext_vw` | prod_operations.edw_extension | supplier/lead-time/MOQ/cost | (almost every screen) |
| 17 | `fact_forecast_accuracy` (DK-7) | prod_operations.demand | **governed** forecast bias (planner vs system), error/cost, lag-3, rolling-6 | Forecast-Bias (S5), Demand drill |
| D1–D5 | `items_scd1`, `inventory_organization_scd1`, `dg5_customer_scd1`, `date_scd1`, `supply_and_demand_plans_scd1` | prod_edw.dimension | conformed dims | all |
| R1–R2 | `dim_forecast_accuracy_reason_codes` (DK-8), `work_order_root_cause_scd1` | prod_operations.demand / prod_edw.dimension | **reference lists** (controlled vocab; NOT joined — picklist / `ai_classify` target) | Bias drill, feedback loop, action log |

> **Practical read:** a planner's single investigation *logically* touches ~9 tables, but because the serving
> layer pre-joins them, the **app issues 1–2 small queries per screen**, not a 9-table join over 13.4B rows.

---

## 7 · Canonical join SQL

*Copy-ready skeletons (READ-ONLY). These are the Job's build queries; the UI reads the resulting `rc_*` tables.*

### 7.1 · Hero position + SS-at-lead-time (latest snapshot)
```sql
-- READ-ONLY. Grain: item×org×forward-week for one SKU at the latest snapshot.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`)
SELECT s.product_bigint_key, i.item_id, o.organization_code, o.designated_org_code,
       s.date_key, d.date_value,
       s.projected_available_balance, s.safety_stock,
       (s.projected_available_balance - s.safety_stock)          AS ss_gap,
       GREATEST(0, s.safety_stock - s.projected_available_balance) AS shortfall_units,
       x.complete_lead_time, x.std_cost                            -- via series
FROM prod_edw.fact.`20_supply_daily` s
JOIN latest                              ON s.process_date = latest.pd
JOIN prod_edw.dimension.items_scd1 i     ON s.product_bigint_key = i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o
                                         ON s.inventory_organization_bigint_key = o.inventory_organization_bigint_key
JOIN prod_edw.dimension.date_scd1 d      ON s.date_key = d.date_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x
                                         ON s.series_bigint_key = x.series_bigint_key
WHERE s.plan_name = '20 Global Supply Plan' AND i.item_id = :item;
```

### 7.2 · Gap decomposition — same target week across two vintages (the self-join)
```sql
-- READ-ONLY. "target refreshed" vs "real position change" for target week :wk.
SELECT now.date_key,
       now.safety_stock - prior.safety_stock                          AS delta_target_refresh,
       now.projected_available_balance - prior.projected_available_balance AS delta_position
FROM prod_edw.fact.`20_supply_daily` now
JOIN prod_edw.fact.`20_supply_daily` prior
  ON  now.product_bigint_key = prior.product_bigint_key
  AND now.inventory_organization_bigint_key = prior.inventory_organization_bigint_key
  AND now.date_key = prior.date_key                 -- SAME target week
  AND now.plan_name = prior.plan_name
WHERE now.date_key = :wk
  AND now.process_date = :latest_snap AND prior.process_date = :earlier_snap;
```

### 7.3 · Consumption % — demand forecast LEFT JOIN actual shipped (monthly)
```sql
-- READ-ONLY. Demand surprise by DG5, monthly bucket.
SELECT c.mkedg5, d.first_date_of_month AS mo,
       SUM(dm.working_final_forecast)                AS forecast,
       SUM(COALESCE(so.shipped_quantity,0))          AS actual,
       ROUND(SUM(COALESCE(so.shipped_quantity,0)) / NULLIF(SUM(dm.working_final_forecast),0)*100,1) AS consumption_pct
FROM prod_edw.fact.`10_demand_daily` dm
JOIN prod_edw.dimension.dg5_customer_scd1 c ON dm.dg5_customer_bigint_key = c.dg5_customer_bigint_key
JOIN prod_edw.dimension.date_scd1 d         ON dm.date_key = d.date_key
LEFT JOIN prod_edw.fact.sales_order_line_transactions so
       ON so.item_bigint_key = dm.product_bigint_key
      AND so.fulfillment_organization_bigint_key = dm.inventory_organization_bigint_key
      AND date_trunc('month', <so date via date_scd1>) = d.first_date_of_month
WHERE dm.process_date = :latest_snap
  AND dm.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan')  -- demand plans are product-line-split, NOT '20 Global'
GROUP BY c.mkedg5, d.first_date_of_month;
```

### 7.4 · PO slip + who moved it
```sql
-- READ-ONLY.
SELECT po.purchase_order_number, po.purchase_order_line_number,
       rq.date_value AS requested, pr.date_value AS promised,
       (po.promised_delivery_date_key - po.original_promised_delivery_date_key) AS slip_days_keydiff,
       co.change_order_originator_type            -- BUYER / SUPPLIER / REQUESTER / SYSTEM
FROM prod_edw.fact.purchase_orders po
JOIN prod_edw.dimension.date_scd1 rq ON po.requested_delivery_date_key = rq.date_key
JOIN prod_edw.dimension.date_scd1 pr ON po.promised_delivery_date_key = pr.date_key
LEFT JOIN prod_edw.fact.purchase_order_change_orders co
       ON po.purchase_order_number = co.purchase_order_number
WHERE po.item_bigint_key = :item_key;
```

### 7.5 · Forecast bias — governed (DK-7, prefer over empirical)
```sql
-- READ-ONLY. MKE's own governed accuracy fact — planner vs system bias split.
SELECT fa.selling_item_number, c.mkedg5,
       fa.planner_bias, fa.system_bias,
       fa.positive_error, fa.negative_error, fa.positive_error_cost, fa.negative_error_cost,
       fa.working_final_forecast_lag3_units, fa.rolling_6_working_final_forecast_lag3_units
FROM prod_operations.demand.fact_forecast_accuracy fa
JOIN prod_edw.dimension.dg5_customer_scd1 c ON fa.dg5_customer_bigint_key = c.dg5_customer_bigint_key
WHERE fa.item_bigint_key = :item_key;
-- Reason codes are a REFERENCE picklist (dim_forecast_accuracy_reason_codes) — surfaced in the UI /
-- used as the ai_classify target; there is NO reason FK on the fact, so do NOT attempt a join.
```

### 7.6 · In-transit / count-integrity (DK-11 — from OPEN transfer orders, NOT the empty cost cols)
```sql
-- READ-ONLY. Open transfer past its scheduled ship = "projected healthy but not actually here yet".
SELECT t.item_bigint_key, o1.organization_code AS src, o2.organization_code AS dst,
       t.requested_quantity, t.scheduled_ship_date, t.status
FROM prod_edw.fact.transfer_orders t
JOIN prod_edw.dimension.inventory_organization_scd1 o1 ON t.source_inventory_organization_bigint_key = o1.inventory_organization_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o2 ON t.destination_inventory_organization_bigint_key = o2.inventory_organization_bigint_key
WHERE t.status = 'Open' AND t.item_bigint_key = :item_key;
-- NOTE: inventory_days_on_hand.in_transit_cost / work_order_wip_cost / received_not_put_away_cost
-- are EMPTY network-wide (verified) — do NOT rely on them; use open transfer_orders instead.
```

### 7.7 · Returns / warranty — conformed, item-keyed (V17/N3, verified 2026-09-03)
```sql
-- READ-ONLY. The returns/quality lens. Uses the CONFORMED fact (item_bigint_key), NOT staging tool_nbr.
-- Returned-tool grain (the tool that came back):
SELECT i.item, i.selling_item_number,
       w.replacement_reason_code, w.problem_description,
       w.part_quantity, w.material_cost, w.labor_cost, w.freight_cost,
       w.warranty_claim_id, w.serial_number, w.posting_date_key
FROM prod_edw.fact.warranty_transaction w
JOIN prod_edw.dimension.items_scd1 i ON w.item_bigint_key = i.item_bigint_key   -- returned tool
WHERE w.posting_date_key >= 20260101 AND i.item IS NOT NULL;
-- ⚠ For the REPLACED-PART grain (parts consumed by the repair), join part_bigint_key = i.item_bigint_key
--   instead — a DIFFERENT question (part demand), never mixed with returned-tool counts in one measure.
-- Provenance: prod_edw.domain_service already integrated JDE/AX/Oracle/Connect upstream; do NOT reach
--   into staging_jde.fact_warranty_tool (tool_nbr) — that layer has no EDW item key.
```

---

## 8 · Join hazards & rules

| # | Hazard | Rule |
|---|---|---|
| 1 | **`product_bigint_key` vs `item_bigint_key`** | plan facts = `product_bigint_key`; txn facts = `item_bigint_key`; both → `items_scd1.item_bigint_key`. Never assume one name. |
| 2 | **Sales org column differs** | `sales_order_line_transactions` uses `fulfillment_organization_bigint_key` (not `inventory_organization_bigint_key`). |
| 3 | **Snapshot not pinned** | always fix `process_date` first; mixing vintages silently mixes plan versions. |
| 4 | **Summing on-hand across dates** | `on_hand_qty` is semi-additive — aggregate across item/org at ONE date only. |
| 5 | **Weekly demand-surprise** | demand is monthly; default month, week only with a caveat. |
| 6 | **Digit-leading table names** | backtick `` `20_supply_daily` `` / `` `10_demand_daily` ``. |
| 7 | **Fan-out on PO changes** | one PO can have many change orders → aggregate or pick latest before joining, or you multiply PO rows. |
| 8 | **SCD dims** | join to the *current*/effective row of `*_scd1` (filter current flag) to avoid duplicate dim rows. |
| 9 | **Cross-org rollup** | pool via `designated_organization_bigint_key`/`designated_org_code`, not by summing arbitrary org rows. |
| 10 | **Plan filter — and supply≠demand plan names (use the FULL string)** | always constrain `plan_name` — unfiltered mixes plans. **Supply facts (`20_supply_daily`) = `'20 Global Supply Plan'`/`'20 Mexico Supply Plan'`. Demand fact (`10_demand_daily`) = product-line-split `'10 TOL Demand Plan'`/`'10 PRT Demand Plan'`/`'10 ACC Demand Plan'`/`'10 HND Demand Plan'`/`'10 QP Demand Plan'`.** ⚠ The value is the **full string** — filtering `'10 TOL'` (short form) returns **0 rows** (verified 2026-09-03 during the ID-catalog run). Filtering a `20 *` name on the demand fact also returns 0. Pick the right family per fact, and use the complete plan name. |
| 11 | **Reason codes are a reference list, not a dimension** | `dim_forecast_accuracy_reason_codes` (DK-8) has only `Buckets` + `reason_code_description` and **`fact_forecast_accuracy` carries no reason FK.** Treat it as a controlled-vocab picklist / `ai_classify` target — **do not attempt a join** (there's no key). |
| 12 | **On-hand in-transit/WIP cost columns are EMPTY** | `inventory_days_on_hand.in_transit_cost` / `work_order_wip_cost` / `received_not_put_away_cost` are $0 network-wide (verified). For in-transit / count-integrity (DK-11) use **`transfer_orders` where `status='Open'`** (240k open), not these columns. |
| 13 | **Lag-N needs the snapshot self-join** | only `lag1` & `lag3` exist as columns (DK-10). For lag-2/4/5/6 (the "lake-one/lake-four story") self-join `10_demand_daily` on `process_date` for a fixed `date_key` — do not expect pre-built lag columns. |
| 14 | **Supplier names fragment (DK-13b)** | `origin_supplier_name` has multiple variants for one entity (TTI `LIMITED`/`LTD`/`LMTD`; `TECHTRONIC CORDLESS GP (OUTSRCD PRDCTN)` vs `(OUTSRC SVPT)`). **Normalize/canonicalize before any supplier-level aggregation** (constraint convergence, scorecard) or concentration is understated and the constraint action fragments. Prefer `origin_supplier_number` where a clean id exists. |
| 15 | **Lifecycle flags are BOOLEAN, not 'Y'/'Yes'** | `items_scd1.transition_sku_flag` and `is_npd_item` are **BOOLEAN** — compare `= true`, never `IN ('Y','Yes')` (throws `DATATYPE_MISMATCH`). Verified 2026-09-03 during the ID-catalog run (V15). |
| 16 | **`fact_forecast_accuracy` max `date_key` is a FUTURE bucket** | the fact spans to ~`20280901`; its latest `date_key` has **no actuals yet**. For a real bias/error read, window to a **past** range (e.g. Jan–Aug 2026) — filtering on `MAX(date_key)` returns rows with zero error. Verified 2026-09-03 (V8). |
| 17 | **Holds are never "open" — recency is the signal** | `sales_fulfillment_hold_transactions` always carries a `hold_release_date_key` (**0 open network-wide**, 2.4B rows). Do **not** filter `hold_release_date_key IS NULL` (returns nothing). Use **`hold_apply_date_key` recency** for active-hold pressure and **`hold_lag_hours`** for recovery velocity (V5/V21, verified 2026-09-03). |

### Recoverability (DK-15) — no new join, but a bimodal-lead-time hazard
`recoverability_class` = `first_cross_week > today + complete_lead_time` → RECOVERABLE else UNRECOVERABLE.
Uses `20_supply_daily` forward first-cross + **`dim_series_ext_vw.complete_lead_time`** (already the series join).
**Hazard #15 — lead time is BIMODAL (median 2d, avg 122d):** never use an average lead time; join per-SKU
`complete_lead_time`. Damage-control path = recoverability × org-rollup: UNRECOVERABLE + in-network excess
(`designated_org_code`) = TRANSFER (20%), else ALLOCATE (80%).

### Convergence joins (DK-13) — grouping the star by constraint, not SKU
Convergence analysis is the **same conformed star, aggregated on a different key**:
- **Multi-cause (13a):** join the three variance sources (`20_supply_daily` gap, `10_demand_daily` over-consumption, `purchase_orders` slip) on `item_bigint_key`/`product_bigint_key`, then rank co-firing causes per SKU.
- **Shared-constraint (13b):** shortage SKUs (`20_supply_daily`) → `series_bigint_key` → `dim_series_ext_vw.origin_supplier_name` (**normalized**, hazard #14) → `GROUP BY supplier`. Swap the group key to component / `designated_org_code` for other constraint types.
- **Risk-wave (13c):** forward first-cross `date_key` (from `20_supply_daily`) → `GROUP BY week`. No new join — an aggregation of the forward-risk query.

### Classifier-axis data keys (N/DK, validated V15–V26) — all off the conformed spine

*The confirmed axes are **item-master / series attributes** joined to the existing star — no new fact joins.*

| Axis (req) | Source column | Join path | Notes |
|---|---|---|---|
| **Lifecycle** (V15/N1) | `items_scd1.transition_sku_flag`, `is_npd_item`, `npd_launch_date` | fact `product_bigint_key`/`item_bigint_key` → `items_scd1.item_bigint_key` | ⚠ on the **item master**, NOT `10_demand_daily.transition_active_flag` (that's NULL — hazard #16) |
| **Criticality** (V22/DK-16) | `dim_series_ext_vw.inventory_abc_class` (also `global_/local_planning_abc_code`) | fact `series_bigint_key` → `dim_series_ext_vw` | 37% Unclassified → fallback rule needed |
| **Demand-class** (V24/DK-18) | *derived* — ADI proxy = `SUM(shipments_history>0)/COUNT(periods)` | `10_demand_daily` per item over periods | computed, no column; <34% = intermittent |
| **Dormant** (V23/DK-17) | *derived* — `MAX(date_key)` where `shipments_history>0` (last-ship recency) | `10_demand_daily` per item | ⚠ NOT `obsolete_date` (too sparse — hazard #17) |
| **Intentional-hold** (V26/DK-20) | `dim_series_ext_vw.safety_stock_managed_flag='Yes'` (+ `inventory_planning_method`) | fact `series_bigint_key` → `dim_series_ext_vw` | partial signal; no explicit Strategic-Reserve/BOM flag |
| **Found-inventory** (V18/N4) | `inventory_material_transaction.transaction_quantity` **signed** | item/org keys | positive = found/heal, negative = lost |
| **Alignment / health / Sankey** (V26/DK-20) | derived from `20_supply_daily` gap + `inventory_days_on_hand.on_hand_cost` × `inventory_abc_class` | existing joins | Sankey: Total$ → ABC → health-state |
| **Returns / warranty** (V17/N3) | ✅ `prod_edw.fact.warranty_transaction.item_bigint_key` → `items_scd1.item_bigint_key` | **conformed, item-keyed** — clean star join (+ `replacement_reason_code`, `problem_description`, cost cols) | ✅ Ready — crosswalk found 2026-09-03 |

**New hazards from this pass:**
- **#16 — lifecycle is item-master, not demand-fact.** `10_demand_daily.transition_active_flag` is 100% NULL;
  use `items_scd1.transition_sku_flag`/`is_npd_item` (V15).
- **#17 — `obsolete_date` is too sparse for dormant.** Use last-shipment recency from `10_demand_daily`
  `shipments_history` instead (V23).
- **#18 — RESOLVED (2026-09-03): warranty/returns ARE conformed and item-keyed.** The earlier "cross-system,
  no crosswalk" read looked only at raw `staging_jde`/`staging_ax` tables. The governed **`prod_edw.fact.warranty_transaction`**
  (and `fact.service_order_warranty`) carry `item_bigint_key` → clean join to `items_scd1`; the whole
  `domain_service` schema already integrated JDE/AX/Oracle/Connect upstream. Use the conformed fact, **not** the
  staging tool_nbr keys. (V17/N3 now ✅, 60 real IDs.) *Watch-out that remains:* `part_bigint_key` (the replaced
  part) differs from `item_bigint_key` (the returned tool) — pick the grain deliberately.

---

## 9 · How industry research shaped these joins

*The web research done earlier this session (control towers, demand FVA, MEIO, supplier OTIF) informed several
join/derivation choices — cited so the modeling isn't just internal opinion.*

| Research finding (source) | How it shows up in the join model |
|---|---|
| **Control towers correlate signals across demand/supply/logistics via a unified layer** (o9 EKG, Kinaxis concurrent model) | the conformed-dim backbone + `series_bigint_key` bridge is our lightweight version — one join spine so demand, supply, holds all align on item×org×week |
| **Forecast Value Added / lag-based accuracy waterfall** (IBF, Lokad) | the `10_demand_daily` **self-join across `process_date`** (priors / late 1–6) is exactly the lag-waterfall pattern; late-3 as standard metric |
| **Demand decomposition: base vs promo uplift, by account** (CPG practice) | join `10_demand_daily` promo/base columns × `dg5_customer_scd1` to split demand-surprise by type and customer |
| **MEIO / inventory pooling across a network; days-of-coverage vs statistical SS** | `designated_org_code` rollup join = network pooling; `safety_stock` self-join = DOC-vs-actual movement (gap decomposition) |
| **OTIF measured to BOTH requested and promise date; capture change originator + reason (EDI 860/865)** (Gartner) | our supply drill joins `purchase_orders` (requested AND promised/original) + `purchase_order_change_orders.change_order_originator_type` — the "who initiated" the research says to capture |
| **Supplier scorecards: fill rate, confirmed-date moves, chronic offenders** | `ops_scorecard_fill_rate_vw` join by `supplier_number` + chronic-slip count from change orders = the scorecard pattern |

> **Net:** the big platforms buy this with a proprietary knowledge graph; we approximate it with a **conformed
> star + two hub keys (dims + `series_bigint_key`)** — enough to correlate the same signals, far less to build,
> and it lands in the governed serving layer instead of a black box.

---

<div align="center">

### 📌 Join model in one line
**One conformed star — item, org, customer, series, date, plan — joins every fact; `series_bigint_key` is the
second hub carrying supplier/lead-time/MOQ/cost; snapshot vintage (`process_date`) is pinned for current
views and self-joined for plan-movement views; ~18 source tables collapse into 5 pre-joined serving tables the
UI reads in 1–2 small queries per screen.**

*All keys verified live READ-ONLY on `mke-rsc`. Serving tables live in `sandbox_operations.po_management`;
state in Lakebase; `prod_edw`/`prod_operations` never written.*

</div>
