<div align="center">

# V1 · Watchlist / Top-Missing-Items — Validation

</div>

**Claims (from design):** rank at-risk SKUs by shortfall + $ at risk; show low point, weeks at risk, likely
cause; entry point of the whole workbench. **Measures tested:** `ss_gap = PAB − safety_stock`,
`shortfall`, `low_point = MIN(PAB)`, `$ at risk = |gap| × standard_cost`. **Source:** `20_supply_daily` +
`items_scd1` + `inventory_organization_scd1` + `dim_series_ext_vw` (cost via `series_bigint_key`).

---

## The 10 real items (live, latest snapshot, next quarter, `20 Global`)

| # | item_id | org | worst gap (u) | low point (PAB) | qtr demand | $ at risk |
|---|---|---|---|---|---|---|
| 1 | **369722** (hero 3697-22) | 2012 | −38,734 | **+15,906** | 117,950 | **$6.98M** |
| 2 | 301621STN | 2013 | −22,522 | +7,579 | 4,440 | $4.78M |
| 3 | PN0013905 | 8000 | −7,571,303 | **−1,047,827** | 4,127,754 | $3.96M |
| 4 | 293020J | 2013 | −28,168 | −16,915 | 44,241 | $3.37M |
| 5 | 377120 | 2012 | −21,496 | −14,780 | 17,647 | $3.17M |
| 6 | 296720 | 2012 | −31,297 | +20,457 | 43,073 | $2.79M |
| 7 | 48111819 | 2012 | −29,257 | −18,621 | 36,335 | $2.66M |
| 8 | 48111852 | 2012 | −48,551 | **+43,158** | 259,038 | $2.60M |
| 9 | 48111862ZY | 2012 | −27,565 | −7,820 | 29,240 | $2.37M |
| 10 | 271920 | 2013 | −48,063 | −8,862 | 91,955 | $2.36M |

## 📖 The story the data tells

Open the watchlist cold and the data narrates a clear opening scene: **the top of the book is dominated by the
FUEL/PACKOUT franchise** — the hero **3697-22 sits at #1 with $6.98M at risk**, and four of the top ten are
`4811xxxx` PACKOUT SKUs, all in the Olive Branch org 2012. This is not noise: it says the biggest dollar
exposure is concentrated in a *handful of flagship, high-cost SKUs at one org* — exactly the kind of thing a
product/channel partner walks in asking about, and exactly why the planners field this question daily.

But the data immediately complicates the story in a *useful* way. Three of the top ten (3697-22, 296720,
48111852) are flagged red on **gap** yet never actually go negative on **on-hand** — they're below the
*safety-stock target* but not heading to zero. So the honest narrative isn't "we're about to stock out on the
hero" — it's **"we're projected to dip below our safety-stock cushion on the hero, which is a service-risk
signal, not an imminent zero."** A tool that conflated those two would cry wolf on the most visible SKU in the
book and lose planner trust on day one. The data is telling us the *severity ladder matters more than the
ranking.*

And the punchline is the cross-org row: 3697-22 looks alarming at org 2012 (−38,734 vs target) but its sister
org **2013 — same network — is sitting on +3,797 of headroom.** The data's story is that **the "shortage" is
partly a distribution problem, not a supply problem** — some of the answer is already sitting one org over. That
single fact reframes the first recommended action from "expedite a PO" to "check a transfer first," and it's
invisible on any per-org screen the planners use today.

## Verdict: 🟡 works — with one important measure-definition caveat

**What works ✅**
- Ranking by $ at risk returns sensible, high-value SKUs; the hero **3697-22 legitimately ranks #1 ($6.98M)**.
- Measures compute cleanly; cost joins via `series_bigint_key` (after fixing a correlated-subquery error — see DQ-2).
- Spans multiple orgs (2012, 2013, 8000) — the watchlist is inherently multi-org.

**Data-quality / definition findings**
- 🟡 **DQ-1 — "gap" ≠ "stockout".** Items 1, 6, 8 have a large *negative gap* (below **safety-stock target**) but a **positive low-point PAB** (never physically stock out). e.g. 3697-22: gap −38,734 but low point **+15,906**. **The watchlist must distinguish "below safety-stock target" (service-risk) from "projected negative on-hand" (hard stockout)** — else planners chase items that aren't actually going to zero. Both are valid, but they're different severities and must be labelled (ties to the goal-status vocabulary: *at risk* vs *breach*).
- 🔴 **DQ-2 — outlier org 8000.** `PN0013905` in org **8000** shows gap −7.57M, low point −1.05M on 4.1M demand — orders of magnitude larger than everything else. Org 8000 is outside the Olive Branch/Mexico set and looks like a **bulk/component or a different UoM/aggregation grain**. **Filter or segregate org 8000** (and validate its UoM) or it dominates the $-ranking with a possibly-not-comparable number.
- 🟡 **DQ-3 — cost null-safety.** `$ at risk` uses `COALESCE(standard_cost,0)` — SKUs with no series cost silently show $0 and sink in the ranking. Flag missing-cost SKUs rather than zero them.

