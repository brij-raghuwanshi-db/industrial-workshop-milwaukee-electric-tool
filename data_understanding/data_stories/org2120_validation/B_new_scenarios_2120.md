# Org 2120 (Mexico Supply Plan) — Unique Scenarios & Data Patterns

**Report Date:** 2026-08-31  
**Analysis Scope:** Comparison of `sandbox_operations.po_management.rung2_plan_vs_actual` between org 2120 (Mexico, 9,758 items) and org 2012 (Global, 28,146 items)  
**Data Grain:** Item × Organization × Week  
**Queries:** READ-ONLY against gold table only

> **⚠️ CORRECTION (2026-08-31, post-verification):** this report's "net-receiving node → intercompany
> transfer from 2012" hypothesis (Obs 4, and the transfer-risk notes) was later **refuted** by checking the
> actual network tables. **2120 has ZERO transfer-order lines and NO "Transfer from" sourcing rules — it is
> a directly-sourced (Buy/Make) leaf, not a transfer-fed hub. 2012 is the transfer hub** (395,940
> Transfer-from rules, 19 source orgs). The ship/receive ratio (0.094) is real, but the cause is inbound
> purchasing/manufacturing, not transfer. See `C_synthesis…` N3 and `D_network_flow_tables.md`. The rest of
> this report's findings (planner concentration, 41% unique SKUs, lean-yet-green, plan coverage) stand.

---

## Executive Summary

Org 2120 exhibits **6 genuinely distinct scenarios** from org 2012. These patterns reflect Mexico's role as a dedicated regional supply plan with unique sourcing, planning rigor, demand-fulfillment cadence, and inventory posture. None are confounds; all are actionable.

---

## Discovery Scenarios (Ranked by Distinctness & Actionability)

### Scenario 1: Ultra-Concentrated Planner Population (Mexico-Specific Planning Model)

**Category:** Planning org structure | **Priority:** P2 (operational pattern)

#### Discovery SQL (READ-ONLY):
```sql
SELECT organization_code, COUNT(DISTINCT planner_name) as unique_planners, COUNT(*) as total_rows
FROM sandbox_operations.po_management.rung2_plan_vs_actual
GROUP BY organization_code;
```

#### Evidence:
| Org | Unique Planners | Total Rows | Rows per Planner (avg) |
|-----|-----------------|------------|------------------------|
| 2012 (Global) | 92 | 219,938 | 2,391 rows/planner |
| 2120 (Mexico) | 6 | 77,273 | 12,879 rows/planner |

**2120 Planner Breakdown:**
| Planner Name | Rows Managed | Unique Items | % of 2120 |
|--------------|--------------|--------------|----------|
| Miller, Sarah | 40,957 | 5,170 | 53.00% |
| Ystesund, Nolan | 24,686 | 3,101 | 31.95% |
| Wick, Madison | 9,085 | 1,142 | 11.76% |
| Dickson, Aiden | 1,456 | 182 | 1.88% |
| Unassigned | 924 | 141 | 1.20% |
| Murphy, Nicholas | 165 | 22 | 0.21% |

#### Why Mexico-Specific:
- **2012 has 92 planners** distributing global responsibility across 219K rows (~2.4K rows/planner).
- **2120 has only 6 planners**, concentrating Mexico supply-plan responsibility into 12.9K rows per person.
- This concentration implies a **centralized, compact regional planning model** vs. a distributed global one.
- **Miller & Ystesund own 85% of Mexico planning** — a critical bottleneck and knowledge concentration risk.

#### Data-Model Implication:
- Mexico planning is **not a federated multi-planner delegate model**; it is **top-down centralized** from 2–3 key personnel.
- Workload imbalance: Miller manages 53%; Wick manages 11.76%. Turnover risk for Miller = supply-plan paralysis.
- **Handoff risk:** If Miller/Ystesund leave, Mexico supply plan loses institutional knowledge.

#### Actionable Insight:
- Validate whether 2–3 planners can sustainably manage 12,879 rows (items × weeks) each.
- Cross-train backup planners; document key decisions & heuristics from Miller & Ystesund.
- Monitor alert-escalation load on these 6 individuals.

---

### Scenario 2: Mexico Planning Has Far Better Planned-PAB Coverage (Data Completeness)

