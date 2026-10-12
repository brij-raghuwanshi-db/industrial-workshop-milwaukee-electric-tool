<div align="center">

# V3 · Demand Surprise / Consumption + Priors — Validation

</div>

**Claims (design):** consumption % (actual vs forecast) by DG5 customer, split promo/base, at monthly grain;
priors matrix = forecast evolution across vintages (late 1–6). **Measures:** `consumption% = actual ÷ forecast`,
demand type split, late-N via `process_date` self-join. **Source:** `10_demand_daily` (+ `dg5_customer_scd1`),
plan `10 ACC Demand Plan`.

---

## Test 1 — Consumption % by customer (10 real DG5 customers, `10 ACC`)

| # | customer (mkedg5) | actual (ship hist) | forecast (late-3) | baseline | promo | consumption % |
|---|---|---|---|---|---|---|
| 1 | TTI NZ | 67,442 | 23,261 | 67,442 | — | **290%** |
| 2 | PCS | 541,265 | 257,964 | 411,315 | −592 | 210% |
| 3 | OTHER NA | 760,129 | 371,871 | 759,592 | — | 204% |
| 4 | NO CHARGE | 430,637 | 231,336 | 338,395 | — | 186% |
| 5 | OEM | 15,600 | 8,609 | 15,600 | — | 181% |
| 6 | LANDSCAPING | 28,525 | 15,809 | 27,182 | −100 | 180% |
| 7 | ISN | 96,487 | 59,968 | 73,581 | −356 | 161% |
| 8 | STH CONE | 289,364 | 181,179 | 244,104 | — | 160% |
| 9 | CAM | 1,207,304 | 790,552 | 1,095,656 | — | 153% |
| 10 | SIS COMP | 2,491,692 | 1,710,144 | 2,491,380 | — | 146% |

## Test 2 — Priors / forecast evolution (CAM, Nov-2026 target, across vintages)

| snapshot vintage | forecast for Nov-2026 |
|---|---|
| 2026-08-25 → 08-31 | **94,703** |
| 2026-09-01 → 09-02 | **88,326** |

→ Forecast evolution is reconstructable: CAM's Nov forecast was cut ~6,400 units between late-Aug and early-Sep.

## 📖 The story the data tells

The demand data tells a blunt, consistent story: **this book is chronically under-forecast.** All ten of the
top-consumption customers on accessories shipped *more* than plan — from +46% to +190% — and there isn't a
single over-forecast customer near the top. That's not random error; a forecast that's *always* low across the
customer base is a **systematic bias**, and it's the upstream reason the supply team keeps fighting shortages
(V1). The demand story and the supply story are the same story told from two ends.

Two customers reframe it further. **"NO CHARGE"** and **"OTHER NA"** are near the top — these look like
catch-all / non-standard demand streams, and their being chronically under-forecast suggests the *misses
concentrate in the demand the planners model least carefully*, not the marquee customers. And **promo is
essentially absent on accessories** (all null or small negatives) — so for this product line the "promo vs base"
lever the transcript emphasized barely applies; it's a **base-demand** story here. That's a useful scoping fact:
the promo/base split matters for some plans (tools) far more than others (accessories).

