# Losses due to supply-chain issues — can we quantify them in $?

**As-of 2026-08-30 · READ-ONLY · queried live.** Answer: **yes, directionally** — every issue type we traced
can be dollarized from the finance columns (FIN_finance_data.md). Below are real, queried magnitudes with
**honest caveats** — several need dedup/key-fixes before they're audit-grade (and that need is itself the
point of the pain journey).

## The loss types and what they cost (real numbers, caveated)

### L1 — Working capital tied up in inventory (the "too much" loss)
- **SUM(on_hand_cost) as of 2026-08-29 = ~$1.68 BILLION** across 48,581 items (queried).
- The *loss* portion = the slice that's excess/dead: 37% of SKUs are excess-vs-target (E2), 200–300 items
  dead 90+ days (X). Carrying cost (storage + capital, ~20–30%/yr industry rule) on the excess slice is the
  annual loss. → **$-value is real and in the data; the "excess" filter (vs target/SS) sizes the loss.**
- Issue types: #2 excess inventory, MOQ waste, dead stock, over-forecasting.

### L2 — Committed $ stuck in past-due / open POs (supply-timing loss)
- Past-due open-PO **value ≈ $10.8B raw**, BUT the PO table is **SCD2-duplicated: 378,884 raw rows vs
  166,547 distinct PO-lines (2.3× inflation)**. Deduped, the real figure is roughly **$4–5B order-value
  overdue** (must dedup on latest valid_to before quoting). → cash committed to supply that hasn't landed;
  the *loss* is the expedite premium + downstream stockouts it causes.
- Issue types: #7 supplier late, #12 PO past-due, #13 lead-time drift, logistics delay.

### L3 — Revenue-at-risk from stockouts / shortfalls (the "too little" loss)
- Method: units projected below zero PAB (or below SS) × selling price/cost = revenue/margin at risk.
- **My first query returned 0 — because I joined `product_bigint_key = series_bigint_key`, which is WRONG**
  (they're different keys; dim_series_ext_vw joins on item, not on the plan's product key). This is a live
  example of the Chapter-4 key trap. The correct path: plan shortfall units → items_scd1 → applied_standard_cost
  (or sales ASP for revenue). → **derivable, but needs the right join**; the S5 single-item version worked
  ($235K on one item), so the network rollup is a corrected-join away.
- Issue types: #1 demand-exceeds-supply, #8 safety-stock violation, forecast-under.

### L4 — Scrap / shrink / adjustment losses (inventory-adjustment loss)
- inventory_material_transaction: Production Scrap (9,791 rows/90d), Rework (3,016), Excess/Obsolete,
  Cycle-Count adjustments, plus the 69M-unit reversal on one item (P). × applied_standard_cost = write-off $.
- → real and dollarizable; the reason codes (PROD-Scrap, INV-Adjustment, CC-*) categorize the loss.
- Issue types: inventory adjustment, quality, shrink.

### L5 — Quality / rejected-receipt losses
- purchase_receipt_line: `rejected_quantity` / (received − accepted) × cost = value rejected/held (X:
  suppliers <90% acceptance). → supplier-quality loss, dollarizable per supplier.

### L6 — Logistics / freight & tariff cost exposure
- dim_series_ext_vw freight_cost + import_fees_cost + import_duty_cost as a share of unit cost, × volume on
  long lanes (LG/B1). → the recurring logistics *cost* (not a one-off loss, an ongoing drag); expedite
  premiums when late are the incremental loss.

### L7 — Forecast-error cost (plan-accuracy loss)
- forecast≫actual (V: Inkzall 269K forecast vs 4K shipped) drives either excess (L1) or, when under, stockout
  (L3). Bias × ASP = the systematic cost of bad forecasting. → both tails roll into L1/L3 in $.

## Summary table
| Loss | Real figure (queried) | $ source | Caveat |
|---|---|---|---|
| L1 inventory working capital | **$1.68B on-hand value** | on_hand_cost | loss = excess/dead slice × carry rate |
| L2 past-due PO value | ~$4–5B (deduped from $10.8B raw) | purchase_orders.usd_price | **SCD2 dedup required (2.3×)** |
| L3 stockout revenue-at-risk | per-item works ($235K S5); network TBD | ASP / applied_standard_cost | **needs correct item join (not series key)** |
| L4 scrap/shrink | scrap 9,791 + rework 3,016 rows/90d × cost | inv_material_transaction + cost | reason-coded |
| L5 rejected receipts | suppliers <90% acceptance × cost | purchase_receipt_line rejected/accepted | verify populated |
| L6 freight/tariff drag | freight+import share of cost | dim_series_ext_vw cost buildup | ongoing cost not one-off |
| L7 forecast error | Inkzall 269K→4K etc. | rolls into L1/L3 × ASP | seasonality-guard |

## Honest bottom line
**Yes — losses per supply-chain issue are quantifiable in dollars**, and even a rough live pass surfaces
**~$1.68B of inventory value and multiple $B of overdue committed POs**. BUT the exact numbers are only
trustworthy after fixing the same traps the pain journey named: **dedup SCD2 PO rows (2.3× inflation), use the
correct item join (the series-key join silently returned $0), pick one cost base, keep currency in USD, and
never sum semi-additive $ across dates.** In other words: the *loss story is in the data*, but extracting a
board-ready number re-pays the full understanding cost — exactly why a governed, certified metric layer (not
hand queries) is what makes "losses due to issues" a reliable, repeatable KPI instead of a per-analyst
adventure.