**Category:** Data quality & plan structure | **Priority:** P1 (data model)

#### Discovery SQL (READ-ONLY):
```sql
SELECT organization_code, plan_name, 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN planned_pab IS NULL THEN 1 END) as null_planned_pab,
  ROUND(100.0 * COUNT(CASE WHEN planned_pab IS NULL THEN 1 END) / COUNT(*), 2) as pct_null_pab,
  COUNT(CASE WHEN planned_safety_stock IS NULL THEN 1 END) as null_safety_stock,
  ROUND(100.0 * COUNT(CASE WHEN planned_safety_stock IS NULL THEN 1 END) / COUNT(*), 2) as pct_null_safety_stock
FROM sandbox_operations.po_management.rung2_plan_vs_actual
GROUP BY organization_code, plan_name;
```

#### Evidence:
| Org | Plan | Total Rows | Null planned_pab | % Null planned_pab | Null safety_stock | % Null safety_stock |
|-----|------|-----------|------------------|--------------------|-------------------|---------------------|
| 2012 | Global | 219,938 | 39,964 | **18.17%** | 88,767 | 40.36% |
| 2120 | Mexico | 77,273 | 1,565 | **2.03%** | 30,236 | 39.13% |

#### Why Mexico-Specific:
- **2120 has 9× fewer null planned_pab rows** than 2012 (2.03% vs 18.17%).
- This signals that **Mexico plan enforces planned-pab entry discipline** across its concentrated planner team, while the **global plan (2012) has gaps in 1 of 5.5 rows**.
- Safety stock nulls are similar (39–40%), but the **planned_pab completeness is distinctly higher in Mexico**.

#### Data-Model Implication:
- Mexico plan is **more rigorously populated** in the demand-signal column (planned_pab).
- Global plan has a **data-ingestion or validation gap** affecting planned-pab coverage.
- The 18.17% null rate in 2012 is likely due to **multi-source / federated data feeds** with inconsistent SLAs; Mexico's 2.03% suggests **tighter ETL or manual override**.

#### Actionable Insight:
- Investigate which 2012 items/planners contribute the 39,964 null planned_pab rows. Are they legitimate no-plan items, or data-pipeline gaps?
- Audit Mexico's planned-pab entry process to codify what makes it 9× better, then apply to 2012.
- Consider **planned-pab nullness as an alert trigger** in 2012 until root cause is addressed.

---

### Scenario 3: Lower On-Hand Variance & More Stable Supply Pattern (Mexico-Specific Dynamics)

**Category:** Supply chain stability | **Priority:** P2 (operational signal)

#### Discovery SQL (READ-ONLY):
```sql
SELECT organization_code, 
  COUNT(*) as total_rows,
  ROUND(AVG(ABS(onhand_variance_abs)), 2) as avg_abs_variance,
  ROUND(AVG(onhand_variance_pct), 2) as avg_pct_variance,
  ROUND(STDDEV(onhand_variance_pct), 2) as stddev_pct_variance,
  COUNT(CASE WHEN ABS(onhand_variance_pct) > 50 THEN 1 END) as rows_variance_gt_50pct,
  ROUND(100.0 * COUNT(CASE WHEN ABS(onhand_variance_pct) > 50 THEN 1 END) / COUNT(*), 2) as pct_high_variance
FROM sandbox_operations.po_management.rung2_plan_vs_actual
GROUP BY organization_code;
```

#### Evidence:
| Org | Avg Abs Variance | Avg % Variance | StdDev % Var | % High Variance (>50%) |
|-----|------------------|----------------|-------------|----------------------|
| 2012 (Global) | 495.38 units | **100.96%** | 3,140.09 | **20.93%** |
| 2120 (Mexico) | 39.77 units | **20.71%** | 1,191.02 | **14.16%** |

#### Why Mexico-Specific:
- **2120 has 5× lower average % variance** than 2012 (20.71% vs 100.96%).
- **2120 has 5.1× less volatility** (stddev 1,191 vs 3,140).
- **Only 14.16% of 2120 rows exceed ±50% variance**, vs 20.93% in 2012.
- This means **Mexico's supply-plan adherence is significantly tighter** than the global plan.

