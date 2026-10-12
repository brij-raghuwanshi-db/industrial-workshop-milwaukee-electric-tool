<div align="center">

# V16 (N2) · Over-forecast → Excess Causal Link — Validation

</div>

**Lead (from V14/V8):** most customers are under-forecast (→ shortage), but some (CAN REGIONAL +1.25M,
CONST_IND +361k) are chronically *over*-forecast. Hypothesis: over-forecast is the **demand cause of the $452M
excess** — the mirror of under-forecast→shortage. Can we prove it in the data?

---

## What the data shows

| probe | result |
|---|---|
| Over-forecast customers (planner_bias > +50k) | **5** |
| SKUs those customers drive (any demand) | 40,327 |
| …of those, SKUs in excess (>3× SS) | **15,275** |
| **Baseline excess rate — ALL SKUs** | **62.5%** (20,759 of 33,191) |

## 📖 The story the data tells — and its honest limit

The *concept* is sound and the direction is right: over-forecasting a customer plans supply that never sells →
inventory piles up. And it's directionally visible — the over-forecast customers' SKUs do land heavily in the
excess pile (15,275).

**But the data will not let me claim a clean causal link at SKU grain, for two real reasons:**
1. **Excess is pervasive** — **62.5% of ALL SKUs are in excess** (>3× SS), so "an over-forecast customer's SKU is
   in excess" is barely above the base rate. The overlap isn't distinctive.
2. **SKUs are shared across many customers** — only 5 customers clear the +50k bias bar, yet their SKUs span
   40,327 (DG5 customers share the catalog broadly). A SKU's excess can't be attributed to one customer's bias
   without **customer-level demand allocation** (which SKU×customer demand drove the over-plan).

So N2 is a **plausible mechanism the SKU-grain join can't isolate.** To prove it you'd need to decompose excess
*by the customer-level forecast that created it* — data that exists (`10_demand_daily` is customer-grain) but
requires a proper allocation model, not a membership join.

**The more useful reframing the probe surfaced:** the headline isn't "over-forecast causes excess" — it's that
**excess is systemic (62.5%), not customer-specific.** That's a bigger finding than N2: the $452M overstock is
broad-based, which points at *planning-policy* causes (SS targets, MOQ over-buy, forward-DOC inflation — the
DK-12 refresh) more than a few over-forecasting customers.

## Verdict: 🟡 Plausible, not provable at SKU grain — and it reframed the excess story

**What's true:** the mechanism is sound; over-forecast customers' SKUs are heavily in excess.
**What's not provable here:** clean attribution — excess is too pervasive (62.5%) and SKUs too shared to isolate
one customer's bias as *the* cause.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Can't attribute excess to over-forecast customers | SKU shared across customers + excess is baseline-pervasive → membership join ≠ causation |
| Excess is 62.5% systemic | broad planning-policy drivers (SS/MOQ/forward-DOC), not a handful of customers |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Don't ship N2 as a causal claim** — the SKU-grain evidence doesn't support it | — | 🔴 must (integrity) |
| 2 | If pursued, build **customer-level excess attribution** (allocate excess to the SKU×customer forecast that created it) — needs a real model, not a join | build (later) | 🟡 could |
| 3 | **Pivot to the bigger finding:** excess is **62.5% systemic** → investigate planning-policy causes (SS realism, MOQ over-buy, DK-12 forward-DOC inflation) as the excess root, not customers | planner/analyst | 🔴 must |
| 4 | Keep V8's simpler, provable action: route **positive-bias customers to a demand re-baseline** (that IS clean) — just don't claim it explains the excess dollars | planner | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V16 N2: over-forecast customers' SKUs in excess (READ-ONLY) — overlap, not attribution.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
bias AS (SELECT dg5_customer_bigint_key c, SUM(planner_bias) pb FROM prod_operations.demand.fact_forecast_accuracy GROUP BY 1),
over AS (SELECT c FROM bias WHERE pb>50000),
demand_of_over AS (SELECT DISTINCT dm.product_bigint_key po FROM prod_edw.fact.`10_demand_daily` dm JOIN over ON dm.dg5_customer_bigint_key=over.c),
excess AS (SELECT DISTINCT product_bigint_key po FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan' AND date_key BETWEEN 20260907 AND 20261207
    AND safety_stock>0 AND projected_available_balance > safety_stock*3)
SELECT (SELECT COUNT(*) FROM over) over_forecast_customers,
       (SELECT COUNT(*) FROM demand_of_over) skus_they_drive,
       COUNT(*) those_skus_in_excess
FROM demand_of_over d JOIN excess e ON d.po=e.po;
```
```sql
-- V16 N2: baseline excess rate (the reframe) — 62.5% of all SKUs are in excess (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
allskus AS (SELECT DISTINCT product_bigint_key po FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan' AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0),
excess AS (SELECT DISTINCT product_bigint_key po FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan' AND date_key BETWEEN 20260907 AND 20261207
    AND safety_stock>0 AND projected_available_balance>safety_stock*3)
SELECT COUNT(*) all_skus, (SELECT COUNT(*) FROM excess) excess_skus,
       ROUND((SELECT COUNT(*) FROM excess)/COUNT(*)*100,1) baseline_excess_rate FROM allskus;
```

**Lesson logged:** a **membership join is not causation** — with excess at a 62.5% base rate and SKUs shared
across customers, "over-forecast customer's SKU is in excess" proves nothing. This is the discipline that keeps
the tool honest: the probe *disproved* a clean causal claim and surfaced the bigger truth (excess is systemic).
