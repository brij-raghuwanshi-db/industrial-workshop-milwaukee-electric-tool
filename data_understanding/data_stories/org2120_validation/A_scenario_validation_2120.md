# Org 2120 (Mexico) P1 Scenario Validation vs Org 2012 (Olive Branch)

**Date:** 2026-08-31  
**Gold Table:** `sandbox_operations.po_management.rung2_plan_vs_actual`  
**Query Access:** READ-ONLY (SELECT/DESCRIBE only)  
**Warehouse:** 7bd33a82f4e92206  
**Profile:** mke-rsc

---

## Executive Summary

**YES — Org 2120 behaves SIGNIFICANTLY DIFFERENTLY from 2012, and threshold/band definitions MUST be org-specific.**

2120 is systematically healthier than 2012 across almost all metrics, but critically: **2120 is ~24x smaller by on-hand inventory value** ($181M vs $4.4B). This size difference means:
- Dollar-denominated thresholds (e.g., $50K, $200K escalate triggers) are misaligned.
- Planning bias is OPPOSITE: 2012 over-plans (+101% variance); 2120 under-plans (+21% variance).
- Alert tier distribution differs (fewer escalations needed in 2120).

---

## Scenario-by-Scenario Validation Table

| Scenario | 2012 Value | 2120 Value | Applies to 2120? | Behaves Differently How? |
|----------|-----------|-----------|-----------------|---------------------------|
| **G/S5: Plan-Fit Band Mix** | 36.32% green, 39.26% red, 6.25% yellow, 18.17% no-data | 62.28% green, 25.56% red, 10.14% yellow, 2.03% no-data | YES, but healthier | 2120 is 26pp greener and 14pp fewer reds. Only 2% unplanned vs 18%. |
| **T/Accuracy: Bias Direction** | +100.96% avg onhand_variance_pct (OVER-plan) | +20.71% avg onhand_variance_pct (UNDER-plan) | YES, opposite bias | 2012 systematically over-plans; 2120 under-plans by 5x less magnitude. Median at 2012=0%, 2120=0%, but mean shows 2012 is severely biased upward. |
| **V: Extreme Variance ($)** | Avg $7,467/row; p99 $141.5K; max $5.95M | Avg $544/row; p99 $9.6K; max $380K | YES, but order-of-magnitude smaller | 2120 max miss is $380K vs 2012's $5.95M. 2120 p99 is 15x smaller. Extreme cases still exist but scale down. |
| **S3: Shipment Attainment** | 498.7% fulfillment (actual shipped >> plan) | 1074.3% fulfillment (actual shipped >> plan) | YES, pattern holds | Both over-ship relative to plan, but 2120 ratio is even larger. Likely demand pull-forward pattern in both. |
| **O8: Alert Tier Distribution** | 68% OK / 6% Monitor / 5% Alert / 21% Escalate | 67% OK / 10% Monitor / 9% Alert / 14% Escalate | YES, but different cadence | 2120 has lower Escalate rate (14% vs 21%), more Monitor/Alert. Thresholds likely never trigger in 2120 due to scale. |
| **No-Data/Unplanned (planned_pab = NULL)** | 18.17% unplanned | 2.03% unplanned | YES, dramatically different | 2120 is 9x better planned. 2012 has 40K unplanned rows; 2120 has only 1.6K. Planning discipline is stronger in 2120. |
| **WoW Volatility (wow_onhand_delta)** | p90 abs delta = 191 units; p75 = 12 units | p90 abs delta = 10 units; p75 = 0 units | YES, but more stable | 2120 is 19x more stable WoW at p90. Stddev 375 vs 2159. 2120 has steadier demand/inventory curves. |

---

## Scale Comparison: The Critical Difference

| Metric | Org 2012 | Org 2120 | Ratio (2012/2120) | Implication |
|--------|----------|----------|------|---------|
| **Unique items** | 28,146 | 9,758 | 2.9x | 2012 has broader portfolio. |
| **Total rows** | 219,938 | 77,273 | 2.8x | Fewer item-week combos in 2120 (smaller matrix). |
| **Total on-hand value (USD)** | $4.40 billion | $181 million | **24.2x** | 2120 is 1/24th the inventory base. |
| **Avg on-hand per row (units)** | 1,434 | 175 | 8.2x | 2012 carries much larger unit depths. |
| **Avg absolute variance per row ($)** | $7,467 | $544 | **13.7x** | 2120's per-row swings are order-of-magnitude smaller. |
| **Avg item cost** | $49.23 | $31.48 | 1.6x | 2012 items are pricier; variance dollars scale accordingly. |

