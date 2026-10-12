<div align="center">

# V7 · Excess / Overstock — Validation

</div>

**Claims (design/scenario S1):** the inverse of shortage — SKUs with PAB far above target = tied-up capital +
E&O risk; rank by $ tied up + weeks of cover. **Measures:** `excess = PAB − SS` (over a threshold),
`$ = excess × std_cost`, `weeks_cover = PAB ÷ avg_weekly_demand`. **Source:** `20_supply_daily` + cost.

---

## Test — 10 most-overstocked SKUs (>3× safety stock, next quarter)

| # | item_id | org | excess units | excess $ | weeks of cover |
|---|---|---|---|---|---|
| 1 | 290920 | 2012 | 28,169 | $5.59M | **123** |
| 2 | 290422 | 2013 | 36,960 | $4.85M | 11 |
| 3 | 273421 | 2012 | 12,263 | $4.52M | **237** |
| 4 | 301620STN | 2013 | 27,663 | $3.87M | **212** |
| 5 | 369727 | 2013 | 6,227 | $2.95M | 6 |
| 6 | 282620TB | 2012 | 18,201 | $2.41M | 14 |
| 7 | 48111814 | 2012 | 3,243 | $2.24M | 51 |
| 8 | 290920 | 2013 | 10,566 | $2.10M | 20 |
| 9 | 48112442 | 2013 | 71,147 | $2.07M | 5 |
| 10 | 48894631 | 2012 | 158,005 | $1.99M | 17 |

## 📖 The story the data tells

The mirror-image story holds up and it's uncomfortable: **there is serious money sleeping on the shelf.** Three
of the top ten carry **123, 212, and 237 weeks of cover** — that's **2.5 to 4.5 years** of supply sitting in a
DC. `273421` alone is $4.5M that will not move for ~4.5 years — textbook excess-and-obsolete risk, and *nobody
in the Day-3 room was looking at it* because the whole session was about shortage.

But the data also disciplines the metric. Look at `48112442`: it trips the ">3× safety stock" excess filter, yet
has only **5 weeks of cover** — because its demand is high, 3× its (small) safety stock is still not much
inventory. So the "3× SS" threshold **over-flags high-demand SKUs that aren't truly overstocked.** The story the
data tells is that **weeks-of-cover is the honest excess signal, not the safety-stock multiple** — the two
disagree on ~half the list, and weeks-of-cover is the one a finance partner would trust.

Net: excess is a real, large, unwatched problem (validates S1's $452M), *and* the way we currently detect it
(SS-multiple) needs to shift to a coverage/aging basis to avoid crying wolf on fast movers.

## Verdict: 🟡 works — but switch the excess trigger from "×SS" to weeks-of-cover / aging

**What works ✅**
- Excess detection + $ valuation works; genuine multi-year-cover SKUs surface ($4.5M / 237 weeks).
- Confirms the S1 thesis (excess is large and unwatched) on real named SKUs.

**Data-quality findings**
- 🔴 **DQ-1 — "3× safety stock" over-flags fast movers.** `48112442` (5 wks) and `369727` (6 wks) trip the filter
  but aren't overstocked. **Use weeks-of-cover (and aging) as the primary excess trigger**, not the SS multiple.
- 🟡 **DQ-2 — weeks-of-cover needs a robust demand denominator.** `AVG(total_demand)` over the window is crude;
  near-zero demand → absurd cover (capped at 999 here). Use a trailing/forward average and handle intermittent SKUs.
- 🟡 **DQ-3 — same cost-basis caveat as V1** (std vs landed) and component/bulk-org UoM.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Multi-year cover exists | over-buying / demand drop after purchase / MOQ-driven over-order; nobody watches the *over* side |
| ×SS over-flags | safety stock scales with demand; 3× a small SS is trivial for a high-demand SKU → false excess |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Trigger excess on weeks-of-cover + aging**, not ×safety-stock (DQ-1) | build | 🔴 must |
| 2 | Ship the **Excess board (S1)** — real $ and multi-year-cover SKUs justify it; a new finance audience | build | 🟡 should |
| 3 | Robust **weeks-of-cover denominator** (trailing/forward avg, intermittent handling) (DQ-2) | build | 🟡 should |
| 4 | Pair excess with **rebalance (V6)** — excess here may cover a shortage elsewhere | build | 🟡 should |
| 5 | Confirm cost basis + segregate component orgs (shared w/ V1) | planner/build | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V7: top overstocked SKUs by $ + weeks of cover (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
ex AS (
  SELECT product_bigint_key po, inventory_organization_bigint_key io, MAX(series_bigint_key) sk,
         MAX(projected_available_balance - safety_stock) peak_excess, MAX(safety_stock) ss,
         AVG(total_demand) avg_wk_dem, MAX(projected_available_balance) peak_pab
  FROM prod_edw.fact.`20_supply_daily`, latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0
  GROUP BY 1,2
  HAVING MAX(projected_available_balance - safety_stock) > MAX(safety_stock)*3)   -- NOTE: use MAX(safety_stock), not bare col
SELECT i.item_id, o.organization_code org, ROUND(ex.peak_excess,0) excess_u,
       ROUND(ex.peak_excess*COALESCE(x.standard_cost,0),0) excess_dollars,
       ROUND(CASE WHEN ex.avg_wk_dem>0 THEN ex.peak_pab/ex.avg_wk_dem ELSE 999 END,0) weeks_cover
FROM ex JOIN prod_edw.dimension.items_scd1 i ON ex.po=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON ex.io=o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON ex.sk=x.series_bigint_key
ORDER BY excess_dollars DESC LIMIT 10;
```

**Gotcha logged:** in a `HAVING`, reference `MAX(safety_stock)` not the bare `safety_stock` column
(`UNRESOLVED_COLUMN` otherwise). And weeks-of-cover, not ×SS, is the trustworthy excess trigger.