#### Data-Model Implication:
- Mexico operates with **lower demand-supply mismatch** — either demand is more predictable, supply is more responsive, or both.
- This could reflect:
  - **Smaller, more stable item set** (4,041 Mexico-only items may be lower volatility than 2012 mix).
  - **Shorter lead times / faster reorders** within Mexico (intra-regional sourcing).
  - **Smaller order batch sizes** and higher fulfillment frequency (vs. bulk imports).
  - **Better demand forecasting** due to concentrated planner expertise.

#### Actionable Insight:
- Investigate which 2012 items/planners drive the 100.96% variance spike. Are they FX-exposed, seasonal, or bulk-receipt items?
- Analyze 2120's low-variance items: what SKU, sourcing, or demand characteristics enable stability? Can patterns be replicated for high-variance 2012 items?
- Consider 2120's variance profile as a **"supply-plan health baseline"** for benchmarking.

---

### Scenario 4: Mexico Has Much Higher Green (OK) On-Hand Status & Lower Red (Out-of-Stock)

**Category:** Inventory health | **Priority:** P1 (operational signal)

#### Discovery SQL (READ-ONLY):
```sql
SELECT organization_code, onhand_status, 
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY organization_code), 2) as pct
FROM sandbox_operations.po_management.rung2_plan_vs_actual
GROUP BY organization_code, onhand_status
ORDER BY organization_code, onhand_status;
```

#### Evidence:
| Org | Green (OK) | Yellow (Warn) | Red (OOS) | No-Data |
|-----|-----------|--------------|----------|---------|
| 2012 (Global) | **36.32%** | 6.25% | **39.26%** | 18.17% |
| 2120 (Mexico) | **62.28%** | 10.14% | **25.56%** | 2.03% |

#### Why Mexico-Specific:
- **Mexico is 26% greener** (62.28% OK vs 36.32%).
- **Mexico is 13.7% less red** (25.56% OOS vs 39.26%).
- Mexico's **no-data is 9× lower** (2.03% vs 18.17%), aligning with the planned-pab completeness finding (Scenario 2).
- This is **not due to larger safety stock**. 2120 avg safety stock (112.88 units) is **lower than 2012's (1,496.78 units)** — see Scenario 5.

#### Data-Model Implication:
- **Mexico's inventory posture is optimized** — less carrying cost (lower safety stock), yet fewer stock-outs (higher green status).
- **This suggests tighter demand forecasting + faster/more frequent replenishment cycles** in Mexico.
- The **25.56% red status in 2120** (vs 39.26% in 2012) might reflect **planned scarcity** (intentional stockouts to test demand elasticity or ROI on safety stock).

#### Actionable Insight:
- Analyze Mexico's receipt and shipment frequency: do orders flow more frequently (e.g., weekly) than 2012's (monthly/quarterly)?
- Audit whether Mexico's lower red status is due to demand forecasting rigor or operational process difference (e.g., faster PO-to-receipt cycles, just-in-time supplier partnerships).
- Benchmark Mexico's green-status items against 2012 to identify if low-red-rate items can be scaled globally.

---

### Scenario 5: Mexico Operates with Ultra-Low Safety Stock (Right-Sized Inventory Management)

**Category:** Inventory strategy | **Priority:** P2 (operational pattern)

#### Discovery SQL (READ-ONLY):
```sql
SELECT organization_code, plan_name,
  COUNT(*) as total_rows,
  ROUND(AVG(CASE WHEN planned_safety_stock IS NOT NULL THEN planned_safety_stock ELSE NULL END), 2) as avg_ss_when_present,
  COUNT(CASE WHEN planned_safety_stock > 0 THEN 1 END) as rows_with_positive_ss,
  ROUND(SUM(CASE WHEN planned_safety_stock > 0 THEN planned_safety_stock ELSE 0 END), 2) as total_ss,
  ROUND(AVG(actual_end_on_hand), 2) as avg_end_onhand
FROM sandbox_operations.po_management.rung2_plan_vs_actual
GROUP BY organization_code, plan_name;
```

#### Evidence:
| Org | Avg Safety Stock (when present) | Rows with Positive SS | Total SS | Avg End On-Hand |
|-----|--------------------------------|----------------------|----------|-----------------|
| 2012 | **1,496.78 units** | 83,809 | 196.3M | 1,434.09 |
| 2120 | **112.88 units** | 44,244 | 5.3M | 175.01 |

