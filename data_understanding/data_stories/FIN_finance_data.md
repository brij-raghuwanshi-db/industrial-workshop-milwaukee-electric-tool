# Where the FINANCE data lives in the story

**As-of 2026-08-30 · READ-ONLY · queried live.** Every dollar figure in the stories (the $0.0134 carbide part,
the ~$235K impact, working-capital, cost-weighted priority) traces to real columns. Here's exactly where.

## The primary money source: `prod_operations.edw_extension.dim_series_ext_vw` (item × org × supplier)
This is the cost spine — a full standard-cost buildup per item/org/supplier (confirmed columns):
- **`applied_standard_cost`** — THE unit cost used across the stories ($/unit). This is what turns a unit-miss
  into a $ impact (S5: 17.6M units × $0.0134 ≈ $235K).
- `standard_cost`, `active_estimated_cost` — alternate cost bases.
- **Cost breakdown (the "why is it expensive" columns):** `direct_material_cost`, `direct_labor_cost`,
  `freight_cost`, `import_fees_cost`, `import_duty_cost`, `purchase_burden_cost`, `fixed_overhead_cost`,
  `variable_overhead_cost`, `outside_ops_cost`, `equipment_cost`.
- **`currency_code`** — FX exposure (non-USD sourced items).
- `demand_materiality` — a materiality flag.
→ Freight + import_fees + import_duty as a share of applied_standard_cost = the **logistics/tariff exposure**
lens (LG/B1). This one view answers "what is a unit worth, what's it made of, and where's the cost risk."

## Inventory $ value: `prod_edw.fact.inventory_days_on_hand`
- **`on_hand_cost`** — dollar value of stock on hand (→ working-capital tied up, by item/org/day).
- `standard_cost`, `six_months_scop_cost`, `work_order_wip_cost`, `received_not_put_away_cost`,
  `in_transit_cost` (several are sparsely/NULL-populated — verify before relying).
→ "Where is capital locked?" = SUM(on_hand_cost) by org (the O/X inventory-concentration finding).

## Purchase $ (what we paid / committed): `prod_edw.fact.purchase_orders`
- **`usd_price` / `usd_line_amount`** (+ `transactional_*` and `base_*` variants) and the three currency-code
  keys (transactional / usd / base). → PO spend, price variance, committed $ on open POs, multi-currency.

## Sales $ (what we sold): `prod_edw.fact.sales_order_line_transactions`
- **`base_extended_amount` / `base_unit_amount`** (revenue), **`base_extended_cost` / `base_unit_cost`** (COGS),
  `unit_list_price`, `standard_value`, plus `order_currency` / `trans_currency` + `base_currency_rate`.
→ Revenue, margin (amount − cost), and the $ side of a shipment miss (a stockout's revenue-at-risk).

## Demand $ (forecast in dollars): `prod_edw.fact.10_demand_daily`  ⚠️ verify
Cluster-D profiling reported dollarized measures here — `final_asp`, `baseline_asp`, `invoiced_asp` (average
selling prices) and `*_amount` variants (e.g. `planner_baseline_amount`, `working_final_forecast_amount`). A
quick grep this pass didn't surface them by those exact names, so **confirm the live column names before use**
— but demand-in-$ (forecast revenue) is expected to be derivable here or via ASP × forecast-units.

## Cost of Goods sold / standard cost also on `items_scd1`
- `items_scd1.applied_standard_cost` — a per-item standard cost at the master level (matches the series view).

## How finance threads each priority
- **P1 (Actuals):** variance in **units × applied_standard_cost = $ variance**; alert tiers are $-based
  (>$50K Alert, >$200K Escalate). on_hand_cost = inventory value moved.
- **P2 (Supply Exceptions):** priority = unit-miss **× applied_standard_cost** (the fix for the raw-magnitude
  trap); cost-buildup shows freight/tariff-driven exceptions; PO $ = committed spend at risk.
- **P3 (Demand Events):** event volume × ASP = incremental **revenue** of an event; helps size/justify it.
- **P4 (Demand Exceptions):** forecast drift × ASP = **revenue-at-risk** of a bad forecast; over-forecast =
  excess inventory $ (working capital).
- **Beyond/P5 (finance-owned):** dead-stock $, inventory concentration $, FX exposure, margin analysis — all
  from on_hand_cost + the cost buildup + currency codes (B3 in BEYOND_P1P4).

## Honest caveats (finance data has the same traps)
- **Multiple cost bases** (applied_standard vs standard vs active_estimated vs the component buildup) — pick
  one deliberately; they differ. Stories use `applied_standard_cost` as the canonical unit cost.
- **NULL / 0 costs** — dim_series_ext_vw has domain-violation marker rows with null costs; some inventory cost
  columns (WIP, in-transit) are largely NULL. Distinguish "zero cost" from "uncosted."
- **Currency** — amounts come in transactional / USD / base flavors; always use the USD/base variant for
  cross-item rollups, never mix currencies.
- **Semi-additive $** — `on_hand_cost` is point-in-time just like on_hand_qty; **never sum across dates.**
- **No P&L / GL / landed-actual-freight here** — this is standard-cost + order/shipment pricing, not the
  finance general ledger. True landed cost / actual freight invoices / margin actuals would be a separate
  finance system, not `prod_edw`. Confirm before promising "actual" margin.

## One-line answer
The money lives mainly in **`dim_series_ext_vw`** (unit cost + full cost buildup + currency), with inventory
value in **`inventory_days_on_hand.on_hand_cost`**, purchase spend in **`purchase_orders` (usd_*)**, and
revenue/COGS in **`sales_order_line_transactions` (base_extended_amount/cost)** — so every "units" story can
be turned into a "$" story (impact, working capital, revenue-at-risk, margin) — but it's **standard-cost and
order pricing, not the GL**, and it carries the same cost-base / currency / NULL / semi-additive traps as the
rest of the warehouse.
