<div align="center">

# V15 (N1) · Transition / NPD SKUs — Validation

</div>

**Lead (from V14):** the transcript named **"transition-level"** as one of its two biggest template permutations,
but `transition_active_flag` was 100% NULL in `10_demand_daily` and no Transition plan rows existed in
`20_supply_daily`. Question: does transition/NPD status exist *anywhere*, and is it a distinct root cause?

---

## Where it actually lives — the ITEM MASTER, not the demand fact

`prod_edw.dimension.items_scd1` carries: **`transition_sku_flag`, `is_npd_item`, `npd_launch_date`,
`npd_project_name`, `item_status`.** Plus dedicated tables: `staging_oracle_fusion_erp.item_lifecycle_phases`
(+`_temporal`), `staging_supply_chain.oracle_npd_launchdate`.

## Populations (live)

| population | count | of 300,115 items |
|---|---|---|
| **Transition SKUs** (`transition_sku_flag=true`) | **71,484** | 24% |
| **NPD items** (`is_npd_item=true`) | **4,038** | 1.3% |

## The payoff — transition/NPD are OVER-REPRESENTED in shortages

| population | shortage SKUs | transition | NPD |
|---|---|---|---|
| count | 9,022 | **3,320 (37%)** | **1,037 (11.5%)** |
| baseline rate | — | 24% | 1.3% |
| **over-representation** | — | **~1.5×** | **~9×** |

→ Transition SKUs are **1.5× over-represented** in shortages (37% vs 24% baseline); **NPD items ~9×** (11.5% vs
1.3%). Transition/NPD is a **real, distinct, over-firing root cause** — exactly as the transcript implied.

## 📖 The story the data tells

The transcript was right to name transition as a top permutation — and the data explains *why* it kept coming up:
**new-product and phasing SKUs stock out far more than mature ones.** That's intuitive (no demand history, ramp
uncertainty, first-buy timing) but now it's quantified: an NPD item is ~9× more likely to appear in the shortage
book than its share of the catalog. The reason it looked "absent" in V14 is a modeling trap — transition status
is an **item-master attribute**, not a demand-fact flag, so the demand-fact column is (correctly) empty. The
signal was there all along, one join away.

This reframes a chunk of the shortage board: a transition/NPD shortage is a **different story** than a mature-SKU
shortage. "Home Depot over-consumed" is a demand-surprise on a known baseline; "3697-XX is an NPD ramping faster
than the first buy" is a *launch-execution* problem with different owners (NPD/marketing) and different levers
(accelerate the launch buy, not expedite a replenishment). The reason-code taxonomy (DK-8) even has
**"NPD/Transition assumptions"** and **"Make-to-Order"** as named miss reasons — the tool should route these
shortages to that lens, not the standard demand/supply triage.

## Verdict: ✅ CONFIRMED — transition/NPD is a distinct, sourceable, over-represented root cause

**What works ✅**
- Transition + NPD flags live on `items_scd1` (one join from any SKU); 71,484 transition, 4,038 NPD.
- Over-representation in shortages is real and large (1.5× / 9×).

**Data-quality findings**
- 🟡 **DQ-1 — status is item-master, not demand/supply fact.** The `10_demand_daily.transition_active_flag` is
  NULL; use `items_scd1.transition_sku_flag` / `is_npd_item` instead. (This is why V14 saw it as "absent.")
- 🟡 **DQ-2 — `transition_sku_flag` is very broad (24% of catalog).** Likely includes any SKU ever in a
  transition; combine with `npd_launch_date` recency / `item_lifecycle_phases` to isolate *active* ramp/EOL.
- 💭 **DQ-3 — the "23 Transition SKU Supply Plan" is still empty** in `20_supply_daily` — the dedicated plan isn't
  populated; use the item-master flags for now.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| NPD ~9× over-represented in shortages | no demand history + ramp uncertainty + first-buy timing → structurally shortage-prone |
| Looked "absent" in V14 | transition is an **item attribute**, not a plan-fact flag — wrong table probed |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Join `items_scd1.transition_sku_flag`/`is_npd_item` into the serving layer as a **lifecycle class** (mature / transition / NPD) | build | 🔴 must |
| 2 | Add a **lifecycle badge** on the watchlist + a **NPD/launch-risk lens** — route these shortages to launch-execution owners (NPD/marketing), not standard triage | build | 🟡 should |
| 3 | Refine "active transition" using `npd_launch_date` recency + `item_lifecycle_phases` (24% flag is too broad) | build | 🟡 should |
| 4 | Map transition/NPD shortages to the governed reason codes "NPD/Transition assumptions" / "Make-to-Order" (DK-8) | build | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V15 N1: transition/NPD populations (READ-ONLY).
SELECT SUM(CASE WHEN transition_sku_flag=true THEN 1 ELSE 0 END) transition_skus,
       SUM(CASE WHEN is_npd_item=true THEN 1 ELSE 0 END) npd_items, COUNT(*) total
FROM prod_edw.dimension.items_scd1;
```
```sql
-- V15 N1: transition/NPD over-representation in shortages (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
short AS (SELECT DISTINCT s.product_bigint_key po FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0 AND s.projected_available_balance<s.safety_stock)
SELECT COUNT(*) short_skus,
       SUM(CASE WHEN i.transition_sku_flag=true THEN 1 ELSE 0 END) short_transition,
       SUM(CASE WHEN i.is_npd_item=true THEN 1 ELSE 0 END) short_npd
FROM short JOIN prod_edw.dimension.items_scd1 i ON short.po=i.item_bigint_key;
```

**Gotcha logged:** transition/NPD status is on **`items_scd1`** (`transition_sku_flag`, `is_npd_item`,
`npd_launch_date`), NOT the demand fact (`10_demand_daily.transition_active_flag` is NULL). Probe the item master.