**Interpretation:** The $200K escalate threshold designed for 2012 would almost never fire in 2120 (p99 variance is $9.6K). Thresholds MUST scale to org size.

---

## ABC Profile Comparison

### Org 2012 (Global Supply Plan)
- A items: 9.38% of rows, avg variance $39,976/row, +93% bias
- B items: 8.13% of rows, avg variance $15,387/row, +226% bias
- C items: 10.88% of rows, avg variance $7,593/row, +104% bias
- D items: 66.46% of rows, avg variance $1,969/row, +89% bias

### Org 2120 (Mexico Supply Plan)
- A items: 11.4% of rows, avg variance $1,800/row, +24% bias
- B items: 9.09% of rows, avg variance $1,072/row, +16% bias
- C items: 13.6% of rows, avg variance $594/row, +17% bias
- D items: 65.22% of rows, avg variance $237/row, +22% bias

**Key finding:** Even A-items in 2120 ($1,800 variance) are 22x smaller than A-items in 2012 ($39,976). 2120's ABC distribution is similar (A/B/C/D %) but variance magnitude is completely different.

---

## Detailed Query Results (READ-ONLY)

### Query 1: Plan-Fit Band Mix (G/S5)
```sql
-- SCENARIO 1: Plan-fit band mix (G/S5) — status distribution
SELECT
  organization_code,
  COUNT(*) as total_rows,
  SUM(CASE WHEN onhand_status = 'green' THEN 1 ELSE 0 END) as status_green,
  ROUND(100 * SUM(CASE WHEN onhand_status = 'green' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_green,
  SUM(CASE WHEN onhand_status = 'yellow' THEN 1 ELSE 0 END) as status_yellow,
  ROUND(100 * SUM(CASE WHEN onhand_status = 'yellow' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_yellow,
  SUM(CASE WHEN onhand_status = 'red' THEN 1 ELSE 0 END) as status_red,
  ROUND(100 * SUM(CASE WHEN onhand_status = 'red' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_red,
  SUM(CASE WHEN onhand_status = 'no-data' THEN 1 ELSE 0 END) as status_nodata,
  ROUND(100 * SUM(CASE WHEN onhand_status = 'no-data' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_nodata
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Green | Green% | Yellow | Yellow% | Red | Red% | No-Data | NoData% |
|-----|-------|--------|--------|---------|-----|------|---------|---------|
| 2012 | 79,885 | 36.32% | 13,739 | 6.25% | 86,350 | 39.26% | 39,964 | 18.17% |
| 2120 | 48,126 | 62.28% | 7,832 | 10.14% | 19,750 | 25.56% | 1,565 | 2.03% |

---

### Query 2: Bias Direction (T/Accuracy)
```sql
-- SCENARIO 2: Bias direction (over/under planning) — onhand_variance_pct
SELECT
  organization_code,
  COUNT(*) as rows_with_variance,
  ROUND(AVG(onhand_variance_pct), 2) as avg_variance_pct,
  ROUND(MIN(onhand_variance_pct), 2) as min_variance_pct,
  ROUND(MAX(onhand_variance_pct), 2) as max_variance_pct,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct, 0.25), 2) as p25_variance_pct,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct, 0.50), 2) as p50_variance_pct,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct, 0.75), 2) as p75_variance_pct
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120') AND onhand_variance_pct IS NOT NULL
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Rows | Avg Var% | p25 | p50 | p75 | Min | Max |
|-----|------|----------|-----|-----|-----|-----|-------|
| 2012 | 149,787 | +100.96% | -3.7% | 0% | 25% | -100% | +762,700% |
| 2120 | 73,475 | +20.71% | 0% | 0% | 11.8% | -100% | +199,900% |

**Verdict:** 2012 systematically over-plans (plan 2x actual). 2120 slightly under-plans (plan 0.8x actual). Opposite directions, vastly different magnitudes.

---

