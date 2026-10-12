<div align="center">

# V10 · Plan Nervousness + SS-Refresh Trap + Chronic — Validation

</div>

**Claims (S3/DK-12/G5):** flag SKUs whose target *thrashes* across snapshots (nervousness); detect the SS-refresh
decision trap (DK-12, validated in V2); separate **chronic** (perpetually short) from **acute** (one-off).
**Source:** `20_supply_daily` snapshot self-joins.

---

## Test — Chronic detection (% of snapshots below SS for a fixed target week)

10 SKUs, target week 20261012, across 55 snapshots since 2026-07-01:

| # | item_id | org | snapshots | snaps below SS | % chronic |
|---|---|---|---|---|---|
| 1 | 45343750T | 2012 | 55 | 55 | **100%** |
| 2 | 48353701C | 2012 | 55 | 55 | 100% |
| 3 | E10548 | 2012 | 55 | 55 | 100% |
| 4 | 51162654X | 1080 | 55 | 55 | 100% |
| 5 | 51162656MX | 1080 | 55 | 55 | 100% |
| 6 | 48892218T | 2012 | 55 | 55 | 100% |
| 7 | 45349086T | 2012 | 55 | 55 | 100% |
| 8 | 267220Z | 2012 | 55 | 55 | 100% |
| 9 | 48229200 | 2012 | 55 | 55 | 100% |
| 10 | 48228903F | 2012 | 55 | 55 | 100% |

→ These SKUs have been below safety stock in **every one of 55 snapshots** for the same target week — perpetual,
not transient. (SS-refresh trap + nervousness magnitudes already validated live in V2 and the DK-12 detail:
demand ~+220% / SS target ~+17.6% coupled; ~1.3% of series thrash 3+ times.)

## 📖 The story the data tells

This is the story that reframes half the workbench: **some shortages are events, and some are conditions.** The
chronic test finds SKUs that have been under safety stock *100% of the time across 55 snapshots* — these aren't
"how did we get here?" incidents, they're **steady states.** A planner fire-fighting one of these weekly is
running the same play against a structural problem: the safety-stock target may simply be set higher than the
supply chain can ever hold, or the item is chronically under-sourced. The right action isn't an expedite — it's
"raise SS realism / re-source / accept the risk," a **fix-the-system** conversation, not a fire drill.

Combine with V2's SS-refresh finding and the nervousness data, and the data is telling us the plan has three
distinct temporal personalities that today all look the same on a shortage screen: **acute** (crossed this week —
act now), **chronic** (always short — fix the system), and **nervous** (target thrashing — *don't* act, it'll
revert). Treating all three as "you're short, go expedite" is how planners burn time on problems that either
can't be fixed by expediting or shouldn't be acted on at all. Separating them is arguably the single biggest
*time-saving* lever in the tool — it tells the planner not just what's wrong, but **what kind of wrong**, which
dictates whether to act, escalate, or ignore.

## Verdict: ✅ chronic detection works · ✅ SS-refresh & nervousness validated (V2/DK-12) — all ready

**What works ✅**
- Chronic = % of snapshots below SS for a fixed target week: clean, decisive (100% cases are unambiguous).
- Nervousness (target thrash) and SS-refresh coupling proven live earlier (V2, DK-12) — consistent.
- 55-snapshot depth since July is ample for a trailing chronic window.

**Data-quality findings**
- 🟡 **DQ-1 — chronic here is "always below" for one fixed week.** Generalize to a **trailing window across
  target weeks** ("below in N of last M snapshots") so it's not tied to a single `date_key`.
- 🟡 **DQ-2 — 100%-chronic SKUs may be SS-target artifacts.** If SS is set unrealistically high (see V2 refresh),
  "always below" may mean "target too high," not "always short" — cross-check with the SS-refresh decomposition
  before labelling a SKU a supply failure.
- 🟢 **DQ-3 — the snapshot depth (55) is more than enough**; no data shortage.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| 100%-below SKUs (chronic) | either genuine chronic under-supply **or** an unrealistically high safety-stock target — must disambiguate with V2 decomposition |
| Nervous SKUs (from DK-12) | forecast/DOC-driven SS target recomputes each cycle → target thrash on volatile-demand SKUs |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **temporal-class tag** to every at-risk SKU: `acute` / `chronic` / `nervous` — dictates act vs escalate vs ignore | build | 🔴 must (biggest time-saver) |
| 2 | Chronic = **N of last M snapshots below**, trailing window across target weeks (not one fixed week) (DQ-1) | build | 🟡 should |
| 3 | For chronic SKUs, **cross-check SS-realism** (V2 decomposition) before calling it a supply failure — route "target too high" to a policy fix, not an expedite (DQ-2) | build + planner | 🔴 must |
| 4 | Route **nervous** SKUs to a "don't react — target will revert" hold; **chronic** to a systemic-fix backlog; **acute** to the action workflow | planner | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V10: chronic detection — % of snapshots below SS for a fixed target week (READ-ONLY).
WITH perSnap AS (
  SELECT process_date, product_bigint_key po, inventory_organization_bigint_key io,
         MAX(CASE WHEN projected_available_balance<safety_stock THEN 1 ELSE 0 END) below
  FROM prod_edw.fact.`20_supply_daily`
  WHERE process_date>=20260701 AND plan_name='20 Global Supply Plan'
    AND date_key=20261012 AND safety_stock>0
  GROUP BY 1,2,3),
chronic AS (SELECT po, io, COUNT(*) snaps, SUM(below) snaps_below FROM perSnap GROUP BY 1,2)
SELECT i.item_id, o.organization_code org, c.snaps, c.snaps_below,
       ROUND(c.snaps_below/c.snaps*100,0) pct_below
FROM chronic c
JOIN prod_edw.dimension.items_scd1 i ON c.po=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON c.io=o.inventory_organization_bigint_key
WHERE c.snaps>=10 AND c.snaps_below>=1 ORDER BY c.snaps_below DESC LIMIT 10;
```

*(Nervousness + SS-refresh coupling queries are logged in the DK-12 detail / V2 — validated there: demand ~+220%
/ SS target ~+17.6% moved together; 2,668 series thrashed 3+ times over 5 snapshots.)*
