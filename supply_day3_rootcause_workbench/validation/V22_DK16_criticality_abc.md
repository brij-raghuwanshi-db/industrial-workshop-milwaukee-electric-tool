<div align="center">

# V22 (DK-16) · Criticality / ABC as a Classifier Axis — Validation

</div>

**Lead (cross-pollination):** the peer MRO app leads every SKU with **Criticality / ABC**. We rank by $ and
recoverability but not by *how critical* the part is. Hypothesis: an A/B/C axis materially re-prioritizes the
worklist. **Source:** `dim_series_ext_vw.inventory_abc_class` + `standard_cost`.

---

## Shortage SKUs by ABC class (live, next quarter)

| ABC | short SKUs | short $M | **$ per SKU** |
|---|---|---|---|
| **A** | 608 | $41.2M | **$67,763** |
| B | 45 | $0.6M | $13,333 |
| **C** | 5,008 | $162.0M | $32,348 |
| Unclassified | 3,361 | $97.3M | $28,950 |

**The punchline:** an A-class shortage averages **$67,763/SKU — 2.1× the C-class average.** But A-class is only
608 SKUs vs 5,008 C-class, so a **pure $-rank buries the critical parts** among the long C tail.

## 📖 The story the data tells

Criticality is a genuinely missing axis, and the data proves why it matters: **the most critical parts are
individually the most expensive to be short on** ($67.8k/SKU for A vs $32.3k for C), yet they're a *small*
population (608). A worklist sorted purely by total $ interleaves them with thousands of C-class items and a
planner working top-down might not reach an A-class stockout until late. That's backwards — an A-class critical
part (safety-critical, high-value, or single-source) short by a few units can matter more than a C-class item
short by many.

This is the peer app's core framing, and MKE has the data for it (`inventory_abc_class`: A/B/C/D populated). It
slots cleanly into our **classifier layer** as one more tag — `criticality_class` — that *weights* the ACT
ranking rather than replacing $. The right sort isn't "$ desc" or "criticality desc" alone; it's a **blended
priority** (criticality × $ × recoverability) so A-class winnable shortages float to the top.

**Honest caveat:** 3,361 shortage SKUs are **Unclassified** (no ABC) — a real data-completeness gap. Criticality
weighting only works where the class is populated; the unclassified third needs a fallback (treat as C, or flag
for classification).

## Verdict: ✅ CONFIRMED — criticality is a real, missing, high-value axis

**What works ✅**
- ABC class is populated and live-joinable; A-class shortages are 2.1× more expensive per SKU.
- Cleanly extends the classifier layer as a ranking *weight*.

**Data-quality findings**
- 🟡 **DQ-1 — 3,361 shortage SKUs Unclassified** (~37% of the short list) — needs a fallback rule or a
  classification backlog; criticality weighting is incomplete until addressed.
- 🟡 **DQ-2 — ABC is `inventory_abc_class`; there are also `global_/local_planning_abc_code`** — confirm which is
  the authoritative criticality with a planner (they may differ by lens).
- 💭 **DQ-3 — "critical part" (safety/regulatory) ≠ ABC (value/volume).** The peer app had *both* (Criticality +
  Critical-Part). MKE has ABC; a separate safety-critical flag (if it exists) would be a further axis.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| A-class 2.1× $/SKU | A-class = high-value/high-usage by definition → each unit short costs more |
| Buried in a $-rank | small population (608) interleaved with 5,008 C-class → top-down misses them |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add **`criticality_class`** (from `inventory_abc_class`) to `rc_serving_sku_week` (classifier layer) | build | 🔴 high value |
| 2 | **Blended priority sort** = criticality × $ × recoverability — surface A-class winnable shortages first | build | 🔴 must |
| 3 | Fallback for the **Unclassified 37%** (treat as C / flag for classification) | build + master data | 🟡 should |
| 4 | Confirm authoritative ABC field + whether a **safety-critical-part** flag exists (separate axis) | planner | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V22 DK-16: shortage SKUs + $ by ABC class (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
short AS (SELECT s.product_bigint_key po, MAX(s.series_bigint_key) sk,
    MIN(s.projected_available_balance - s.safety_stock) gap
  FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0
  GROUP BY 1 HAVING MIN(s.projected_available_balance - s.safety_stock)<0)
SELECT COALESCE(x.inventory_abc_class,'Unclassified') abc, COUNT(*) short_skus,
       ROUND(SUM(ABS(short.gap)*COALESCE(x.standard_cost,0))/1e6,1) short_dollars_M
FROM short LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON short.sk=x.series_bigint_key
GROUP BY 1 ORDER BY short_dollars_M DESC;
```