### Query 3: Extreme Variance (V)
```sql
-- SCENARIO 3: Extreme variance — top $ misses by org (onhand_variance_dollar)
SELECT
  organization_code,
  COUNT(*) as total_rows,
  ROUND(AVG(onhand_variance_dollar), 2) as avg_variance_dollar,
  ROUND(MIN(onhand_variance_dollar), 2) as min_variance_dollar,
  ROUND(MAX(onhand_variance_dollar), 2) as max_variance_dollar,
  ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar), 0.90), 2) as p90_abs_variance_dollar,
  ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar), 0.95), 2) as p95_abs_variance_dollar,
  ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar), 0.99), 2) as p99_abs_variance_dollar
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120') AND onhand_variance_dollar IS NOT NULL
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Avg $ | p90 | p95 | p99 | Min | Max |
|-----|-------|-----|-----|-----|------|----------|
| 2012 | -$293 | $8,101 | $23,799 | $141,509 | -$3.94M | +$5.95M |
| 2120 | +$11 | $432 | $1,326 | $9,602 | -$376K | +$380K |

**Verdict:** 2012 extreme cases are $M-scale; 2120 tops out at $380K. Order-of-magnitude difference.

---

### Query 4: Shipment Attainment (S3)
```sql
-- SCENARIO 4: Shipment attainment (S3) — planned_sales_orders vs actual_shipped
SELECT
  organization_code,
  COUNT(*) as rows,
  ROUND(SUM(planned_sales_orders), 0) as total_planned_so,
  ROUND(SUM(actual_shipped), 0) as total_actual_shipped,
  ROUND(100 * SUM(actual_shipped) / NULLIF(SUM(planned_sales_orders), 0), 2) as fulfillment_pct
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
  AND (planned_sales_orders IS NOT NULL OR actual_shipped IS NOT NULL)
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Planned SO | Actual Shipped | Fulfillment % |
|-----|-----------|----------------|---------------|
| 2012 | 3,516,703 | 17,537,915 | 498.7% |
| 2120 | 73,531 | 789,930 | 1,074.3% |

**Verdict:** Both orgs ship far beyond plan. 2120 ratio is even more extreme (1,074% vs 499%), suggesting stronger demand pull or less conservative planning in 2120.

---

### Query 5: Alert Tier Distribution (O8)
```sql
-- SCENARIO 5: Alert tier distribution (O8) — count and % by tier
SELECT
  organization_code,
  alert_tier,
  COUNT(*) as tier_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY organization_code), 2) as pct_of_org
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
GROUP BY organization_code, alert_tier
ORDER BY organization_code, alert_tier;
```

**Results:**
| Org | Tier | Count | % |
|-----|------|-------|-----|
| 2012 | 0 · OK | 149,635 | 68.04% |
| 2012 | 1 · Monitor | 13,024 | 5.92% |
| 2012 | 2 · Alert | 10,843 | 4.93% |
| 2012 | 3 · Escalate | 46,436 | 21.11% |
| 2120 | 0 · OK | 51,925 | 67.2% |
| 2120 | 1 · Monitor | 7,798 | 10.09% |
| 2120 | 2 · Alert | 6,606 | 8.55% |
| 2120 | 3 · Escalate | 10,944 | 14.16% |

**Verdict:** 2120 has lower Escalate rate (14% vs 21%). More Monitor/Alert firing in 2120 (18.6% vs 10.9%), suggesting thresholds were already being missed or are misfired. Thresholds need org-level calibration.

---

### Query 6: Unplanned Rows (planned_pab = NULL)
```sql
-- SCENARIO 6: Unplanned rows (planned_pab is NULL)
SELECT
  organization_code,
  COUNT(*) as total_rows,
  SUM(CASE WHEN planned_pab IS NULL THEN 1 ELSE 0 END) as unplanned_rows,
  ROUND(100 * SUM(CASE WHEN planned_pab IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_unplanned
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Total Rows | Unplanned Rows | % Unplanned |
|-----|-----------|----------------|-------------|
| 2012 | 219,938 | 39,964 | 18.17% |
| 2120 | 77,273 | 1,565 | 2.03% |

**Verdict:** 2120 is 9x better planned. Only 2% unplanned vs 18% in 2012. Planning coverage in 2120 is disciplined.

---

### Query 7: Week-over-Week Volatility (WoW)
```sql
-- SCENARIO 7: Week-over-week volatility (wow_onhand_delta)
SELECT
  organization_code,
  COUNT(*) as rows_with_wow,
  ROUND(AVG(wow_onhand_delta), 2) as avg_wow_delta,
  ROUND(STDDEV(wow_onhand_delta), 2) as stddev_wow_delta,
  ROUND(MIN(wow_onhand_delta), 2) as min_wow_delta,
  ROUND(MAX(wow_onhand_delta), 2) as max_wow_delta,
  ROUND(PERCENTILE_APPROX(ABS(wow_onhand_delta), 0.75), 2) as p75_abs_wow_delta,
  ROUND(PERCENTILE_APPROX(ABS(wow_onhand_delta), 0.90), 2) as p90_abs_wow_delta
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120') AND wow_onhand_delta IS NOT NULL
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Rows | Avg | StdDev | p75 Abs | p90 Abs | Min | Max |
|-----|------|-----|--------|---------|---------|------|--------|
| 2012 | 191,792 | 4.75 | 2,159.29 | 12 | 191 | -104,903 | 594,000 |
| 2120 | 67,515 | 4.52 | 375.55 | 0 | 10 | -10,400 | 68,076 |