The priors test tells a quieter story: forecasts *do* move (CAM's Nov cut by ~6.4k in a week), so the
"how did the forecast evolve" question is answerable — **but only if you aggregate the target month**, because
any single weekly `date_key` is too sparse to trace across vintages.

## Verdict: 🟡 works — with two definitional/DQ caveats that must be resolved before display

**What works ✅**
- Consumption % computes cleanly for all 10 customers; DG5 join is clean; the chronic under-forecast pattern is real and stark.
- Baseline is well-populated; the actual-vs-forecast comparison is sound.
- Priors evolution works via the `process_date` self-join **at month grain**.

**Data-quality / definition findings**
- 🔴 **DQ-1 — "demand surprise" is genuinely ambiguous, confirmed by the data.** This run's `actual÷forecast`
  gives CAM **153%**; the earlier bias run `(actual−forecast)÷forecast` gave the same customers as **+60–190%**.
  *Same data, different metric, very different number.* The transcript's "demand surprise means different things
  to different people" is a live risk — **one definition must be pinned and labelled in the UI** or two planners
  will read the same screen differently.
- 🟡 **DQ-2 — promo is near-empty on accessories.** `planner_promo` is null or small-negative for 9/10 — the
  promo/base split is *available* but **barely populated on `10 ACC`**. It likely matters on `10 TOL` (tools);
  validate per plan before making promo a headline dimension everywhere.
- 🔴 **DQ-3 — priors self-join fails on a single `date_key`.** Matching one weekly bucket across vintages returns
  **empty** (sparsity); must aggregate the **target month** (`date_key BETWEEN` first-of-month … end). This is a
  build rule, not a data defect — but a naïve implementation would show a blank priors matrix.
- 🟡 **DQ-4 — which plan(s)?** These are `10 ACC` only. A SKU/customer spans multiple product-line plans; the UI
  must either scope to the relevant plan or union them — and label which.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Every top customer > 100% (DQ-story) | systematic **under-forecasting** — the forecast baseline is set low relative to realized demand |
| Consumption number ambiguous (DQ-1) | two legitimate formulas (ratio vs signed error) both called "demand surprise" — no single governed definition |
| Promo empty (DQ-2) | accessories are base-demand-driven; promo is a tools/seasonal phenomenon → column sparse by product line |
| Priors blank on one week (DQ-3) | demand is planned **monthly**; a single weekly `date_key` is too sparse across daily vintages |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Pin ONE governed "demand surprise" definition** (ratio vs signed-error) + show the formula in the UI (DQ-1) | planner + Chris | 🔴 must (trust) |
| 2 | **Priors = aggregate the target month** across vintages; never single-`date_key` match (DQ-3) | build | 🔴 must |
| 3 | Make **promo/base a per-plan** dimension — headline it on tools, de-emphasize on accessories (DQ-2) | build | 🟡 should |
| 4 | Prefer the **governed `fact_forecast_accuracy`** (DK-7, V8) for bias; use `10_demand_daily` empirical only for lag-flex | build | 🟡 should |
| 5 | Always **label the plan(s)** in scope on the demand view (DQ-4) | build | 🟡 should |
| 6 | Route the chronic under-forecast customers to the **demand-team handoff** with this evidence (Gap 7) | planner→demand | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V3 Test 1: consumption % + promo/base by customer (READ-ONLY). Plan = 10 ACC.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`)
SELECT c.mkedg5,
       ROUND(SUM(dm.shipments_history),0) actual,
       ROUND(SUM(dm.final_demand_forecast_3_month_ago),0) fcst_late3,
       ROUND(SUM(dm.planner_baseline),0) baseline,
       ROUND(SUM(dm.planner_promo),0) promo,
       ROUND(SUM(dm.shipments_history)/NULLIF(SUM(dm.final_demand_forecast_3_month_ago),0)*100,0) consumption_pct
FROM prod_edw.fact.`10_demand_daily` dm JOIN latest ON dm.process_date=pd
JOIN prod_edw.dimension.dg5_customer_scd1 c ON dm.dg5_customer_bigint_key=c.dg5_customer_bigint_key
WHERE dm.plan_name='10 ACC Demand Plan' AND dm.shipments_history>0 AND dm.final_demand_forecast_3_month_ago>0
GROUP BY c.mkedg5 HAVING SUM(dm.final_demand_forecast_3_month_ago)>2000
ORDER BY consumption_pct DESC LIMIT 10;
```
```sql
-- V3 Test 2: priors / forecast evolution across vintages (MONTH-aggregated — the working pattern).
SELECT dm.process_date AS vintage, COUNT(*) rows, ROUND(SUM(dm.working_final_forecast),0) forecast_for_month
FROM prod_edw.fact.`10_demand_daily` dm
JOIN prod_edw.dimension.dg5_customer_scd1 c ON dm.dg5_customer_bigint_key=c.dg5_customer_bigint_key
WHERE dm.plan_name='10 ACC Demand Plan' AND c.mkedg5='CAM'
  AND dm.date_key BETWEEN 20261101 AND 20261130   -- target MONTH, not a single week
GROUP BY dm.process_date ORDER BY dm.process_date DESC LIMIT 8;
```

**Gotcha logged:** matching a **single weekly `date_key`** across `process_date` vintages returns EMPTY (demand
sparsity) — aggregate the **target month** instead. This is the difference between a populated and a blank priors
matrix.
