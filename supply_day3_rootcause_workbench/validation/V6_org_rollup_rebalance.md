<div align="center">

# V6 · Org Rollup + Rebalance (within/across orgs) — Validation

</div>

**Claims (design):** roll an item up across orgs via `designated_org_code`; detect same-SKU short-in-one-org /
excess-in-another → recommend transfer before buy (S2/DK-9). **Source:** `20_supply_daily` +
`inventory_organization_scd1` (designated_org) + `transfer_orders` (lanes).

---

## Test — 10 item×networks, short in one org & excess in another (near-term)

| # | item_id | short units | excess units | #short orgs | #excess orgs | coverage verdict |
|---|---|---|---|---|---|---|
| 1 | 50567041 | −267,754 | 132,413 | 1 | 1 | partial (49%) |
| 2 | **48228902WM** | −244,942 | **684,026** | 1 | 2 | **FULLY coverable** |
| 3 | 48221500 | −229,211 | 1,330 | 2 | 1 | partial (<1%) |
| 4 | 50567252 | −94,174 | 65,497 | 1 | 1 | partial (70%) |
| 5 | 48221725V | −88,848 | 332 | 2 | 1 | partial |
| 6 | 48221503 | −86,083 | 73 | 2 | 1 | partial |
| 7 | 48223170P | −85,930 | 22,187 | 1 | 2 | partial (26%) |
| 8 | 48732014TL | −82,343 | 10 | 1 | 1 | partial |
| 9 | 48224560 | −63,866 | 1,035 | 2 | 1 | partial |
| 10 | 48228903F | −61,789 | 1,949 | 2 | 1 | partial |

**Per-org proof (item #2, `48228902WM`):** org **2013 = −244,942** (the alarm) but org **2012 = +680,409** in the
same network → a per-org screen cries shortage; pooled, there's **2.8× the coverage one org over.**

## 📖 The story the data tells

The rebalance idea is real — but the data tells a more disciplined story than "1,646 free transfers." Of ten
short-and-excess items, **only one (48228902WM) is *fully* coverable by in-network excess; the other nine are
partial** — the excess exists but doesn't fully plug the hole (from 70% down to <1%). So the honest headline
isn't "transfer instead of buy," it's **"transfer *first*, then buy the remainder"** — the tool must quantify the
coverable fraction, or it will over-promise and a planner will get burned when a "rebalance" leaves them still
short.

But where it hits, it hits hard: 48228902WM is short 245k at org 2013 while org 2012 sits on 680k — the kind of
"we're not actually short, it's in the wrong building" case the transcript described almost verbatim ("pooled
inventory rather than what an individual org record shows"). **The data validates that the per-org view is
genuinely misleading**, and that the network rollup turns a false alarm into a transfer order. That single
reframing — from "expedite a PO" to "move what we already own" — is the highest-ROI action in the whole product,
and it's invisible on every screen the planners use today.

## Verdict: ✅ works — with the essential refinement that coverage is a *fraction*, not a yes/no

**What works ✅**
- `designated_org_code` rollup pools correctly; short-here/excess-there detection is real.
- The per-org-misleads / pooled-is-truth thesis is confirmed on real data (48228902WM).

**Data-quality findings**
- 🟡 **DQ-1 — coverage is mostly partial.** 9/10 can't be fully covered by transfer → **must show coverable
  units / %**, not a binary "rebalance available." Over-stating coverage would erode trust fast.
- 🟡 **DQ-2 — network key is a bigint** (`776578178872804310`) — map to a human network name/`designated_org_code`
  for display.
- 🟡 **DQ-3 — doesn't yet net transfer lead time / in-transit.** A transfer takes ~1wk (V-lanes); the coverage
  calc should respect timing + subtract already-in-transit (open transfer_orders, V-DK11) to avoid double-count.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Mostly partial coverage | shortages are often network-wide (all orgs low); true "wrong-building" surplus is the minority |
| Per-org misleads | Oracle plans per-org; pooled availability isn't a native record — must be derived via `designated_org_code` |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Show **coverable units and %** on every rebalance suggestion; label "transfer covers X, buy remainder Y" | build | 🔴 must (trust) |
| 2 | Recommend **transfer-first, buy-the-rest** as the default action ordering | build | 🔴 must |
| 3 | Net out **in-transit** (open transfer_orders) and **transfer lead time** before proposing a transfer qty | build | 🟡 should |
| 4 | Map network bigint → human name for display | build | 🟡 should |
| 5 | Feed the fully-coverable cases (like 48228902WM) as **highest-confidence** rebalance actions | planner | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V6: short-here / excess-there within a network, with coverage verdict (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
byorg AS (
  SELECT product_bigint_key po, designated_organization_bigint_key net,
         inventory_organization_bigint_key org,
         MIN(projected_available_balance - safety_stock) gap
  FROM prod_edw.fact.`20_supply_daily`, latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261005 AND safety_stock>0
  GROUP BY 1,2,3),
roll AS (
  SELECT po, net,
         SUM(CASE WHEN gap<0 THEN gap ELSE 0 END) short_units,
         SUM(CASE WHEN gap>0 THEN gap ELSE 0 END) excess_units,
         SUM(CASE WHEN gap<0 THEN 1 ELSE 0 END) short_orgs,
         SUM(CASE WHEN gap>0 THEN 1 ELSE 0 END) excess_orgs
  FROM byorg GROUP BY 1,2)
SELECT i.item_id, r.net, ROUND(r.short_units,0) short_u, ROUND(r.excess_units,0) excess_u,
       r.short_orgs, r.excess_orgs,
       CASE WHEN r.excess_units >= ABS(r.short_units) THEN 'FULLY coverable by transfer' ELSE 'partial' END verdict
FROM roll r JOIN prod_edw.dimension.items_scd1 i ON r.po=i.item_bigint_key
WHERE r.short_orgs>0 AND r.excess_orgs>0 ORDER BY ABS(r.short_units) DESC LIMIT 10;
```
```sql
-- V6: per-org breakdown proving pooled-vs-per-org (swap item_id).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`)
SELECT o.organization_code org, ROUND(MIN(s.projected_available_balance - s.safety_stock),0) worst_gap
FROM prod_edw.fact.`20_supply_daily` s JOIN latest ON s.process_date=latest.pd
JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON s.inventory_organization_bigint_key=o.inventory_organization_bigint_key
WHERE i.item_id='48228902WM' AND s.plan_name='20 Global Supply Plan'
  AND s.date_key BETWEEN 20260907 AND 20261005 AND s.safety_stock>0
GROUP BY 1 ORDER BY worst_gap;
```