#### Why Mexico-Specific:
- **Mexico operates with 13.3× lower average safety stock per item** (112.88 vs 1,496.78 units).
- **Mexico's total safety stock is 37× smaller** (5.3M vs 196.3M units) despite managing 27.6% of 2012's rows.
- **Mexico's end-on-hand is 8.2× lower** (175 vs 1,434 units average).
- Yet Mexico achieves **lower variance** and **higher green status** (Scenarios 3–4) with **this lower buffer**.

#### Data-Model Implication:
- **Mexico's supply model is lean/just-in-time** — it prioritizes **demand-responsive replenishment over carrying buffers**.
- 2012's high safety stock (196.3M units) suggests:
  - **Conservative planning** (higher risk aversion).
  - **Demand unpredictability** (broad global sourcing, FX exposure, cross-border lead times).
  - **Supplier variability** (inconsistent lead times or quality requiring larger buffers).
- **Mexico's low safety stock** implies:
  - **Reliable, short-lead suppliers** (intra-region or just-in-time partners).
  - **Predictable demand** (regional customer base, concentrated sourcing).
  - **Operational discipline** (fast execution, low process variance).

#### Actionable Insight:
- Mexico's safety-stock model may be under-conservative. If demand volatility increases (e.g., major customer win, channel shift), 112.88 units/item could prove inadequate. **Model demand-shock scenarios** to validate stock adequacy.
- 2012's 1,496.78 avg units/item may reflect hedging against global supply-chain disruption risk (Brexit, tariffs, port congestion). Segment 2012 by risk profile to identify items that could adopt Mexico's leaner model.
- **Cross-train 2012 suppliers on Mexico's fast-lead-time partnership model** to reduce global safety-stock requirements.

---

### Scenario 6: Mexico Has 41% Unique SKUs Not in Global Plan (Distinct Regional Sourcing Footprint)

**Category:** SKU portfolio | **Priority:** P2 (sourcing/assortment)

#### Discovery SQL (READ-ONLY):
```sql
SELECT 
  'Total 2120 items' as category, COUNT(DISTINCT item_id) as count
FROM sandbox_operations.po_management.rung2_plan_vs_actual WHERE organization_code = '2120'
UNION ALL
SELECT 'Items ONLY in 2120 (not 2012)', COUNT(DISTINCT item_id) 
FROM sandbox_operations.po_management.rung2_plan_vs_actual p2120
WHERE organization_code = '2120' AND item_id NOT IN (
  SELECT DISTINCT item_id FROM sandbox_operations.po_management.rung2_plan_vs_actual WHERE organization_code = '2012'
)
UNION ALL
SELECT 'Items in BOTH', COUNT(DISTINCT item_id)
FROM sandbox_operations.po_management.rung2_plan_vs_actual WHERE organization_code = '2120' 
  AND item_id IN (SELECT DISTINCT item_id FROM sandbox_operations.po_management.rung2_plan_vs_actual WHERE organization_code = '2012');
```

#### Evidence:
| Category | Count | % of 2120 |
|----------|-------|----------|
| Total 2120 items | 9,758 | — |
| 2120 only (Mexico-exclusive) | 4,041 | **41.41%** |
| Shared with 2012 | 5,717 | 58.59% |

**Mexico-Only Item Characteristics:**
| Metric | Value |
|--------|-------|
| Unique items (2120 only) | 4,041 |
| D-category items (low-value) | 3,363 (83.2% of 2120-only) |
| Total cost | $421,089 |
| Total received (units) | 277,906 |
| Total shipped (units) | 17,530 |

#### Why Mexico-Specific:
- **4,041 Mexico-exclusive SKUs** (41.41% of 2120 portfolio) do NOT exist in 2012.
- These are **not just duplicates of global items with Mexico-specific variants**; they are genuinely unshared with the global plan.
- **83.2% are D-category** (low-value, low-priority), suggesting they are **regional components, local-sourced materials, or market-specific parts**.
- Examples observed: "DRIVER RIM", "RAM", "GEAR, RING" — mechanical subcomponents, likely sourced from local/regional suppliers rather than global product hierarchy.