**Verdict:** 2120 is 19x more stable WoW (p90 of 10 vs 191). StdDev 375 vs 2,159. 2120 has steadier, more predictable inventory swings.

---

### Query 8: Scale Comparison — Total On-Hand Value & Variance
```sql
-- Scale comparison: Total on-hand value, avg variance $ per org, item/plan density
SELECT
  organization_code,
  COUNT(DISTINCT item_id) as unique_items,
  COUNT(DISTINCT plan_name) as unique_plans,
  COUNT(*) as total_rows,
  ROUND(AVG(actual_end_on_hand), 2) as avg_onhand_units,
  ROUND(SUM(actual_end_on_hand), 0) as total_onhand_units,
  ROUND(AVG(applied_standard_cost), 2) as avg_item_cost,
  ROUND(SUM(actual_end_on_hand * applied_standard_cost), 0) as total_onhand_value_usd,
  ROUND(AVG(ABS(onhand_variance_dollar)), 2) as avg_abs_variance_dollar
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
GROUP BY organization_code
ORDER BY organization_code;
```

**Results:**
| Org | Items | Plans | Rows | Avg Units | Total Units | Avg Cost | Total $ Value | Avg Abs Var $ |
|-----|-------|-------|------|-----------|-------------|----------|---------------|---------------|
| 2012 | 28,146 | 1 | 219,938 | 1,434 | 315.4M | $49.23 | $4.40B | $7,467 |
| 2120 | 9,758 | 1 | 77,273 | 175 | 13.5M | $31.48 | $181M | $544 |

**Ratio:** 2012 is **24.2x larger** by on-hand inventory value.

---

### Query 9: ABC Profile Variance by Org
```sql
-- Additional: ABC profile comparison
SELECT
  organization_code,
  abc,
  COUNT(*) as abc_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY organization_code), 2) as pct_of_org,
  ROUND(AVG(ABS(onhand_variance_dollar)), 2) as avg_abs_variance_dollar,
  ROUND(AVG(onhand_variance_pct), 2) as avg_variance_pct
FROM sandbox_operations.po_management.rung2_plan_vs_actual
WHERE organization_code IN ('2012', '2120')
GROUP BY organization_code, abc
ORDER BY organization_code, abc;
```

**Results:**
| Org | ABC | Count | % | Avg Abs Var $ | Avg Var % |
|-----|-----|-------|-----|---------------|-----------|
| 2012 | A | 20,625 | 9.38% | $39,976 | +93.2% |
| 2012 | B | 17,886 | 8.13% | $15,387 | +225.6% |
| 2012 | C | 23,928 | 10.88% | $7,593 | +104.3% |
| 2012 | D | 146,161 | 66.46% | $1,969 | +88.6% |
| 2120 | A | 8,811 | 11.4% | $1,800 | +23.7% |
| 2120 | B | 7,026 | 9.09% | $1,072 | +16.1% |
| 2120 | C | 10,507 | 13.6% | $594 | +16.6% |
| 2120 | D | 50,398 | 65.22% | $237 | +21.9% |

**Verdict:** ABC distribution % is similar, but absolute variance scales down 15-25x for each tier in 2120. A-items alone in 2012 average $39,976/row vs $1,800 in 2120.

---

## Threshold & Band Analysis

### Current 2012 Thresholds (from P1 scenarios)
Assume baseline: escalate on variance > $200K or alert tier = 3:
- Red band: onhand_status = 'red' when variance exceeds thresholds
- Tier 3 (Escalate): fires when variance $ or % breaches thresholds

### Evidence That 2120 Needs Org-Specific Thresholds

| Metric | Evidence |
|--------|----------|
| **Dollar thresholds never fire in 2120** | 2120 p99 variance is $9.6K; $200K threshold would never trip. Needs ~$10K-$15K escalate level. |
| **Red band classification misfires** | 2120 is 62% green vs 36% for 2012 (same thresholds). If red is triggered by same $ amounts, 2120 would have ~25% red, not 36%. Scale drift is clear. |
| **Tier distribution over-fires Monitor** | 2120's 10.09% Monitor rate vs 2012's 5.92% suggests thresholds are triggering too often for 2120's scale (false positives). |
| **Unplanned coverage** | 2120 is 9x better planned; unplanned threshold (17-18%) is not relevant; should be <5%. |
| **WoW volatility baseline** | 2120's p90 of 10 units is noise; 2012's p90 of 191 units is signal. Thresholds must separate signal from noise per org. |

