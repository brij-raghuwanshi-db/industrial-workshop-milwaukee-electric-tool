# Data Stories — Scenario Catalog (the journeys we will walk)

**As-of:** 2026-08-30 · READ-ONLY · workspace `mke-rsc`. This is the *map* of stories. Each story = an
**anchor ID discovered by query** (not picked at random) that satisfies a real priority use-case, plus the
**path** it travels and **what attributes join on along the way**. Findings for each are written to
`data_stories/S<n>_*.md` and the data is printed inline as we go.

## Anchoring principle
The **item** is the universal spine (`item_bigint_key` in EDW facts/dims; `item_id` string is the
crosswalk to raw-Oracle tables like receipts). So most P1/P2 stories hang off **one discovered "hero item"**
that we prove is present across plan + on-hand + shipments + receipts + movements + demand + supplier. A few
stories need their own anchor: a **PO** (`po_header_id`), a **demand event** (`expansion_name`), and a
**customer** (`mkedg5`). We discover each anchor with a targeted query, then follow it.

---

## The scenarios

### Spine
- **S0 — The hero item's full presence map.** Anchor: one `item_bigint_key` / `item_id`.
  *Question:* where does an item originate and every table it shows up in, with the key it uses in each.
  *Proves:* the conformed backbone + the raw-id↔bigint crosswalk is real and traversable.

### P1 — Actuals Supply Plan (plan vs actual)
- **S1 — Receipt attainment (PO plan → actual receipt).** Anchor: hero item + a `po_header_id`.
  Path: `20_supply_daily` (planned purchase_orders for a week) → `purchase_orders` (what we ordered) →
  `receiving_receipt_transactions` (what actually arrived, raw-id, RECEIVE only) — joined through
  `items_scd1` as the crosswalk. *Proves M1 + the crosswalk + RECEIVE/DELIVER pick.*
- **S2 — Ending on-hand & WHY it moved.** Anchor: hero item × org.
  Path: `20_supply_daily` (planned PAB for the week) → `inventory_days_on_hand` (actual ending on_hand,
  point-in-time) → `inventory_material_transaction` (the 27-type ledger explaining the delta). *Proves
  M3 + root-cause categorization 2.3.7, and the semi-additivity gotcha in the flesh.*
- **S3 — Shipment attainment.** Anchor: hero item.
  Path: `20_supply_daily` (planned shipped_sales_orders / sales_orders) → `sales_order_line_transactions`
  (actual shipped, filter Standard + Invoiced/Closed, non-null shipped_quantity). *Proves M2 + the 87%-null
  gotcha handled.*

### P2 — Supply Exceptions (prioritized queue; evidence only, no PO writes)
- **S5 — Stockout / safety-stock violation, prioritized by unit miss.** Anchor: discovered item where a
  future week's `projected_available_balance` < `safety_stock` (or PAB<0) in the latest snapshot.
  Path: `20_supply_daily` (the miss) → `dim_series_ext_vw` (supplier, planner, lead_time, std cost → $ impact
  + who to route to) → `items_scd1` (ABC tier for threshold). *Proves exception #1/#8, largest-unit-miss
  prioritization, and $-impact enrichment.*
- **S6 — DC imbalance (rebalancing trigger).** Anchor: discovered item with on-hand in ≥2 orgs where one is
  long and one is short. Path: `inventory_days_on_hand` (same item, on_hand across orgs) +
  `inventory_material_transaction` transfer types. *Proves exception #15.*

### P3 — Demand Events (Excel replacement)
- **S7 — A demand event's journey.** Anchor: one `expansion_name` discovered in `expansion_loads`.
  Path: `expansion_loads` (its item × customer × month × value lines) + `expansion_dims` (its header) →
  validate items against `items_scd1` (PurchPlan?) → map its customer code to `dg5_customer_scd1` mkedg5 →
  check whether the increment shows up in `10_demand_daily` (`expansions_loadin`/`expansions_runrate`).
  *Proves the event output contract + the customer-code↔mkedg5 reconciliation open item + the round-trip.*

### P4 — Demand Exceptions
- **S9 — Forecast drift since last freeze.** Anchor: discovered (item × customer) where
  `working_final_forecast` differs materially from `frozen_working_final_forecast` in `10_demand_daily`.
  Path: `10_demand_daily` (live vs frozen) → `dg5_customer_scd1` (customer context) → `items_scd1`.
  *Proves "changed since last plan" is measurable from the frozen twins, deep-links to P3.*

---

## What each story lets us decide
- S0 fixes the **join map** (which key in which table) — the prerequisite for every pipeline.
- S1/S2/S3 validate the **P1 comparison mechanics** end-to-end on ONE real item before we generalize.
- S5/S6 prove **P2 detection has enough evidence** and the prioritization signal is computable.
- S7 proves the **P3 output contract + customer mapping** with a real legacy event.
- S9 proves **P4 drift** is deterministic from existing columns (no ML needed to start).

## End-user-question lens (applied to every pointer)
For each hop we tag it: **✅ answers a planner question** (and *what it shows* them) or **⚠️ does not**
(and what it *actually* shows — usually plumbing, a key, or a gap). This separates "data a planner would act
on" from "data that only serves the join."

## Status
Anchors are discovered live below; each S-file records the exact IDs, the printed rows, the SQL (READ-ONLY),
and the "what came along" attribute inventory.