#### Data-Model Implication:
- Mexico's supply plan is **not a filtered subset of the global plan**; it is a **distinct portfolio with its own sourcing network**.
- The 41% unique-SKU rate implies:
  - **Local/regional suppliers** (Mexico or nearby Central America) provide items not in 2012's global supply chain.
  - **Intercompany transfer** may occur for shared items (5,717), but 2120-only items are likely **independent procurement**.
  - **Tariffs, import restrictions, or regional customization** may drive use of Mexico-exclusive SKUs.

#### Actionable Insight:
- Audit the 4,041 Mexico-only items: are they truly regional-specific, or are they duplicates in prod_edw with different item_id? (Cross-check with items_scd1 country_of_origin if accessible.)
- Analyze cost-to-serve for 2120-only vs shared items: does regional sourcing reduce delivered cost or improve lead time?
- **Intercompany transfer risk:** if 2120's shared items (5,717) are supplied FROM 2012, pricing and SLA must be audited for margin leakage.

---

## Lower-Priority Observations (Less Distinctly 2120-Specific)

### Observation 1: 2120 Has Fewer High-Concentration Receipts
- **2012 avg receipt (when >0):** 7,978.73 units; p95: 32,400 units.
- **2120 avg receipt (when >0):** 2,104.1 units; p95: 3,000 units.
- **Implication:** 2012 has **bulk-import receipt behavior** (large shipments, infrequent); 2120 has **smaller, more frequent receipts** (just-in-time).
- **Why:** 2120 likely has shorter lead times (regional suppliers), lower inventory carrying cost, and less FX/tariff risk per shipment.
- **Status:** Not unique to 2120 — likely a **consequence of Scenarios 4–5 (leaner model)**.

### Observation 2: 2120 Alert Tier Distribution Slightly Healthier
- **2012:** 68.04% OK (Tier 0), 21.11% Escalate (Tier 3).
- **2120:** 67.20% OK, 14.16% Escalate.
- **Implication:** Mexico has 6.95% fewer escalations than Global.
- **Status:** Expected consequence of **lower variance (Scenario 3) and better inventory health (Scenario 4)**.

### Observation 3: 2120 ABC Classification Slightly Higher in A/B Categories
- **2012:** A=9.79%, B=8.52%, C=11.44%, D=70.25% of items.
- **2120:** A=11.47%, B=9.17%, C=13.76%, D=65.60% of items.
- **Implication:** Mexico has a **slightly richer portfolio of high-value items** (A/B/C = 34.4% vs 29.75% in 2012).
- **Status:** Modest difference, likely due to **smaller SKU set selecting high-turnover items**.

### Observation 4: 2120 Lower Shipment-to-Receipt Ratio
- **2012 shipped/received ratio:** 0.38 (receive 2.6× more than ship).
- **2120 shipped/received ratio:** 0.09 (receive 11× more than ship).
- **Implication:** 2120 is a **net-receiving node** (warehouse/distribution hub supplied FROM 2012 or external suppliers); 2012 is a **balanced producer/receiver**.
- **Status:** This could signal **intercompany transfer from 2012 to 2120**, but without visibility to transfer GL codes, cannot confirm. Requires **prod_edw.domain_inventory inventory_material_transaction transfer analysis** (outside scope: READ-ONLY gold table only).

---

## NOT Actually 2120-Specific (False Alarms / Explained by Org Structure)

### Non-Finding 1: Cost Profile Difference
- **2012 avg cost:** $49.23/item; **2120 avg cost:** $31.48/item.
- **Expected explanation:** 2120 has 83.2% D-category items (low-value), while 2012 has more balanced ABC mix. Cost is driven by **portfolio composition, not 2120-specific dynamics**.
- **Verdict:** Not 2120-unique; consequence of item filtering.

### Non-Finding 2: End-On-Hand Scale Difference
- **2012 avg onhand:** 1,434 units; **2120 avg onhand:** 175 units.
- **Expected explanation:** This is an **expected consequence of lower safety stock (Scenario 5)** and **smaller, Mexico-exclusive SKU set (Scenario 6)**.
- **Verdict:** Not independently unique; drives from Scenarios 5–6.