**Within / across org (hero 3697-22)**

| org | network | worst gap | read |
|---|---|---|---|
| 2012 | 2012 | −38,734 | the flagged shortage |
| 2013 | 2012 | **+3,797** | **same network — has headroom → rebalance candidate** |
| 2093 | 2012 | −1,089 | minor |
| 2120 | 2120 | −2,498 | Mexico, separate network |
| 3031 | 3031 | +6 | fine |

→ **Cross-org insight confirmed live:** 3697-22 is short at 2012 but org 2013 (same "2012" network) has +3,797 headroom — a **transfer-before-buy** candidate (feeds V6). A per-org watchlist row would mislead; the pooled view is essential.

**Time-range behavior:** ran on next-quarter window (20260907–20261207); the `date_key BETWEEN` filter works; widening/narrowing the window changes the worst-gap as expected (longer window → deeper low points surface).

## 🔍 Root causes (of what the test exposed)

| Finding | Root cause |
|---|---|
| Gap flagged but no stockout (DQ-1) | "gap" measures distance to the **safety-stock target** (a cushion), not to zero on-hand — two different questions collapsed into one number |
| Org 8000 dominates $-ranking (DQ-2) | org 8000 is outside the OB/Mexico DC set — likely a **component/bulk org or different UoM/grain**; mixing it with finished-goods DCs is a grain violation |
| Some SKUs sink with $0 risk (DQ-3) | `standard_cost` missing on the series → `COALESCE(...,0)` silently zeroes real risk |
| Per-org row misleads (hero) | inventory pools across the network; a single-org record is "misleading" (the transcript's exact word) |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **severity split** — `below_ss_target` (service risk) vs `projected_negative_pab` (hard stockout); sort by $, filter by severity | build | 🔴 must (trust) |
| 2 | **Segregate/flag org 8000** + non-OB/Mexico orgs; confirm UoM with data owner before including in $-rank | build + data owner | 🔴 must |
| 3 | Surface a **`cost_missing` flag** instead of $0-coalescing; chase missing series cost | build + master data | 🟡 should |
| 4 | Show **pooled/network gap inline** next to per-org, with a rebalance hint | build | 🔴 must (feeds V6) |
| 5 | Persist `severity_class`, `pooled_gap`, `dollars_at_risk`, `cost_missing_flag` as **serving columns** in `rc_serving_sku_week` (ADR) | build | 🟡 should |
| 6 | Confirm the **$-at-risk cost basis** (std vs landed) with a planner before headlining dollars | planner | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V1 Watchlist: top-10 by $ at risk (READ-ONLY). warehouse 7bd33a82f4e92206
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
agg AS (
  SELECT s.product_bigint_key po, s.inventory_organization_bigint_key io,
         MAX(s.series_bigint_key) sk,
         MIN(s.projected_available_balance - s.safety_stock) min_gap,
         MIN(s.projected_available_balance) low_pab,
         SUM(s.total_demand) dem
  FROM prod_edw.fact.`20_supply_daily` s, latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0
  GROUP BY 1,2)
SELECT i.item_id, o.organization_code org,
       ROUND(a.min_gap,0) worst_gap, ROUND(a.low_pab,0) low_point,
       ROUND(a.dem,0) qtr_demand,
       ROUND(ABS(a.min_gap)*COALESCE(x.standard_cost,0),0) dollars_at_risk
FROM agg a
JOIN prod_edw.dimension.items_scd1 i ON a.po=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON a.io=o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON a.sk=x.series_bigint_key
WHERE a.min_gap<0 ORDER BY dollars_at_risk DESC LIMIT 10;
```
```sql
-- V1 across-org coverage for one SKU (hero). Swap item_id to reuse.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`)
SELECT o.organization_code org, o.designated_org_code net,
       ROUND(MIN(s.projected_available_balance - s.safety_stock),0) worst_gap,
       COUNT(DISTINCT s.date_key) wks
FROM prod_edw.fact.`20_supply_daily` s JOIN latest ON s.process_date=latest.pd
JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON s.inventory_organization_bigint_key=o.inventory_organization_bigint_key
WHERE i.item_id='369722' AND s.plan_name='20 Global Supply Plan'
  AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0
GROUP BY 1,2 ORDER BY worst_gap;
```

**Gotcha logged:** a correlated scalar subquery for cost **fails** on this warehouse (`UNSUPPORTED_CORRELATED_SCALAR_SUBQUERY`); pre-aggregate `series_bigint_key` in the CTE and LEFT JOIN cost — pattern above works.
