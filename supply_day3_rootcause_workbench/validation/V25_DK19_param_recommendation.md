<div align="center">

# V25 (DK-19) · Parameter Recommendation + Proposal Queue — Validation

</div>

**Lead (cross-pollination):** the peer MRO app's core loop is **current-SAP vs recommended SS/ROP/MAX/LT + delta +
working-capital $ → accept/override/no-change → proposal queue**. Hypothesis: MKE can do the same. **Question:
does MKE even run a ROP/MAX min-max policy, and are those parameters stored to compare?**

---

## What MKE actually stores (live)

| parameter | MKE has it? | column |
|---|---|---|
| Safety Stock | ✅ | `20_supply_daily.safety_stock`; `dim_series_ext_vw.safety_stock_managed_flag` (176,732 "Yes") |
| Order min / max (lot sizing) | ✅ | `purchase_/inventory_/sales_minimum_/maximum_order_quantity`, `fixed_lot_multiplier` |
| Lead time | ✅ | `complete_lead_time` |
| **Reorder Point (ROP)** | ❌ | **no ROP column** in `dim_series_ext_vw` or `20_supply_daily` |
| **Maximum stock LEVEL (MAX)** | ❌ | **no max-stock-level column** (only max *order* qty, which is different) |

## 📖 The story the data tells — a fundamental model difference

This is where the peer app **does not transfer cleanly**, and the data says why: **MKE and the peer run different
inventory philosophies.**
- The peer app is a **min-max / ROP-MAX policy** (classic MRO): SAP holds a Reorder Point and a Maximum stock
  level, and their tool recommends better values → the "current-vs-recommended ROP/MAX" comparison is the whole
  product.
- **MKE is projection-based**: the plan computes forward PAB (the verified recursion, V2) against a **safety
  stock** target — there is **no stored ROP or MAX-level** to compare, because MKE doesn't run that policy. The
  only truly tunable parameter is **safety stock** (176,732 series actively managed).

So a faithful MKE version of DK-19 isn't "recommend ROP/MAX" — it's **"recommend safety stock"** (current SS vs a
recommended SS, with the working-capital delta). And that runs **straight into our already-blocked findings**:
statistical SS is blocked (measures B1), `service_level` is a category not a % (B10), the 22-SS-Stat/DOC plans
are empty in fact, and Sarah's reconstruction isn't a live table (Activity 4). **We can show current SS and the
*gap-driven implied* SS, but we cannot yet compute an authoritative "recommended" SS.**

**What IS reusable right now, without a recommendation engine:** the **proposal-queue workflow itself.** The peer
app's accept/override/no-change → queue → implement → audit pattern is exactly our Lakebase `action_request`
plumbing + DK-14's verdict pattern. So MKE can ship the *governance loop* (propose a safety-stock change, route
it, log it, audit it) **now**, and plug a recommendation engine in **later** when SS methodology is unblocked.

## Verdict: 🟡 Partially applicable — workflow YES (now), recommendation engine NO (blocked)

**What works ✅**
- The **proposal-queue governance loop** (accept/override/no-change → queue → audit) maps directly to our
  Lakebase `action_request` + DK-14 — reusable now.
- Current parameters (SS, order min/max, lead time) are all stored and displayable.

**What doesn't ❌ / 🔴 blocked**
- 🔴 **No ROP / MAX-level to compare** — MKE is projection-based, not min-max. The peer's headline comparison
  doesn't map.
- 🔴 **"Recommended SS" is blocked** — statistical SS unavailable (B1/B10), Sarah's reconstruction not live.
  We can show current + implied-from-gap, not an authoritative recommendation.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| No ROP/MAX | MKE plans by forward projection (PAB) against safety stock, not a min-max reorder policy |
| Can't recommend SS | SS method not exposed / statistical inputs empty / reconstruction not live (Activity 4, measures B1/B10) |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Reframe DK-19 for MKE**: it's a **safety-stock** review (+ the working-capital $ of an SS change), not ROP/MAX | product | 🔴 must (scope correction) |
| 2 | **Ship the proposal-queue workflow now** (propose SS change / accept / override / no-change → Lakebase action_request → audit) — reuse existing plumbing; the *governance* is valuable even before a recommender | build | 🟡 should |
| 3 | **Gate the recommendation engine** behind the SS-methodology unblock (Sarah's reconstruction / 22-SS activation) — don't fake a "recommended SS" | analyst | 🔴 must (integrity) |
| 4 | Until then, show **current SS + gap-implied SS + working-capital delta** as *decision support*, clearly labelled "not a model recommendation" | build | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V25 DK-19: stocking parameters MKE stores (READ-ONLY).
SELECT column_name FROM prod_operations.information_schema.columns
WHERE table_schema='edw_extension' AND table_name='dim_series_ext_vw'
  AND lower(column_name) RLIKE 'reorder|rop|max|min|order_point|target_level|days_of_cover|safety'
ORDER BY column_name;
-- confirm no ROP/MAX-level in the supply fact:
SELECT column_name FROM prod_edw.information_schema.columns
WHERE table_schema='fact' AND table_name='20_supply_daily'
  AND lower(column_name) RLIKE 'reorder|rop|max|order_point|target';
-- SS actively managed?
SELECT safety_stock_managed_flag, COUNT(*) n FROM prod_operations.edw_extension.dim_series_ext_vw GROUP BY 1;
```

**Key finding:** MKE is **projection-based, not min-max** — no ROP/MAX to compare. The peer's parameter engine
becomes a **safety-stock** review for MKE, and the *recommendation* half is blocked (SS methodology) — but the
**proposal-queue workflow** is reusable now.
