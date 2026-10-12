# Demand Events — Hero Item

**Hero:** `3697-22` → item master `item_id = 369722` — **M18 FUEL 2PC COMBO KIT HD/ID**
**Profiled live at source this session** (`--profile mke-rsc`, warehouse `7bd33a82f4e92206`). All [V].

## Why this is the hero

1. **Named by the business in the call** — the planner literally said *"I took the 3697 and put, like, a 20% lift on it"* in the requirement discussion. Using it makes every demo trace back to a real recorded scenario.
2. **Exercises the multi-customer core enhancement** — appears in **156 events across 43 customers** in `expansion_loads` (7,117 rows, 652 non-zero cells). Home Depot dominates (397,423 units in 2025-06) but it also spans COLONY, CONST_IND, FERGUSON, ELECTRICAL — perfect for disaggregation + multi-customer editing.
3. **Has the interesting cases** — 19 negative cells (reduce-the-forecast), sparse grid, multiple months.
4. **Clean joins** — `item_number 3697-22` → dash-normalize → `item_id 369722` (100% match); present in the demand fact via `item_bigint_key = -8290099280369104813`.
5. **Rich demand-fact footprint** — 1,705,788 rows across **370 daily snapshots**; `planner_baseline` Σ ≈ 290.7M, `working_final_forecast` Σ ≈ 327.9M, `expansions_loadin` Σ ≈ 8.87M, `expansions_runrate` Σ ≈ **−4.38M** (both event columns present and non-trivial → round-trip validation possible).

## Key facts / gotchas

| Attribute | Value |
|---|---|
| Event `item_number` | `3697-22` (dashed) |
| Item master `item_id` | `369722` (dash-less — join via `REPLACE(item_number,'-','')`) |
| `item_bigint_key` | `-8290099280369104813` (join to `10_demand_daily.product_bigint_key`) |
| Description | M18 FUEL 2PC COMBO KIT HD/ID |
| Product line | Tools Combo Kits → TOL 2 Piece Kits |
| **item_status** | **`ShipSO`** (`50.Ready to Ship Sales Orders`) — **NOT `PurchPlan`** |
| Events / customers | 156 events, 43 customers |
| Demand-fact measures | `planner_baseline`, `working_final_forecast`, `expansions_loadin`, `expansions_runrate` all populated |

## Reinforces the design (see TECHNICAL_DESIGN §16.1 + DATA_PROFILE)
- **Validation red flag holds** — the hero is `ShipSO`, so the requirements' `item_status='PurchPlan'` rule would flag it too. Confirms validation must be **non-blocking + rule-versioned + criterion reconfirmed** with analytics engineering.
- **Disaggregation base is real** — `planner_baseline` is populated for this item across 43 customers → the ratio disaggregation and $/%-lift math can be demoed on genuine data, including reproducing the call's "20% lift on 3697."

## Use in the vertical slice
Seed `3697-22`'s existing events → create a multi-customer event on it → enter a total at mkedg4 (e.g. IC FLD) → disaggregate to mkedg5 × month against `planner_baseline` → apply a **20% lift** (the call's exact scenario) → save to Lakebase with lock+audit → bulk-close one customer (→ zero) → publish Active to `sandbox_operations.po_management.demand_events_published`.

*Runner-up candidates (all multi-event, multi-customer, if a second hero is wanted): `2880-20` (162 events), `2719-20` (160), `48-11-2450` (159, batteries), `48-11-1850` (602K units).*
