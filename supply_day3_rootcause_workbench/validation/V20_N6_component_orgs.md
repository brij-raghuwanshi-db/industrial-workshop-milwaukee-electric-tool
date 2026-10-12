<div align="center">

# V20 (N6) · Component / Bulk / Non-DC Orgs — Validation

</div>

**Lead (from V1/V2/V5/V7/V9):** orgs **8000** and **2092** recurred as $-ranking distorters with huge magnitudes.
Hypothesis: they're a different grain (components / consignment / 3PL), not finished-goods DCs, and mixing them
corrupts shortage/excess $-rankings.

---

## What they actually are (live)

| org | name | designated_org | type |
|---|---|---|---|
| 2012 | Olive Branch | 2012 | ✅ finished-goods DC |
| 2013 | OB – Home Depot | 2012 | ✅ finished-goods DC |
| 1080 | Byhalia, MS | 2012 | ✅ mfg/DC (in network) |
| **2092** | **3PL Parts & Service** | 2012 | ⚠ **third-party parts/service — different grain** |
| **8000** | **Supplier Inv** | **None** | ⚠ **supplier-managed / consignment — outside the DC network** |

## 📖 The story the data tells

The recurring distortion had a concrete cause: **8000 and 2092 aren't finished-goods DCs at all.** 8000 is
**"Supplier Inv"** (supplier-managed / consignment stock, tellingly with `designated_org=None` — it doesn't even
belong to a DC network), and 2092 is **"3PL Parts & Service"** (third-party parts, a different fulfillment model
and grain). When V1's watchlist or V7's excess board ranked by dollars, these orgs threw off numbers orders of
magnitude larger than the DCs because they're a *different kind of inventory* — components/consignment/service
parts, not sellable finished goods at an Olive Branch DC.

This validates the DQ guard that kept recurring: **segregate by org type before any dollar comparison.** But it's
more than hygiene — it points at genuinely separate lenses the Day-3 scope never intended: **supplier-managed /
consignment inventory** (a different ownership + replenishment model) and **service-parts / 3PL** (a different
business). Rolling them into the finished-goods planner's shortage board is a category error; each likely serves
a different audience (procurement/consignment ops; service-parts planning).

## Verdict: ✅ CONFIRMED — 8000/2092 are non-DC grains; segregate, and they're candidate separate lenses

**What works ✅**
- Root cause of the recurring distortion identified: org type, not data error.
- `organization_name` + `designated_org_code=None` cleanly distinguish them.

**Data-quality findings**
- 🔴 **DQ-1 — segregate non-DC orgs from finished-goods $-rankings** (8000 Supplier Inv, 2092 3PL, and any
  `designated_org_code IS NULL`). This is the fix for the distortion seen across V1/V2/V5/V7/V9.
- 🟡 **DQ-2 — org type isn't a clean flag** — inferred from `organization_name` text + null designated_org;
  ideally add a governed `org_type` (DC / mfg / consignment / 3PL / service).

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| 8000/2092 distort $-rankings | they're **consignment (8000) / 3PL-parts (2092)** — different inventory grain & ownership than finished-goods DCs |
| Recurred everywhere | no `org_type` filter in the rankings; all orgs treated as comparable |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Filter/segment by org type** — exclude non-DC orgs (`designated_org_code IS NULL`, "Supplier Inv", "3PL") from finished-goods shortage/excess $-rankings | build | 🔴 must (fixes V1/V2/V5/V7/V9 distortion) |
| 2 | Add a governed **`org_type`** (DC / mfg / consignment / 3PL / service) to the org dimension for clean filtering | data eng | 🟡 should |
| 3 | Consider **separate lenses** for supplier-managed/consignment (8000) and service-parts/3PL (2092) — different audiences | product | 💭 later |

---

## ✅ Logged successful query

```sql
-- V20 N6: characterize the outlier orgs (READ-ONLY).
SELECT organization_code, organization_name, designated_org_code
FROM prod_edw.dimension.inventory_organization_scd1
WHERE organization_code IN ('8000','2092','2012','2013','1080')
ORDER BY organization_code;
```

**Gotcha logged:** org **8000 = Supplier Inv (consignment, designated_org=None)** and **2092 = 3PL Parts &
Service** are NOT finished-goods DCs — segregate by org type before any $-ranking, or they dominate with
non-comparable magnitudes.