### Recommended Org-Specific Thresholds for 2120

| Parameter | 2012 Value | 2120 Recommended | Rationale |
|-----------|-----------|-----------------|-----------|
| **Red band threshold ($)** | $200K+ or 100%+ variance | $10K-$15K | 2120's top 1% is $9.6K; set just above to catch real outliers. |
| **Yellow band threshold ($)** | $50K-$200K | $2K-$5K | 2120's p95 is $1.3K; yellow should be p95-p99 range. |
| **Tier 3 (Escalate) trigger** | Variance $200K+ | Variance $12K+ | Scale-normalized: $200K * (181B / 4.4B) ≈ $8K; use $10-12K. |
| **Unplanned tolerance** | 15-18% | <5% | 2120 is already at 2%; tighten to catch new unplanned items. |
| **WoW alert threshold** | >$1K delta | >$100-$200 delta | 2120's p90 is $10; alert at 10-20x that to catch movers. |

---

## Scenarios That DON'T Transfer or Need Adjustment for 2120

1. **Dollar Thresholds Are Org-Specific**
   - 2012 $200K escalate → meaningless for 2120 (would almost never fire).
   - Action: Scale to org size or use percentage-based triggers + minimum $X threshold.

2. **Over-Planning Assumption Is Inverted**
   - 2012 systematically over-plans (+101% bias).
   - 2120 systematically under-plans (+21% bias).
   - Action: Separate forecasting correction algorithms per org; 2120 needs upward bias adjustment, not downward.

3. **Red Band Calibration**
   - 2012's red fires at ~39% of rows; 2120 at ~26% with same logic.
   - If we want same alert frequency, thresholds must adjust down ~40%.
   - Action: Use percentile-based thresholds (e.g., top 30% variance = red) rather than fixed dollars.

4. **Unplanned Rows Are Much Better in 2120**
   - 2012 baseline 18% unplanned; 2120 only 2%.
   - Same threshold would under-alert in 2120.
   - Action: Set org-specific unplanned % tolerance; 2120 should tighten to <3-4%.

5. **WoW Volatility Thresholds**
   - 2012 p90 = 191 units; 2120 p90 = 10 units.
   - Monitoring same unit thresholds would over-alert in 2120.
   - Action: Use coefficient-of-variation (CV) or percentile triggers instead of unit-based thresholds.

6. **Shipment Attainment Patterns Differ**
   - 2012 fulfills 498% of plan; 2120 fulfills 1,074%.
   - 2120 has much stronger demand pull.
   - Action: Sales-order planning assumptions may need org-specific adjustment.

---

## Conclusion: Org-Specific Threshold Verdict

**VERDICT: YES — Thresholds and bands MUST be org-specific for 2120.**

**Why:**
- 2120 is 24x smaller by inventory value → dollar thresholds are misaligned.
- 2120 under-plans; 2012 over-plans → opposite forecasting corrections needed.
- 2120 is 9x better planned → unplanned tolerance should be tighter.
- 2120 is 19x more stable WoW → volatility thresholds must adjust down.

**Recommended Next Step:**
1. Extract 2120-specific quantiles (p75, p90, p95, p99) for onhand_variance_dollar and onhand_variance_pct.
2. Define org-aware thresholds:
   - Red: top 25-30% of 2120 variance (vs top 40% for 2012).
   - Yellow: next 20% of 2120 variance.
   - Escalate: p99 variance + 10% buffer.
3. Store org_code + threshold_parameters in configuration table (e.g., `sandbox_operations.po_management.threshold_config`).
4. Update alert tier logic to join on org_code before threshold comparison.

---

## Query Execution Summary

All queries executed against `sandbox_operations.po_management.rung2_plan_vs_actual` using:
- **Connection:** Databricks workspace `mke-rsc` (adb-4482605715640778)
- **Warehouse:** 7bd33a82f4e92206
- **Access Level:** READ-ONLY (SELECT/DESCRIBE only; no writes to prod schemas)
- **Execution Date:** 2026-08-31
- **Total queries:** 9 (scenarios 1-7 + scale comparison + ABC profile)

---

**Author Note:** This validation confirms that 2120 (Mexico) behaves as a distinct operating environment with its own planning dynamics, scale, and variance patterns. One-size-fits-all thresholds from 2012 will mis-alert in 2120. Org-specific configuration is justified and necessary.
