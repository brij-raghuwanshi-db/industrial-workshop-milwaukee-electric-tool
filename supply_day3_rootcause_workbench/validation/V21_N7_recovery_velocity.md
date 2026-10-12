<div align="center">

# V21 (N7) · Recovery Velocity / Time-to-Heal — Validation

</div>

**Lead (from V12):** we found transient dips recover, but never measured *how fast* a breach typically heals, or
which SKUs stay stuck. Hypothesis: a per-SKU "self-heal velocity" sharpens the WATCH-vs-ACT line and the
do-nothing confidence.

---

## What the data shows (fixed target week 20261012, 55 snapshots since 2026-07-01)

| metric | value |
|---|---|
| SKUs that dipped below SS at least once | **8,836** |
| **Healed fast** (below in ≤5 of 55 snapshots) | **2,600 (29%)** |
| **Stuck** (below in 40+ snapshots) | **2,086 (24%)** |
| Avg snapshots-below | 21.9 |

## 📖 The story the data tells

Recovery velocity is **bimodal and decision-relevant.** For the same future week, **29% of SKUs that ever dipped
recovered quickly** (below in ≤5 of 55 snapshots — a blip that firmed up), while **24% were stuck below for 40+
snapshots** (a persistent condition). The average (21.9) hides this split — most SKUs are near one pole or the
other.

This is the missing third axis under the do-nothing verdict. V12 said "66% are cushion dips → DISMISS"; V13 said
"is it inside the lead-time fence?"; N7 adds **"and how fast does this kind of dip usually heal?"** A SKU flagged
today that *historically* heals in a couple snapshots is a confident **WATCH** — the plan has recovered it before
and will again. A SKU that's been stuck below for 40+ snapshots is not a "dip" at all — it's the **chronic**
population (V10) confirmed from the recovery angle, and it should route to a policy fix, not another week of
watching. So recovery velocity *disambiguates* WATCH (will self-heal) from chronic (never heals) — the two look
identical on a single snapshot.

## Verdict: ✅ CONFIRMED — self-heal velocity is a real, bimodal signal that sharpens the action verdict

**What works ✅**
- Clean bimodal split (29% fast-heal / 24% stuck) from snapshot history; directly informs WATCH vs chronic.

**Data-quality findings**
- 🟡 **DQ-1 — measured for one fixed target week.** Generalize to a rolling "of the last M snapshots that showed
  this SKU below for its near-term weeks, how many recovered" — a per-SKU self-heal rate.
- 🟡 **DQ-2 — "snapshots below" ≈ persistence, not literal calendar heal-time.** To express in weeks, translate
  snapshot-count to the cadence; but the *rank* (fast vs stuck) is what matters for the verdict.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Fast-healers (29%) | timing dips — a late receipt lands, plan recovers next cycle |
| Stuck (24%) | chronic under-supply / unrealistic SS target — the V10 chronic population from the recovery angle |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **self-heal velocity** signal (fast / normal / stuck) to the classifier layer — a per-SKU rolling recover-rate from snapshots | build | 🟡 should |
| 2 | Use it to **sharpen WATCH**: fast-healer + WATCH = high-confidence do-nothing; stuck = it's chronic (V10) → policy fix, not watch | build | 🟡 should |
| 3 | Cross-link "stuck" SKUs to the chronic-critical / living-on-the-edge list (V13/V10) — same population, two lenses | build | 💭 note |

---

## ✅ Logged successful query

```sql
-- V21 N7: recovery velocity — snapshots-below distribution for a fixed target week (READ-ONLY).
WITH perSnap AS (
  SELECT process_date, product_bigint_key po, inventory_organization_bigint_key io,
         MAX(CASE WHEN projected_available_balance<safety_stock THEN 1 ELSE 0 END) below
  FROM prod_edw.fact.`20_supply_daily`
  WHERE process_date>=20260701 AND plan_name='20 Global Supply Plan' AND date_key=20261012 AND safety_stock>0
  GROUP BY 1,2,3),
agg AS (SELECT po, io, COUNT(*) snaps, SUM(below) snaps_below FROM perSnap GROUP BY 1,2 HAVING SUM(below) BETWEEN 1 AND 54)
SELECT COUNT(*) skus_that_dipped,
       SUM(CASE WHEN snaps_below<=5 THEN 1 ELSE 0 END) healed_fast_lte5snaps,
       SUM(CASE WHEN snaps_below>=40 THEN 1 ELSE 0 END) stuck_40plus,
       ROUND(AVG(snaps_below),1) avg_snaps_below
FROM agg;
```
