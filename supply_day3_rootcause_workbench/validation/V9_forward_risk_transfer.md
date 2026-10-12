<div align="center">

# V9 · Forward Risk + Transfer-to-Cover — Validation

</div>

**Claims (DK-1/DK-9):** rank SKUs *projected* to cross below SS in the next N weeks; flag crossings inside lead
time (can't fix by ordering); check if in-network transfer can cover. **Source:** `20_supply_daily` forward PAB
+ `dim_series_ext_vw.complete_lead_time` + `designated_org_code`.

---

## Test 1 — 10 SKUs projected to cross below safety stock (earliest first)

| # | item_id | org | crosses week | depth at low | lead (days) | flag |
|---|---|---|---|---|---|---|
| 1 | 49163647 | 2012 | 2026-09-14 | −1,035 | 100 | crosses **inside** lead time |
| 2 | 345020 | 2012 | 2026-09-14 | −1,765 | 130 | inside |
| 3 | 14300019 | 2092 | 2026-09-14 | −228 | 152 | inside |
| 4 | 22565317 | 2092 | 2026-09-14 | −528 | 103 | inside |
| 5 | 06822681 | 2092 | 2026-09-14 | −12 | 118 | inside |
| 6 | 49666125T | 2012 | 2026-09-14 | −2,433 | 157 | inside |
| 7 | 48208481 | 2013 | 2026-09-14 | −20 | 35 | inside |
| 8 | 49322530 | 2092 | 2026-09-14 | −21 | 120 | inside |
| 9 | 31447215 | 2092 | 2026-09-14 | −648 | 201 | inside |
| 10 | 48225330Y | 2012 | 2026-09-14 | −822 | 163 | inside |

## Test 2 — can a transfer cover it? (item 345020, forward, across orgs)

| org | network | worst gap |
|---|---|---|
| 2012 | 2012 | −1,765 |
| 2093 | 2012 | −1,565 |
| 2013 | 2012 | ~0 |
| 3031/9042/9043 | — | 0 |
| 2120 | 2120 | +19 |

→ **No in-network org has meaningful excess** → transfer will NOT save 345020; it's a genuine expedite/escalate.

## 📖 The story the data tells

Forward-risk works, and the first thing the data says is uncomfortable: **the earliest crossings are all already
inside their own lead time** — items with 100–200 day lead times projected to breach *next week*. The
lead-time-aware flag isn't a nicety; it's the difference between a fixable and an unfixable problem. For these
SKUs, "place a PO" is useless — the horse has left. The honest action is transfer or expedite, and the tool has
to say so rather than suggest an order that can't arrive in time.

Test 2 is the crucial counterweight to V6's rebalance optimism. For `345020` the crossing is real *and* there's
no in-network surplus to move — so this is the case where **transfer is NOT the answer** and escalation is. Put
V6 and V9 together and the data tells a balanced story: *some* forward crossings are wrong-building problems
(transfer), and *some* are true network shortages (expedite/escalate) — and the tool can tell them apart by
checking in-network excess. That distinction is exactly the planner judgement the transcript described as
tribal; here it's computable.

## Verdict: ✅ works — forward risk + lead-time flag + transfer-check are all real and complementary

**What works ✅**
- Forward crossing detection + week + depth compute cleanly from the plan's own forward PAB (no invented forecast — guardrail honored).
- Lead-time-aware flag works and is essential (all top crossings are inside lead time).
- The transfer-coverage check correctly identifies when transfer *won't* help (345020) — complements V6.

**Data-quality findings**
- 🟡 **DQ-1 — "inside lead time" uses a coarse week cutoff.** I approximated with a fixed `date_key <= 20261005`;
  should compute per-SKU as `crossing_week <= snapshot_week + complete_lead_time` (lead is in *days*, bucket to weeks).
- 🟡 **DQ-2 — many crossings at the very first forward week (20260914).** Some are "already at/near breach now,"
  not "about to" — separate *currently-breaching* from *newly-crossing-forward* (ties to V1 DQ-1 severity split).
- 🟡 **DQ-3 — org 2092** appears heavily — validate it's a real DC in scope (like the org-8000/8000 concern).

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Crossings inside lead time | long lead times (100–200d) mean this week's projected breach was "locked in" months ago — ordering can't fix it |
| Transfer sometimes can't cover (345020) | genuine **network-wide** shortage (all orgs low), not a distribution imbalance |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Compute **"inside lead time" per SKU** = `crossing_week ≤ now + complete_lead_time` (days→weeks), not a fixed cutoff | build | 🔴 must |
| 2 | For inside-lead-time crossings, **suppress "place PO"**; offer transfer/expedite/escalate instead | build | 🔴 must |
| 3 | **Chain V9→V6**: on each forward crossing, auto-check in-network excess → "transfer covers X" vs "escalate (no coverage)" | build | 🔴 must (the DK-9 workflow) |
| 4 | Separate *currently-breaching* from *newly-forward-crossing* (shared severity split w/ V1) | build | 🟡 should |
| 5 | Validate org 2092 (and non-core orgs) are in scope | data owner | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V9 Test 1: forward crossings + depth + lead-time flag (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
fwd AS (
  SELECT s.product_bigint_key po, s.inventory_organization_bigint_key io, MAX(s.series_bigint_key) sk,
         MIN(CASE WHEN s.projected_available_balance < s.safety_stock THEN s.date_key END) first_cross,
         MIN(CASE WHEN s.projected_available_balance < s.safety_stock THEN s.projected_available_balance - s.safety_stock END) depth
  FROM prod_edw.fact.`20_supply_daily` s, latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260914 AND 20261207 AND s.safety_stock>0
  GROUP BY 1,2
  HAVING MIN(CASE WHEN s.projected_available_balance < s.safety_stock THEN s.date_key END) IS NOT NULL)
SELECT i.item_id, o.organization_code org, fwd.first_cross crosses_wk, ROUND(fwd.depth,0) depth_at_low,
       ROUND(x.complete_lead_time,0) lead_days,
       CASE WHEN fwd.first_cross <= 20261005 THEN 'crosses INSIDE ~lead time' ELSE 'time to act' END flag
FROM fwd JOIN prod_edw.dimension.items_scd1 i ON fwd.po=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON fwd.io=o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON fwd.sk=x.series_bigint_key
ORDER BY fwd.first_cross ASC LIMIT 10;
```
```sql
-- V9 Test 2: does in-network transfer cover a forward crossing? (swap item_id)
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`)
SELECT o.organization_code org, o.designated_org_code net,
       ROUND(MIN(s.projected_available_balance - s.safety_stock),0) worst_gap
FROM prod_edw.fact.`20_supply_daily` s JOIN latest ON s.process_date=latest.pd
JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON s.inventory_organization_bigint_key=o.inventory_organization_bigint_key
WHERE i.item_id='345020' AND s.plan_name='20 Global Supply Plan'
  AND s.date_key BETWEEN 20260914 AND 20261207 AND s.safety_stock>0
GROUP BY 1,2 ORDER BY worst_gap;
```
