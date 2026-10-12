<div align="center">

# V24 (DK-18) · Demand-Class: Intermittent vs Smooth — Validation

</div>

**Lead (cross-pollination):** the peer MRO app tags **Demand-Class: Intermittent**. This matters because our
verified formulae (safety stock, % consumption, forecast) assume *smooth-ish* demand — but intermittent SKUs
break that. Hypothesis: a meaningful share of MKE SKUs are intermittent → a data-quality guard on our own math.
**Source:** `10_demand_daily.shipments_history` — ADI proxy (share of periods with demand).

---

## Demand-class distribution (ACC plan, items with ≥6 periods)

| demand class | items | share |
|---|---|---|
| Smooth (demand >70% of periods) | 3,824 | 49% |
| **Intermittent** (<34% of periods) | **1,471** | **19%** |
| Erratic (34–70%) | 342 | 4% |
| No demand at all | 2,062 | 27% |

→ **~24% of items are intermittent/erratic** — sporadic demand where Normal-based statistics are unreliable.
Plus 27% with no demand (ties to V23 dormant / never-shipped).

## 📖 The story the data tells

The peer app's demand-class tag isn't cosmetic — it's a **statistical warning label**, and MKE needs it.
Roughly **a fifth of items are intermittent** (demand in fewer than a third of periods), and for those, the tools
we validated as *correct* for smooth demand become *misleading*:
- **% consumption** (V3): "actual ÷ forecast" on a SKU that ships once a quarter swings wildly — a single order
  reads as a 300% "over-consumption" that means nothing.
- **Safety stock** (measures §5B): the ASCM `z·σ` formula assumes ~Normal demand-during-lead-time; for
  intermittent demand it over/under-states — Croston / fill-rate methods apply instead.
- **Demand-surprise / bias**: noisy by construction on sporadic SKUs.

So DK-18 is less a new *feature* and more a **guard on our existing measures**: on intermittent SKUs, the tool
should **flag that the standard math is unreliable** and soften the confidence, rather than present a confident
wrong number. And it explains part of V3's chronic-under-forecast finding — some of those "misses" are
intermittent-demand noise, not a real forecasting failure. Combined with the 27% no-demand (dormant, V23), a
large slice of the catalog simply doesn't behave the way the smooth-demand formulae assume.

## Verdict: ✅ CONFIRMED — ~24% intermittent; a real integrity guard on our own formulae

**What works ✅**
- ADI-proxy classification is computable and clean; intermittent/erratic/smooth/no-demand segments are distinct.

**Data-quality findings**
- 🟡 **DQ-1 — this is a *proxy* ADI** (share of periods with demand), not the full ADI/CV² Syntetos-Boylan
  quadrant. Good enough to flag; refine with CV² for lumpy-vs-intermittent if pursued.
- 🟡 **DQ-2 — tested on one plan (ACC)**; other product lines (tools) may differ — run per plan.
- 🟢 **DQ-3 — no join issues**; pure demand-history aggregation.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| 24% intermittent | spare/accessory/long-tail SKUs sell sporadically — inherent to a broad catalog |
| Explains some V3 "misses" | intermittent demand makes % consumption/bias noisy → false "chronic under-forecast" |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **`demand_class`** (smooth/erratic/intermittent/no-demand) to the classifier layer via the ADI proxy | build | 🟡 should (integrity) |
| 2 | On intermittent SKUs, **flag standard measures as low-confidence** (SS, % consumption, bias) — don't present a confident wrong number | build | 🔴 must (trust) |
| 3 | Route intermittent SKUs to **fill-rate / Croston** thinking rather than Normal-SS (later, with the recommendation engine DK-19) | analyst | 🟡 could |
| 4 | Cross-check: how much of V3's "chronic under-forecast" is intermittent noise vs real bias | analyst | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V24 DK-18: intermittent vs smooth via ADI proxy (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`),
perItem AS (SELECT dm.product_bigint_key it, COUNT(DISTINCT dm.date_key) periods,
    SUM(CASE WHEN dm.shipments_history>0 THEN 1 ELSE 0 END) periods_with_demand
  FROM prod_edw.fact.`10_demand_daily` dm JOIN latest ON dm.process_date=pd
  WHERE dm.plan_name='10 ACC Demand Plan' GROUP BY 1 HAVING COUNT(DISTINCT dm.date_key)>=6)
SELECT CASE WHEN periods_with_demand=0 THEN 'no demand'
            WHEN periods_with_demand/periods < 0.34 THEN 'INTERMITTENT (<34% of periods)'
            WHEN periods_with_demand/periods < 0.7 THEN 'erratic (34-70%)'
            ELSE 'smooth (>70%)' END demand_class,
       COUNT(*) items FROM perItem GROUP BY 1 ORDER BY items DESC;
```
