<div align="center">

# V23 (DK-17) · Dormant / Obsolescence / E&O — Validation

</div>

**Lead (cross-pollination):** the peer MRO app has a **Dormant** health state + last-consumption date. Hypothesis:
MKE has stock that isn't moving at all (heading to write-off) — distinct from *active* overstock (V7). **Sources:**
`inventory_days_on_hand.on_hand_cost`, `dim_series_ext_vw.obsolete_date`, `10_demand_daily.shipments_history`.

---

## Test 1 — the `obsolete_date` flag (sparse)

| status | SKUs | on-hand $M |
|---|---|---|
| active | 156,430 | $1,641.0M |
| **OBSOLETE (past date)** | **66** | **$0.9M** |

→ The `obsolete_date` flag is **too sparse** to be the dormant signal (only $0.9M with on-hand). Use
movement-recency instead.

## Test 2 — dormant by last-shipment recency (the real signal)

| movement class | SKUs | on-hand $M |
|---|---|---|
| Active (shipped <3mo) | 96,118 | $1,060.1M |
| **NEVER shipped** | **25,804** | **$545.0M** ⚠ |
| Slow (3–12mo) | 19,677 | $20.6M |
| **DORMANT (>12mo no ship)** | **14,897** | **$16.3M** |

## 📖 The story the data tells

The dormant lens is real and it surfaced something **bigger than the lead predicted.** The `obsolete_date` flag
looked like the obvious source but it's near-empty ($0.9M) — a classic trap where the "obvious" column
under-reports. **Movement recency** tells the true story, and the standout is a **$545M pile of on-hand across
25,804 SKUs that has NEVER shipped.** That's not "slow" — it's inventory the demand history has *no record of
selling*, sitting on the shelf. Even the strictly-dormant (>12mo, $16.3M) and slow (3–12mo, $20.6M) buckets are
real write-off risk.

This is a genuinely different problem from V7's *active overstock* (which is fast-moving SKUs with too much
cover). Dormant/never-shipped is **frozen capital + obsolescence exposure** — a finance and E&O conversation, and
one the shortage-focused Day-3 scope would never surface. The $545M "never shipped" especially deserves scrutiny:
some is legitimate (new-product pre-stock, strategic/safety-critical spares — the intentional-hold states from
DK-20), but a chunk is likely dead stock. **The dormant lens must pair with the intentional-hold flag (DK-20)**
or it will over-accuse deliberate reserves.

## Verdict: ✅ CONFIRMED — dormant/E&O is real & material; use movement-recency, not the obsolete flag

**What works ✅**
- Movement-recency cleanly segments active / slow / dormant / never-shipped; $545M never-shipped is a major
  unwatched exposure.

**Data-quality findings**
- 🔴 **DQ-1 — `obsolete_date` is too sparse** ($0.9M) to be the dormant signal — use last-shipment recency from
  `10_demand_daily.shipments_history` instead.
- 🟡 **DQ-2 — "never shipped" is heterogeneous** — includes legitimate NPD pre-stock (V15/DK-16) + strategic/
  safety spares (intentional-hold, DK-20) + true dead stock. Must be split before accusing it of E&O.
- 🟡 **DQ-3 — recency uses shipment history**; a SKU shipped from a different plan/channel could look dormant —
  confirm shipment coverage across plans.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| obsolete_date near-empty | the flag isn't consistently maintained → not a reliable dormant signal |
| $545M never-shipped | mix of NPD pre-stock, strategic spares, and genuine dead stock — no single cause |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Build the **dormant/E&O lens on movement-recency** (last-ship age bands), not `obsolete_date` | build | 🔴 must |
| 2 | **Pair with intentional-hold (DK-20) + NPD (DK-16/V15)** before flagging as dead stock — or it over-accuses legitimate holds | build | 🔴 must |
| 3 | Prioritize the **$545M never-shipped** for a write-off/liquidation review (finance) — after removing legitimate holds | finance/planner | 🟡 should |
| 4 | Feed dormant into the Sankey (DK-20) as its own health state | build | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V23 DK-17 Test 2: dormant by last-shipment recency (READ-ONLY).
WITH latest AS (SELECT MAX(date_key) dk FROM prod_edw.fact.inventory_days_on_hand),
oh AS (SELECT ioh.item_bigint_key it, SUM(ioh.on_hand_cost) val
  FROM prod_edw.fact.inventory_days_on_hand ioh JOIN latest ON ioh.date_key=latest.dk
  JOIN prod_edw.dimension.inventory_organization_scd1 o ON ioh.inventory_organization_bigint_key=o.inventory_organization_bigint_key
  WHERE o.designated_org_code IS NOT NULL AND ioh.on_hand_cost>0 GROUP BY 1),
lastship AS (SELECT product_bigint_key it, MAX(date_key) last_ship_dk
  FROM prod_edw.fact.`10_demand_daily` WHERE shipments_history>0 GROUP BY 1)
SELECT CASE WHEN ls.last_ship_dk IS NULL THEN 'NEVER shipped'
            WHEN ls.last_ship_dk < 20250903 THEN 'DORMANT (>12mo no ship)'
            WHEN ls.last_ship_dk < 20260603 THEN 'slow (3-12mo)'
            ELSE 'active (<3mo)' END mv,
       COUNT(*) skus, ROUND(SUM(oh.val)/1e6,1) onhand_M
FROM oh LEFT JOIN lastship ls ON oh.it=ls.it GROUP BY 1 ORDER BY onhand_M DESC;
```

**Gotcha logged:** `obsolete_date` is **near-empty** as a value signal ($0.9M) — the real dormant/E&O signal is
**last-shipment recency**; and "never shipped" ($545M) must be split from NPD pre-stock + intentional holds
before calling it dead stock.
