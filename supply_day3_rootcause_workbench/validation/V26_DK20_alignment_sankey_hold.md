<div align="center">

# V26 (DK-20) · Alignment KPI + Sankey + Intentional-Hold — Validation

</div>

**Lead (cross-pollination):** the peer MRO app shows an **"inventory alignment %"** north-star, a **Sankey** of $
by health status, and **intentional-hold** states (Strategic-Reserve / BOM-Standby) so it doesn't mis-flag
deliberate holds. Validate all three for MKE.

---

## 1 · Inventory-alignment KPI (by SKU×org, next quarter)

| health state | SKU×orgs | share |
|---|---|---|
| **Healthy** | 36,526 | **54%** |
| Excess (>3× SS) | 20,272 | 30% |
| At-risk / short | 10,996 | 16% |

→ **Alignment = 54% healthy** (single north-star KPI). Clean, exec-friendly, one number for the landing screen.

## 2 · Sankey health-status flow — ✅ works
Confirmed buildable (also in the cross-pollination doc): **Total on-hand $ → ABC class → health state.** The
three health states above are the terminal nodes; $ can replace SKU-count for the value view.

## 3 · Intentional-hold signal — 🟡 partial (and a model correction)

| ss_managed | planning_method | SKUs | on-hand $M |
|---|---|---|---|
| unset | Not planned | 68,151 | $1,031.2M |
| **Yes** | Not planned | 33,065 | **$446.5M** |
| No | Not planned | 2,218 | $148.8M |
| unset | **Min-max planning** | 40,093 | $11.3M |
| Yes | Min-max planning | 12,924 | $4.1M |
| Yes/unset | **Reorder point planning** | 5 | ~$0 |

**Two findings:**
- **`safety_stock_managed_flag='Yes'`** marks **~46k SKUs / $450M as actively safety-stock-managed** — a *partial*
  intentional-hold signal (these are deliberately stocked, so shouldn't be auto-flagged dormant/excess).
- **Model correction to V25:** MKE **does** have `inventory_planning_method` with **Min-max (53k SKUs) and
  Reorder-point (5)** — but they're a tiny slice ($15M); the overwhelming majority ($1.6B) is **"Not planned"**
  (i.e., projection-driven). So V25's "no min-max policy" is *mostly* right — min-max exists but is negligible.

## 📖 The story the data tells

All three peer-app framings land, with nuance:
- **The alignment KPI is genuinely useful** — 54% healthy / 30% excess / 16% short is a single sentence an exec
  gets instantly, and it's the natural headline for the day-in-the-life landing screen. (The peer showed 29%;
  MKE by SKU-count is 54% — different base, same idea.)
- **The Sankey is real** and richer than the peer's (our validated health states as terminal nodes).
- **Intentional-hold is only *partially* signalled.** `safety_stock_managed_flag='Yes'` ($450M) is a real "this
  is deliberately stocked" marker — enough to stop the dormant/excess lenses (V7/V23) from crying wolf on managed
  safety stock. But there's **no explicit Strategic-Reserve / BOM-Standby flag** like the peer app has; MKE would
  need to infer intentional-hold from SS-managed + planning-method + (later) a BOM-dependency signal. So we can
  *reduce* false flags now, but not fully replicate the peer's clean intentional-hold health states.

The **model correction matters**: MKE isn't purely projection-based — it has a small min-max/ROP tail (53k SKUs,
$15M). Negligible in $, but it means a *future* parameter-recommendation (V25/DK-19) could target the min-max SKUs
specifically, where a ROP/MAX genuinely exists.

## Verdict: ✅ alignment KPI + Sankey confirmed · 🟡 intentional-hold partial

**What works ✅**
- Alignment % is a clean, computable north-star; Sankey flow validated; both ready to build.

**Data-quality findings**
- 🟡 **DQ-1 — no explicit intentional-hold flag** (no Strategic-Reserve/BOM-Standby). Approximate with
  `safety_stock_managed_flag='Yes'` ($450M) + planning-method; a true BOM-standby needs a BOM-dependency join.
- 🟡 **DQ-2 — alignment % is SKU-count based here**; do a **$-weighted** version for the exec KPI (a few big-$
  SKUs matter more than many small ones).
- 🟢 **DQ-3 — `inventory_planning_method` is a useful new dimension** (Not-planned / Min-max / ROP) — corrects
  V25 and enables planning-method segmentation.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| No clean intentional-hold state | MKE doesn't tag Strategic-Reserve/BOM-Standby explicitly; must be inferred |
| 99% "Not planned" | MKE plans by projection (PAB), not min-max — min-max is a tiny legacy tail |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Ship the **inventory-alignment % KPI** ($-weighted) on the landing/Dashboard screen | build | 🟢 cheap, high visibility |
| 2 | Build the **health-status Sankey** (Total → ABC → health), non-DC orgs filtered (V20) | build | 🟡 should |
| 3 | Use **`safety_stock_managed_flag='Yes'` as a partial intentional-hold** to suppress false dormant/excess flags (protects V7/V23/V12 from crying wolf) | build | 🟡 should |
| 4 | Add **`inventory_planning_method`** as a segmentation dimension; target any future param-recommendation (DK-19) at the min-max/ROP tail where it applies | build | 🟡 should |
| 5 | A true Strategic-Reserve/BOM-Standby flag needs a **BOM-dependency signal** — later | product | 💭 later |

---

## ✅ Logged successful queries

```sql
-- V26 DK-20 (1): alignment KPI / health-status distribution (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
pos AS (SELECT product_bigint_key it, inventory_organization_bigint_key io,
    MIN(projected_available_balance - safety_stock) mingap, MAX(projected_available_balance) maxpab, MAX(safety_stock) ss
  FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan' AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0
  GROUP BY 1,2)
SELECT CASE WHEN mingap<0 THEN 'At-risk / short' WHEN maxpab>ss*3 THEN 'Excess' ELSE 'Healthy' END health,
       COUNT(*) sku_orgs FROM pos GROUP BY 1 ORDER BY sku_orgs DESC;
```
```sql
-- V26 DK-20 (3): intentional-hold signal + planning-method (READ-ONLY).
WITH latest AS (SELECT MAX(date_key) dk FROM prod_edw.fact.inventory_days_on_hand),
oh AS (SELECT ioh.series_bigint_key sk, SUM(ioh.on_hand_cost) val
  FROM prod_edw.fact.inventory_days_on_hand ioh JOIN latest ON ioh.date_key=latest.dk
  JOIN prod_edw.dimension.inventory_organization_scd1 o ON ioh.inventory_organization_bigint_key=o.inventory_organization_bigint_key
  WHERE o.designated_org_code IS NOT NULL AND ioh.on_hand_cost>0 GROUP BY 1)
SELECT COALESCE(x.safety_stock_managed_flag,'unset') ss_managed,
       COALESCE(x.inventory_planning_method,'none') planning_method,
       COUNT(*) skus, ROUND(SUM(oh.val)/1e6,1) onhand_M
FROM oh LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON oh.sk=x.series_bigint_key
GROUP BY 1,2 ORDER BY onhand_M DESC LIMIT 8;
```

**Findings:** alignment 54% healthy; Sankey ready; intentional-hold *partial* (`ss_managed='Yes'` $450M, no
explicit Strategic-Reserve flag); and `inventory_planning_method` corrects V25 — MKE has a tiny min-max/ROP tail
($15M) but is 99% projection-based.
