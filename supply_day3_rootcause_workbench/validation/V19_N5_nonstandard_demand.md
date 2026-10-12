<div align="center">

# V19 (N5) · Non-Standard Demand Streams (NO CHARGE / OTHER NA) — Validation

</div>

**Lead (from V3):** "NO CHARGE" (+186%) and "OTHER NA" (+204%) ranked among the worst-consumed customers — but
they're catch-all / non-standard streams (samples, no-charge, unclassified). Hypothesis: they **pollute the
demand-surprise signal**.

---

## What the data shows (live)

| metric | value |
|---|---|
| Non-standard actual demand (NO CHARGE / OTHER NA / sample-type) | **11,526,035 units** |
| Total actual demand | 1,061,799,052 units |
| **Non-standard share of total** | **1.1%** |

## 📖 The story the data tells

The nuance matters: these streams are **loud in the *ranking* but tiny in *volume*.** They top the consumption-%
board (V3) because they're chronically under-forecast on a percentage basis — but they're only **1.1% of total
demand.** So the honest read is: they **distort an *unweighted* bias/consumption ranking** (a planner sorting by
"% over forecast" sees NO CHARGE at the top and wastes attention), but they **do not materially move the
volume/$ picture.** It's a *display* problem, not a data-integrity problem — and the fix is simple: exclude or
tag them, and rank by weighted impact ($/units), not raw %.

## Verdict: 🟡 Minor — a ranking-hygiene fix, not a material distortion

**What's true:** non-standard streams over-rank on unweighted %.
**What's not:** they're only 1.1% of volume — no material pollution of the aggregate.

## 🔍 Root cause

| Finding | Root cause |
|---|---|
| Top of the % ranking, tiny in volume | unweighted consumption-% treats a 200%-of-tiny-forecast the same as 200%-of-huge → small streams float up |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Rank the demand-bias/consumption board by weighted impact ($ or units)**, not raw % — keeps NO CHARGE/OTHER NA from crowding out real customers | build | 🟡 should |
| 2 | **Tag/segregate** non-standard DG5 streams (no-charge, samples, OTHER) so a planner can exclude them | build | 🟡 should |
| 3 | Don't over-invest — at 1.1% of volume this is hygiene, not a lens | — | 💭 note |

---

## ✅ Logged successful query

```sql
-- V19 N5: non-standard demand share of total (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`)
SELECT ROUND(SUM(CASE WHEN c.mkedg5 IN ('NO CHARGE','OTHER NA','OTHER','SAMPLE','SAMPLES') THEN dm.shipments_history ELSE 0 END),0) nonstd_actual,
       ROUND(SUM(dm.shipments_history),0) total_actual,
       ROUND(SUM(CASE WHEN c.mkedg5 IN ('NO CHARGE','OTHER NA','OTHER','SAMPLE','SAMPLES') THEN dm.shipments_history ELSE 0 END)/NULLIF(SUM(dm.shipments_history),0)*100,1) pct_nonstandard
FROM prod_edw.fact.`10_demand_daily` dm JOIN latest ON dm.process_date=pd
JOIN prod_edw.dimension.dg5_customer_scd1 c ON dm.dg5_customer_bigint_key=c.dg5_customer_bigint_key
WHERE dm.shipments_history>0;
```