### Non-Finding 3: Rows-per-Planner Scale
- Covered in **Scenario 1**; not a false alarm, but organizational structure, not operational pattern.

---

## Summary Ranked by Distinctness & Actionability

| Rank | Scenario | Distinctness | Actionability | Priority | Type |
|------|----------|--------------|---------------|----------|------|
| 1 | Ultra-concentrated planner population (6 vs 92) | **VERY HIGH** | Knowledge concentration risk; turnover mitigation needed. | P2 | Org/Risk |
| 2 | Planned-PAB completeness 9× better (2.03% null vs 18.17%) | **VERY HIGH** | Identify 2012 data-entry gaps; replicate Mexico discipline globally. | P1 | Data Quality |
| 3 | 5× lower on-hand variance (20.71% vs 100.96%) | **VERY HIGH** | Benchmark 2120 for supply-chain tightness; investigate 2012 volatility drivers. | P2 | Ops Signal |
| 4 | 26% higher green-status inventory (62.28% vs 36.32%) | **HIGH** | Analyze 2120's faster replenishment model; scale patterns to 2012. | P1 | Inventory Health |
| 5 | 13× lower safety stock (112.88 vs 1,496.78 units/item) | **HIGH** | Validate Mexico's leanness under demand shocks; model tariff/supply scenarios. | P2 | Inventory Strategy |
| 6 | 41% unique SKUs (4,041 Mexico-exclusive items) | **HIGH** | Confirm regional sourcing vs intercompany transfer; audit cost-to-serve. | P2 | Portfolio/Sourcing |

---

## Data-Model Implications & Next Steps

### Key Findings Summary:
1. **Mexico (2120) operates a fundamentally different supply model** than Global (2012): **lean, regionally-concentrated, planner-driven, with tight demand-response cycles**.
2. **2120's tightness is enabled by:**
   - Centralized, expert planner team (2–3 key people) vs. distributed global team.
   - Regional/shorter-lead suppliers (41% unique SKUs).
   - Smaller, managed inventory buffers (13× lower safety stock).
   - Higher data completeness (planned-pab populated 9× better).
3. **2120 is NOT a scaled replica of 2012** — it is a distinct plan architecture.
4. **Risk:** Planner concentration (Miller + Ystesund = 85% of planning) creates turnover vulnerability.
5. **Opportunity:** Mexico's variance profile and inventory health metrics are model use cases for global supply-chain optimization.

### Recommendations:
1. **Protect Mexico planning continuity:** Cross-train backup planners; document decision heuristics for Miller & Ystesund.
2. **Audit 2012 planned-pab nulls:** Investigate why 18.17% of Global rows lack planned-pab. Is this data pipeline gap or legitimate no-plan items?
3. **Benchmark 2120 supply model:** Model demand-shock scenarios (e.g., +50% volume, tariff spike) to validate safety-stock adequacy given low buffers.
4. **Replicate Mexico best practices:** Analyze 2120's receipt/shipment frequency, supplier SLAs, and forecast accuracy. Can patterns apply to high-variance 2012 items?
5. **Investigate intercompany dynamics:** If 2120 is supplied by 2012 (5,717 shared items), audit transfer pricing and SLA compliance.

---

## Appendix: Query Ledger

All queries executed against `sandbox_operations.po_management.rung2_plan_vs_actual` — **READ-ONLY, no writes**.

- Query 1: Item overlap (unique, shared, 2120-only counts)
- Query 2: Planned-PAB and safety-stock null rates
- Query 3: Demand-supply shape (shipped/received ratios)
- Query 4: Alert tier distribution
- Query 5: ABC classification distribution
- Query 6: Variance patterns (onhand_variance_abs, onhand_variance_pct)
- Query 7: Planner count and coverage
- Query 8: Planner names and scope
- Query 9: Quarterly trends (sparse data; single Q as of query date)
- Query 10: Onhand status distribution
- Query 11: Cost profiles (min/max/avg/stddev)
- Query 12: Mexico-only item characteristics
- Query 13: Mexico-only vs shared ABC distribution
- Query 14: Safety stock and onhand patterns
- Query 15: Receipt concentration patterns (large imports vs frequent small receipts)

**All results exported, no derivative tables created. Local analysis only.**

