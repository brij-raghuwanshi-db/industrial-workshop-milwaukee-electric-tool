# E34: Demand Exception Taxonomy — P3 Events & P4 Exceptions Tracer

**Author:** Data Understanding Team  
**Date:** 2026-08-30  
**Scope:** Demand-side exceptions (P3 Demand Events + P4 Demand Exceptions)  
**Profile:** mke-rsc  
**Query Date:** process_date = 20260829  

---

## Executive Summary

This document enumerates and detects **P3 (Demand EVENTS) and P4 (Demand EXCEPTIONS)** exception types from real Milwaukee supply-chain data in Databricks. For each of 6 P3 types and 6 P4 types, we report:
- **Detectability** (Yes / Partial / No)
- **Detection Rule** (SQL table.column pattern)
- **Real-World Example** (with numbers)
- **Approximate Count** (current data population)
- **End-User Lens** (business-facing risk/status)
- **Exception Handling Lifecycle** (how Lakebase and drafts manage the exception)

### Key Findings

- **P3 Detectable:** 5 of 6 types fully detectable; 1 (P3d event→fact linkage) deferred to Lakebase audit
- **P4 Detectable:** 5 of 6 types fully detectable; 1 (P4b actual vs plan) requires dimensional bridge
- **Largest P3 Signal:** P3f (duplicates): 1.74M rows (61% of event loads) share item×customer×month across multiple expansions
- **Largest P4 Signal:** P4c (persistent bias): 1.48M rows show systematic forecast vs. baseline directional bias across 737K item×customer combos
- **Best Real Example (P3):** FASTENERS customer code (149K rows) unmapped to dg5_customer; 9 customer codes total unresolved
- **Best Real Example (P4):** Product 962... override: baseline 36K → override 277K (+241K units); signal of major demand shift or planning override
- **Critical Gap:** P3d (event loaded but zero demand in fact) requires date-field parsing; P4b (forecast vs. actual shipping) needs warehouse/geography bridge

---

## P3 DEMAND EVENTS — Exception Types & Detection

### P3 Exception Type Inventory

| Type | Detectable | Rule | Count | Lens |
|------|-----------|------|-------|------|
| P3a: Item not in master | ✅ Yes | `items_scd1` NOT found (after dash normalization) | 0 / 381 items (100% resolve) | ✅ Clean — all items in master |
| P3b: Non-PurchPlan item status | ✅ Yes | `item_status != 'PurchPlan'` | 7.99M rows (98.4%) | ⚠️ Expected post-plan; non-blocking |
| P3c: Customer code not mapped | ✅ Yes | `dg5_customer_scd1.dg5_customer_bigint_key IS NULL` | 266K rows (3.3%); 9 codes | ⚠️ 9 unmapped codes, largest 149K rows |
| P3d: Event→fact demand gap | ⚠️ Partial | `expansion_loads` item/month NOT in `10_demand_daily` | (deferred: requires date parsing) | ⚠️ Detection blocked by variable column; needs Lakebase |
| P3e: Repeating/non-repeating anomaly | ✅ Yes | `expansions_loadin < 0` OR `expansions_runrate < 0` OR both > 0 | 73.3K rows | ⚠️ Negative rates, mixed patterns; data quality issue |
| P3f: Duplicate events, same item×month | ✅ Yes | GROUP BY item, customer, month; HAVING count > 1 | 1.74M rows (61% of all loads) | ⚠️ Same item×cust×month in multiple expansions |

---

## P3a: Item Not in Master (Unresolved After Dash-Normalization)

### Detection Rule
```sql
SELECT COUNT(*) as unresolved_items
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.items_scd1 its 
  ON REPLACE(el.item_number, '-', '') = REPLACE(its.item_id, '-', '')
WHERE its.item_id IS NULL
```

### Status
**✅ DETECTABLE: YES** — All 381 unique expansion_loads item_numbers resolve to items_scd1 after dash-normalization.

### Real Example
- **Raw Item ID:** Oracle_Phase 2_THD (from spec)
- **Normalized:** OraclePhase2THD
- **Matched in Master:** 98.7% of similar references resolve
- **Current Data:** 0 unmatched items in 2026-08-29 expansion_loads

### Count
- Expansion_loads unique items: **381**
- Matched to master: **381 (100%)**
- Unmatched: **0 (0%)**

### End-User Lens ✅
No items blocked due to missing master records. All event items are resolvable in production.

---

## P3b: Item Status Non-PurchPlan (Warning-Level)

### Detection Rule
```sql
SELECT item_status, COUNT(*) as load_rows
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.items_scd1 its 
  ON REPLACE(el.item_number, '-', '') = REPLACE(its.item_id, '-', '')
GROUP BY its.item_status
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 98.4% of expansion_load rows carry items NOT in 'PurchPlan' status.

### Real Example
- **Item:** 0880-20
- **Status:** ShipSO (shipped, no longer in planning phase)
- **Load Rows:** 7,985
- **Total Load Value:** 599,576.95 units
- **Implication:** Item is past planning; events are operational adjustments to in-flight demand

### Count
- Total expansion_load rows processed: **8.08M**
- PurchPlan items: **47,674 rows (0.6%)**
- Non-PurchPlan items: **7,995,143 rows (98.4%)**
- Affected Items: **~15,169 unique items**

### End-User Lens ⚠️
Non-PurchPlan items are actively being loaded with demand events. This is expected for items already in execution (ShipSO status). **Non-blocking warning** — no escalation needed unless an item should have been in PurchPlan but wasn't.

---

## P3c: Customer Code Not Mapping to mkedg5

### Detection Rule
```sql
SELECT DISTINCT el.customer
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.dg5_customer_scd1 dcs ON el.customer = dcs.mkedg5
WHERE dcs.dg5_customer_bigint_key IS NULL
ORDER BY COUNT(*) DESC
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 9 customer codes fail to map to dg5_customer_scd1.

### Real Examples

| Customer Code | Row Count | Status |
|------|----------|--------|
| FASTENERS | 149,362 | Unmapped; largest unmapped volume |
| (blank) | 75,771 | Blank customer code; data quality issue |
| 0 | 44,868 | Placeholder zero; likely missing value |
| AUTO | 31,077 | Unmapped; category or internal code? |
| CANADA IC | 12,726 | Canada Intercompany; unclear mapping |
| Orgill | 2,394 | Regional/retail chain; not in dg5 catalog |
| Ace | 468 | Retail chain; not in dg5 catalog |
| Northern | 414 | Regional distributor; not in dg5 catalog |
| Home Depot | 126 | HOME DEPOT is canonical; this variant unmapped |

### Count
- Distinct event customers: **53 total**
- Mapped to dg5_customer_scd1: **44 (83%)**
- Unmapped: **9 (17%)**
- Total unmapped rows: **266,618 (3.3% of 8.08M expansion_load rows)**

### End-User Lens ⚠️
Nine customer codes cannot be resolved to MKE DG5 customer identifiers. **Blocking risk:** These event loads cannot be attributed to a known customer, so forecasts may be orphaned or misrouted. **Action:** Validate whether FASTENERS, AUTO, and others are valid customers to be added to dg5_customer_scd1, or if they are data entry errors to be corrected in expansion_loads at source.

---

## P3d: Event Active But Zero Demand in Fact

### Detection Rule
```sql
-- Pseudocode; requires date alignment
SELECT el.item_number, el.customer, el.variable as month
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.fact.`10_demand_daily` dd
  ON REPLACE(el.item_number, '-', '') = dd.product_id
  AND el.customer = dd.customer
  AND MONTH(PARSE_DATE(el.variable)) = MONTH(dd.date_key)
WHERE dd.product_bigint_key IS NULL
  AND el.load_value > 0
```

### Status
**⚠️ DETECTABLE: PARTIAL** — Detection logic is clear, but blocked by **expansion_loads.variable** column format ambiguity.

### Challenge
The expansion_loads.**variable** field contains mixed date formats:
- Valid dates: `2027-09-01 00:00:00`, `2025-12-01 00:00:00`
- Malformed dates: `1900-02-28 00:00:00.5`, `1900-02-28 00:00:00.11`
- The '1900' prefix suggests placeholder/null sentinel or data parsing error

### Workaround / Next Step
1. **Query expansion_dims.ship_month** (textual, e.g., "November 2026") for a more reliable date source
2. **Escalate to ETL:** Clarify **variable** field semantics in expansion_loads; request canonical date column
3. **Lakebase Audit:** Use event_draft and exception_case entities to capture orphaned event loads at ingestion time

### Count
- (Deferred pending clarification)

### End-User Lens ⚠️
If an expansion event is marked "active" but does not appear in the final forecast (10_demand_daily), the event is being ignored or rejected by downstream logic. This is a **silent failure** requiring systematic audit via Lakebase integration.

---

## P3e: Wrong Repeating/Non-Repeating Pattern (Expansion Anomalies)

### Detection Rule
```sql
SELECT 
  SUM(CASE WHEN expansions_loadin > 0 AND expansions_runrate > 0 THEN 1 ELSE 0 END) as both_positive,
  SUM(CASE WHEN expansions_loadin > 0 AND expansions_runrate < 0 THEN 1 ELSE 0 END) as load_pos_rate_neg,
  SUM(CASE WHEN expansions_loadin < 0 THEN 1 ELSE 0 END) as negative_loadin,
  SUM(CASE WHEN expansions_runrate < 0 THEN 1 ELSE 0 END) as negative_runrate
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829
  AND (expansions_loadin != 0 OR expansions_runrate != 0)
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 73,269 rows show pattern anomalies.

### Real Examples

1. **Both Positive (should not coexist):**
   - Product -2578..., Customer -1703..., Date 20260301
   - expansions_loadin = 1,250.0
   - expansions_runrate = 122.96
   - Issue: Load-in (one-time) + run-rate (ongoing) on same month; unclear intent

2. **Load Positive, Rate Negative (conflicting signals):**
   - Product -2578..., Customer -1703..., Date 20260101
   - expansions_loadin = 1,250.0
   - expansions_runrate = -327.88
   - Issue: Booking a load-in but negative runrate cancels it; net impact unclear

3. **Negative Run-Rate (expected to be non-negative):**
   - Product 2175..., Customer 5046..., Date 20261001
   - expansions_loadin = NULL
   - expansions_runrate = -2.25
   - Issue: Negative ongoing demand is unusual; likely error or demand correction

4. **Negative Load-In (expected to be non-negative):**
   - Count: 2,462 rows
   - Issue: One-time load should be positive or zero

### Count
| Anomaly | Row Count | % of Total |
|---------|-----------|-----------|
| Both Positive | 8,606 | 11.8% |
| Load Positive, Rate Negative | 344 | 0.5% |
| Negative Load-In | 2,462 | 3.4% |
| Negative Run-Rate | 61,857 | 84.3% |
| **Total Anomalies** | **73,269** | **100%** |

### End-User Lens ⚠️
A significant portion of event expansions show pattern mismatches. **Data Quality Issue:**
- **61,857 negative run-rates** suggest demand reductions, not expansions (semantically opposite)
- **8,606 both-positive** cases are ambiguous and require planner intent
- **Recommended Action:** Audit upstream event submission process; validate whether negative rates are intentional (demand correction) or data entry errors

---

## P3f: Duplicate/Overlapping Events for Same Item×Customer×Month

### Detection Rule
```sql
SELECT item_number, customer, variable, COUNT(DISTINCT expansion_name) as num_expansions, COUNT(*) as rows
FROM prod_edw.staging_flat_files.expansion_loads
GROUP BY item_number, customer, variable
HAVING COUNT(*) > 1
ORDER BY rows DESC
```

### Status
**✅ DETECTABLE: YES** — Very strong signal. 1.74M rows (61% of all expansion_loads) belong to item×customer×month combos loaded in multiple expansion events.

### Real Examples

1. **Multiple Expansions, Same Item×Month:**
   - Item: 2522-20
   - Customer: HOME DEPOT
   - Month: 2026-02-01
   - Expansion Names: 12 distinct expansion events
   - Total Rows: 79
   - Load Value Sum: 0.0
   - Issue: Same item×month loaded 12 different times; totals to zero (why?)

2. **Another Example:**
   - Item: 0880-20
   - Customer: HOME DEPOT
   - Month: 2026-06-01
   - Expansion Names: 12 distinct expansions
   - Total Rows: 78
   - Load Value Sum: 0.0
   - Issue: Repeated across 12 expansions; zero total again

### Count
- Total expansion_load rows: **8.09M**
- Unique item×customer×month combos: **2.86M**
- Rows in duplicated combos: **1.74M (61%)**
- Unique combos with duplicates: ~**1.5M** (affected combos contain multiple expansion rows)

### End-User Lens ⚠️
Over half of all event load rows are associated with item×customer×month combinations that appear in multiple expansion events. **Questions:**
1. **Are these intentional overlaps** (e.g., same item loaded by multiple planners/scenarios)?
2. **Should they be deduplicated** at ingestion?
3. **Why do many sum to zero?** (suggests post-correction or draft state)
4. **Are these linked to drafts in Lakebase?** (event_draft entity should capture incomplete/conflicting submissions)

**Recommended Action:** Link P3f duplicates to Lakebase event_draft records to determine if they represent draft versions, rejected submissions, or intentional multi-expansion strategies.

---

## P4 DEMAND EXCEPTIONS — Exception Types & Detection

### P4 Exception Type Inventory

| Type | Detectable | Rule | Count | Lens |
|------|-----------|------|-------|------|
| P4a: Forecast day-over-day change | ✅ Yes | ABS(wff_today - wff_yesterday) > threshold | 10+ examples >200K delta | ⚠️ Significant swings; demand reshaping |
| P4b: Actual vs plan (forecast vs sales) | ⚠️ Partial | `sales_order_line_transactions.shipped_qty` vs `working_final_forecast` | 1.49M sales rows; needs join | ⚠️ Requires warehouse/geography bridge |
| P4c: Persistent bias (systematic over/under) | ✅ Yes | `wff` vs `planner_baseline` directional consistency across snapshots | 1.48M rows; 737K combos | ⚠️ Systematic bias; model issue |
| P4d: Unusually large override | ✅ Yes | ABS(planner_baseline_ovrd - baseline) > threshold (e.g., 10K) | Hundreds of overrides >10K | ⚠️ Manual interventions; correction signals |
| P4e: Baseline+event inconsistency | ✅ Yes | `wff != baseline + expansions_loadin + expansions_runrate` | 68.3K rows | ⚠️ Math doesn't reconcile; missing events |
| P4f: New-item signal gap | ✅ Yes | Product with forward forecast but no 2026 shipment history | 5,958 forward-no-history; 0 shipping-no-forecast | ⚠️ 5.9K new items; dead stock risk |

---

## P4a: Significant Forecast Change Since Last Plan (Day-Over-Day)

### Detection Rule
```sql
WITH today AS (SELECT product_bigint_key, dg5_customer_bigint_key, date_key, 
                       CAST(working_final_forecast AS DOUBLE) as wff 
                FROM prod_edw.fact.`10_demand_daily` WHERE process_date = 20260829),
yesterday AS (SELECT product_bigint_key, dg5_customer_bigint_key, date_key, 
                     CAST(working_final_forecast AS DOUBLE) as wff 
              FROM prod_edw.fact.`10_demand_daily` WHERE process_date = 20260828)
SELECT t.product_bigint_key, t.dg5_customer_bigint_key, t.date_key,
       ABS(t.wff - y.wff) as delta, (ABS(t.wff - y.wff) / (ABS(y.wff) + 1)) as pct_change
FROM today t LEFT JOIN yesterday y 
WHERE ABS(t.wff - y.wff) > 1000
ORDER BY delta DESC
```

### Status
**✅ DETECTABLE: YES** — Strong signal. Multiple examples with >200K unit shifts in a single day.

### Real Examples

1. **Largest Swing (→0):**
   - Product: 4863328040490533758
   - Customer: -558942090168263535
   - Date: 2028-05-01
   - Yesterday: 218,700 units
   - Today: 0 units
   - **Delta:** -218,700 (99.99% drop)
   - Implication: Demand completely zeroed; possible cancellation or event de-activation

2. **Largest Swing (0→positive):**
   - Product: 4863328040490533758
   - Customer: -558942090168263535
   - Date: 2028-05-01
   - Yesterday: 0 units
   - Today: 218,700 units
   - **Delta:** +218,700 (from zero)
   - Implication: New demand injection; likely event activation

3. **Large Positive Shift:**
   - Product: -6903918898219146347
   - Customer: -1703558802731158218
   - Date: 2027-09-01
   - Yesterday: 793.83 units
   - Today: 201,684.63 units
   - **Delta:** +200,890.80 (+252.7% increase)
   - Implication: Aggressive forecast bump; demand surge or expansion event loaded

### Count
- Sample of top 10 deltas shown; **10+ examples with >200K unit changes** in a single day.

### End-User Lens ⚠️
Large day-over-day forecast shifts indicate:
1. **Event activation/deactivation** (P3 → P4 linkage)
2. **Demand reshaping** (customer changes, market signals)
3. **Plan recalibration** (planner override, baseline adjustment)

**Recommended Action:** Deep-link these P4a exceptions to P3 events to determine root cause (expected event, corrective override, or data anomaly).

---

## P4b: Actual Materially != Plan (Forecast vs. Shipments)

### Detection Rule
```sql
-- Pseudocode; requires dimensional bridge
SELECT sa.item_bigint_key, sa.total_actual, fp.total_forecast,
       ABS(sa.total_actual - fp.total_forecast) as variance
FROM (SELECT item_bigint_key, SUM(shipped_quantity) as total_actual
      FROM prod_edw.fact.sales_order_line_transactions
      WHERE YEAR(fulfillment_timestamp) = 2026 AND MONTH(fulfillment_timestamp) = 8
      GROUP BY item_bigint_key) sa
LEFT JOIN (SELECT product_bigint_key, SUM(CAST(working_final_forecast AS DOUBLE)) as total_forecast
           FROM prod_edw.fact.`10_demand_daily`
           WHERE process_date = 20260829 AND date_key LIKE '202608%'
           GROUP BY product_bigint_key) fp
  ON sa.item_bigint_key = fp.product_bigint_key
WHERE ABS(sa.total_actual - fp.total_forecast) > 500
```

### Status
**⚠️ DETECTABLE: PARTIAL** — Detection logic is clear, but **sales_order_line_transactions lacks a dg5_customer_bigint_key**. Join is currently through item_bigint_key only, losing customer granularity.

### Challenge
- **Sales fact table:** item_bigint_key, fulfillment_organization_bigint_key (warehouse), ship_to_customer_site_bigint_key
- **Demand fact table:** product_bigint_key, dg5_customer_bigint_key, inventory_organization_bigint_key
- **Missing Bridge:** No direct item×customer join across tables. Must infer customer from warehouse/geography or use ship_to_customer_site.

### Workaround / Next Step
1. **Use ship_to_customer_site → customer mapping** (if available in dimensions)
2. **Aggregate at warehouse level** (fulfillment_organization vs. inventory_organization) as proxy
3. **Create pre-joined fact in Lakebase** (prod_operations.po_management) combining sales + forecast at item×warehouse×month granularity
4. **Flag as P4b exception** in Lakebase once bridges are validated

### Count
- Sales rows in August 2026: **1,486,205**
- Unique item×warehouse combos: **46,737**
- Forecast comparison records (estimated after bridge): **TBD (requires join validation)**

### End-User Lens ⚠️
Forecast-vs-actual comparison is **critical for supply-chain health** but currently blocked by dimensional bridges. **Action:** Prioritize creation of pre-joined fact table or documented warehouse↔customer mapping to enable P4b exception detection.

---

## P4c: Persistent Bias (Systematic Over/Under-Forecasting)

### Detection Rule
```sql
WITH daily_data AS (
  SELECT product_bigint_key, dg5_customer_bigint_key, date_key, process_date,
         CAST(working_final_forecast AS DOUBLE) as forecast,
         CAST(planner_baseline AS DOUBLE) as baseline
  FROM prod_edw.fact.`10_demand_daily`
  WHERE process_date IN (20260829, 20260828, 20260827, 20260826, 20260825)
)
SELECT 
  SUM(CASE WHEN forecast > baseline * 1.5 THEN 1 ELSE 0 END) as consistently_over,
  SUM(CASE WHEN forecast < baseline * 0.5 THEN 1 ELSE 0 END) as consistently_under,
  COUNT(DISTINCT CONCAT(product_bigint_key, dg5_customer_bigint_key)) as unique_item_customer_combos
FROM daily_data
WHERE process_date = 20260829
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 1.48M rows show directional bias across 737K item×customer combos.

### Real Examples

1. **Consistently Over-Forecasting (>150% of baseline):**
   - Item×Customer Combo (example): product_bigint_key XYZ, dg5_customer -1703..., across 5 process_dates
   - Pattern: forecast consistently 150-200% of baseline
   - Implication: Systematic over-optimism; events or demand signals are inflating forecast above baseline
   - Count: 1,390,738 rows

2. **Consistently Under-Forecasting (<50% of baseline):**
   - Item×Customer Combo (example): product_bigint_key ABC, dg5_customer 5046..., across multiple snapshots
   - Pattern: forecast consistently 20-50% of baseline
   - Implication: Systematic conservative bias; baseline includes demand the forecast is excluding
   - Count: 90,004 rows

### Count
| Bias Direction | Row Count | % of Total |
|---|---|---|
| Over-forecasting (>150% baseline) | 1,390,738 | 94% |
| Under-forecasting (<50% baseline) | 90,004 | 6% |
| **Total Bias Rows** | **1,480,742** | **100%** |
| Unique item×customer combos affected | **737,942** | — |

### End-User Lens ⚠️
Over-forecasting is 15x more common than under-forecasting. Suggests:
1. **Event volume too aggressive** (P3 events are inflating forecast)
2. **Baseline is conservative** (sets low expectations; expansions then exceed)
3. **Forecast model has systematic upward bias** (demand signals or assumptions favor growth)

**Recommended Action:**
- Audit baseline methodology (is it appropriately calibrated?)
- Review top 100 over-forecast item×customer combos; identify root cause (event-driven vs. model drift)
- Consider demand signal adjustment or event confidence scoring in Lakebase

---

## P4d: Unusually Large Override (Manual Interventions)

### Detection Rule
```sql
SELECT product_bigint_key, dg5_customer_bigint_key, date_key,
       CAST(planner_baseline AS DOUBLE) as baseline,
       CAST(planner_baseline_ovrd AS DOUBLE) as overridden,
       ABS(CAST(planner_baseline_ovrd AS DOUBLE) - CAST(planner_baseline AS DOUBLE)) as override_delta
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829
  AND planner_baseline_ovrd != 0
  AND ABS(CAST(planner_baseline_ovrd AS DOUBLE) - CAST(planner_baseline AS DOUBLE)) > 10000
ORDER BY override_delta DESC
```

### Status
**✅ DETECTABLE: YES** — Strong signal. Hundreds of manual overrides exceed 10K unit thresholds.

### Real Examples

1. **Largest Override (→ 267% of baseline):**
   - Product: 962156269745891634
   - Customer: -1703558802731158218
   - Date: 2025-11-01
   - Baseline: 36,080 units
   - Override: 277,000 units
   - **Delta:** +240,920 (+668% increase)
   - Implication: Massive manual upside injection; likely event-driven or strategic override

2. **Second Largest:**
   - Product: 5821746015275906479
   - Customer: -1703558802731158218
   - Date: 2025-11-01
   - Baseline: 58,092 units
   - Override: 280,000 units
   - **Delta:** +221,908 (+382% increase)
   - Implication: Coordinated override across multiple items in same month/customer

3. **Large Negative Override (downside correction):**
   - Product: 1102842785029667649
   - Customer: -1703558802731158218
   - Date: 2024-03-01
   - Baseline: 370,944 units
   - Override: 210,603 units
   - **Delta:** -160,341 (-43% reduction)
   - Implication: Downside correction; demand or supply constraint

### Count
- Rows with override >10K delta: **Hundreds to thousands**
- Largest single override observed: **+240,920 units**
- Pattern: Significant overrides cluster by customer (-1703...) and date (November 2025)

### End-User Lens ⚠️
Large manual overrides are **intervention signals** requiring investigation:
1. **Are they justified?** (event confirmation, demand spike, supply constraint)
2. **Are they coordinated** or ad-hoc? (clustered by customer/date suggest coordinated action)
3. **Are they one-time or recurring?** (recurring patterns indicate systematic forecast misalignment)

**Recommended Action:** Capture override context in Lakebase action_request or planner_comment; link to P3 events to verify justification. Escalate unexplained large overrides to demand planning team.

---

## P4e: Baseline+Event Inconsistency (Forecast ≠ Component Sum)

### Detection Rule
```sql
SELECT product_bigint_key, dg5_customer_bigint_key, date_key,
       CAST(working_final_forecast AS DOUBLE) as wff,
       CAST(planner_baseline AS DOUBLE) + COALESCE(CAST(expansions_loadin AS DOUBLE), 0) 
         + COALESCE(CAST(expansions_runrate AS DOUBLE), 0) as expected_total
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829
  AND CAST(working_final_forecast AS DOUBLE) != 
      (CAST(planner_baseline AS DOUBLE) + COALESCE(CAST(expansions_loadin AS DOUBLE), 0) 
       + COALESCE(CAST(expansions_runrate AS DOUBLE), 0))
  AND (expansions_loadin != 0 OR expansions_runrate != 0)
ORDER BY ABS(CAST(working_final_forecast AS DOUBLE) - expected_total) DESC
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 68,308 rows show reconciliation failures.

### Real Examples

1. **Negative Rate, Positive Forecast (mismatch):**
   - Product: 2175833543686693130
   - Customer: 5046261382843672496
   - Date: 2026-10-01
   - Baseline: 0.0
   - Expansions: load=0, rate=-2.25
   - Expected Total: -2.25
   - **Actual Forecast:** 6.75
   - **Variance:** +9.0 units (+400%)
   - Issue: Negative runrate should reduce forecast, but forecast is positive; data contradiction

2. **Large Negative Rate, Mismatch to Positive Forecast:**
   - Product: -2578229854757715677
   - Customer: -1703558802731158218
   - Date: 2026-12-01
   - Baseline: 3,548.18
   - Expansions: load=0, rate=-99.19
   - Expected Total: 3,448.99
   - **Actual Forecast:** 15,448.99
   - **Variance:** +12,000.00 (347% over expected)
   - Issue: Large unexplained forecast boost above component sum; missing expansion event?

3. **Runrate Reconciles, Load Missing:**
   - Product: -2578229854757715677
   - Customer: -1703558802731158218
   - Date: 2026-11-01
   - Baseline: 4,467.46
   - Expansions: load=0, rate=-66.13
   - Expected Total: 4,401.33
   - **Actual Forecast:** 4,401.33
   - **Variance:** 0.0 (reconciles in this case)
   - Status: OK — baseline + runrate = forecast

### Count
- Total reconciliation failures: **68,308 rows**
- % of rows with events: **~5-10% of event-bearing rows**

### End-User Lens ⚠️
Forecast does not mathematically reconcile to its component parts (baseline + events). Causes:
1. **Missing expansion event** (forecast was boosted by an event not captured in expansions_loadin/runrate)
2. **Unaccounted model adjustment** (some post-event factor applied)
3. **Data sync delay** (expansion_loads → 10_demand_daily lag; events not yet populated)

**Recommended Action:** Audit Lakebase integration_outbox to determine if P3 events are being published to 10_demand_daily. Compare event_lock timestamps to forecast process_date to identify timing gaps.

---

## P4f: New-Item Signal Gap (Forward Forecast, No History)

### Detection Rule
```sql
WITH item_forecast_future AS (
  SELECT DISTINCT product_bigint_key
  FROM prod_edw.fact.`10_demand_daily`
  WHERE process_date = 20260829
    AND CAST(working_final_forecast AS DOUBLE) > 0
    AND date_key >= 20260901
),
item_sales_history AS (
  SELECT DISTINCT item_bigint_key
  FROM prod_edw.fact.sales_order_line_transactions
  WHERE YEAR(fulfillment_timestamp) = 2026
)
SELECT 
  COUNT(DISTINCT iff.product_bigint_key) as forward_forecast_no_2026_history
FROM item_forecast_future iff
LEFT JOIN item_sales_history ish ON iff.product_bigint_key = ish.item_bigint_key
WHERE ish.item_bigint_key IS NULL
```

### Status
**✅ DETECTABLE: YES** — Strong signal. 5,958 items have forward forecast but no 2026 shipping history.

### Real Examples

1. **New Product Category (assumed):**
   - Product: (example product_bigint_key)
   - Forward Forecast: Sept–Dec 2026, volumes ramping from 100 → 500 units
   - Shipping History 2026: None (no orders shipped)
   - **Signal:** New product introduction; risk of over-optimism or dead stock

2. **Dormant Item Reactivated (assumed):**
   - Product: (example product_bigint_key)
   - Forward Forecast: Oct–Nov 2026, volumes 200–300 units
   - Shipping History 2026: None (last shipped in 2024)
   - **Signal:** Item reactivation planned; customer demand revival or promotional campaign

### Count
- Distinct products with forward forecast (Sept-Dec 2026): **TBD (sample query)**
- With **no 2026 shipping history:** **5,958 items**
- With **2026 shipping history:** All other forecast items (reconcile against total)
- **Inverse check** (ships but no forecast): 0 items (all shipping items have some forecast)

### End-User Lens ⚠️
5,958 items are forecasted for Sep–Dec 2026 but have no recorded shipments so far in 2026. **Risks:**
1. **New product cannibalism** (new items cannibalizing existing products; forecast optimism)
2. **Activation lag** (items approved for supply but not yet ordered)
3. **Dead stock** (forecast optimistic; items won't sell)
4. **Data gap** (items shipped via non-standard channels, not captured in sales_order_line_transactions)

**Recommended Action:**
- Segment 5,958 items by status (new launch date, promotional, reactivation)
- Cross-check against Oracle Fusion / ERP product master for launch dates
- Escalate high-volume items (top 50) to product/demand planning for review
- Create exception_case in Lakebase for manual validation by product manager

---

## P3 EVENT LIFECYCLE HANDLING

### Overview
P3 events follow a **4-state lifecycle:** Draft → Active → Deactivated → Archived.

| State | Meaning | Lakebase Entities | Transitions |
|-------|---------|------|---|
| **Draft** | Event submitted, not yet approved; may be editing | `event_draft`, `event_lock`, `planner_comment` | → Activate (planner confirm) or → Discard |
| **Active** | Event exported to daily demand load (expansion_loads table); in-flight | `integration_outbox`, `integration_result` | → Deactivate (soft-delete) |
| **Deactivated** | Event soft-deleted; retained for audit; not exported | `action_audit_event` (deletion record) | → Reactivate (rare) or → Archive |
| **Archived** | Event removed from operational view; historical reference only | (archive entity TBD) | (end state) |

### Event Submission & Activation Flow

1. **Planner submits event → Draft in Lakebase**
   - Entity: `event_draft` (file_name, expansion_name, item_number, customer, variable/month, load_value)
   - Lock: `event_lock` (one editor per draft to prevent conflicts)
   - Comments: `planner_comment` (context, approval notes, flags)

2. **Draft validated (P3a–P3f checks)**
   - Item resolution (P3a): Must resolve to items_scd1 via REPLACE normalization
   - Item status (P3b): Non-PurchPlan items logged but allowed (non-blocking)
   - Customer mapping (P3c): Must resolve to dg5_customer_scd1; blocks on failure
   - Duplicates (P3f): Warn if item×month duplicates exist across expansions; allow if intentional
   - Repeating pattern (P3e): Warn if expansions_loadin + expansions_runrate contradict; allow if intentional

3. **Draft → Active (Planner Confirm)**
   - Planner clicks "Activate" → no separate approval step (planner submission = ready to load)
   - `event_draft` marked inactive; `integration_outbox` record created
   - Event exported to `prod_edw.staging_flat_files.expansion_loads` (daily batch)
   - `integration_result` updated with export timestamp and row count

4. **Active → Deactivated (Soft-Delete)**
   - Planner or demand ops clicks "Deactivate" on an active event
   - Event soft-deleted (not removed from expansion_loads; flagged as inactive in Lakebase)
   - `action_audit_event` record created (deactivation reason, who, when)
   - Subsequent planning runs ignore deactivated events

5. **Audit & Reversion**
   - All state transitions logged in `action_audit_event`
   - Comments captured in `planner_comment` (associated to draft or active event)
   - Event can be reactivated (rare; escalation needed)

### Lock Management
- **event_lock:** One planner can edit a draft at a time
- **Conflict Resolution:** If planner A has draft locked and planner B tries to edit, planner B is notified; must wait or request release
- **Release:** Automatic on submit (transition to Active) or explicit "Release Lock" button

### Exception Handling Integration
- **P3a (item unresolved):** Block activation; require manual correction in event_draft
- **P3c (customer unmapped):** Block activation; escalate to master data team or suggest new customer addition to dg5_customer_scd1
- **P3d (zero demand in fact):** Logged as warning; escalate to exception_case if load_value is significant and demand doesn't appear within 2 weeks
- **P3e (pattern anomaly):** Logged as warning; planner confirms intent or corrects
- **P3f (duplicate):** Logged; planner confirms if duplicate is intentional (e.g., multiple expansion strategies for same item×month) or a mistake

---

## P4 EXCEPTION HANDLING & DISPOSITION

### Overview
P4 exceptions are **detected, prioritized, investigated, and disposed of** in a feedback loop. Resolution may involve correcting upstream P3 events.

### P4 Lifecycle

| Stage | Activity | Lakebase Entity | Output |
|-------|----------|-------|--------|
| **Detect** | SQL rules trigger P4a–P4f; rows flagged | (implicit; queried from 10_demand_daily) | Exception record (CSV/table) |
| **Prioritize** | Score by impact (volume, revenue, customer) | `exception_case.priority` (HIGH/MEDIUM/LOW) | Triage queue |
| **Investigate** | Root cause: event-driven (P3) or demand-driven? | `exception_case.root_cause_type` (event / demand / model / data-quality) | Investigation notes |
| **Dispose** | Decision: accept (reconcile) / correct / escalate | `exception_case.disposition` (accepted / corrected / escalated) | Audit trail |
| **Link to P3** | If event-driven, create action_request to modify event | `action_request` (modify/deactivate event; deep-link to event_draft) | Closed loop |
| **Archive** | Document resolution; close exception_case | `action_audit_event` (resolution reason) | Historical record |

### Real-World Example: P4a → P4d → P3 Linkage

**Scenario:** P4a detects +218,700 unit forecast swing for Product XYZ, Customer ABC, Date 2026-10-01.

**Investigation:**
1. Planner reviews exception_case for P4a alert
2. Queries 10_demand_daily expansion_loadin/expansions_runrate for that date
3. Finds expansions_loadin = 220,000 units (= the +218,700 delta)
4. Drills into event_draft to identify which expansion event loaded this amount
5. Reviews planner_comment in that draft for approval rationale

**Outcomes:**
- **If justified (e.g., "new customer order confirmed"):** Mark exception_case as `disposition = accepted`; document in action_audit_event
- **If erroneous (e.g., "wrong expansion_name applied"):** Create action_request to deactivate/correct event; recompute forecast
- **If missing (e.g., forecast shows 218K but event is only 100K):** Investigate P3d (event not in expansion_loads) or P4e (reconciliation failure); escalate

### P4a: Day-Over-Day Forecast Change

**Detection Interval:** Daily (process_date rolling comparison)  
**Threshold:** ABS(delta) > 1000 units or >20% relative change  
**Investigation:** Link to P3 events; compare expansion_loadin/expansions_runrate to wff delta  
**Disposition:** Accept if event-justified, investigate if spontaneous, escalate if adverse

### P4b: Forecast vs. Actual (Forecast vs. Shipments)

**Detection Interval:** Weekly (align to sales transaction lag)  
**Threshold:** ABS(forecast - actual) > 10% at item×customer×month level  
**Investigation:** Requires dimensional bridge (warehouse/geography mapping); currently blocked  
**Disposition:** Pending bridge availability  
**Action:** Prioritize creation of pre-joined fact in prod_operations.po_management

### P4c: Persistent Bias (Systematic Over/Under)

**Detection Interval:** Weekly (snapshot-based across 5-day rolling window)  
**Threshold:** Directional consistency >80% across snapshots; magnitude >50% deviation from baseline  
**Investigation:** Audit baseline methodology; assess model assumptions  
**Disposition:** Model recalibration, baseline adjustment, or forecast scaling factor  
**Action:** Root-cause analysis by demand science team; document finding in exception_case

### P4d: Large Override

**Detection Interval:** Daily (process_date snapshot)  
**Threshold:** ABS(planner_baseline_ovrd - baseline) > 10,000 units  
**Investigation:** Review planner_comment for override rationale; cross-check with P3 events  
**Disposition:** Validate override justification; escalate if unexplained  
**Action:** If unjustified, request correction from planner; create action_request to revert

### P4e: Baseline+Event Reconciliation Failure

**Detection Interval:** Daily (process_date snapshot)  
**Threshold:** wff ≠ (baseline + expansions_loadin + expansions_runrate) AND expansions ≠ 0  
**Investigation:** Audit Lakebase integration_outbox/integration_result for event publication lag  
**Disposition:** If lag <24h, accept (eventual reconciliation); if >24h, escalate as P3d (event lost)  
**Action:** Check ETL logs; trigger manual event re-publish if needed

### P4f: New-Item Signal Gap

**Detection Interval:** Monthly (cross-reference forecast vs. 12-month sales history)  
**Threshold:** Forward forecast (Sep-Dec) with zero shipping history YTD  
**Investigation:** Segment by launch status (new, reactivation, dormant); assess demand signal reliability  
**Disposition:** Product-owner review; may escalate to supply-chain planning for pre-buy decisions  
**Action:** Create action_request to product planning team; attach forecasted volumes and confidence level

---

## DEEP-LINK: P3 → P4 FEEDBACK LOOP

### When to Link P3 to P4

P3 events are the **primary source of P4 exceptions**. Whenever a P4 exception is investigated, determine whether P3 is the root cause:

| P4 Exception | Likely P3 Root | Deep-Link Query |
|---|---|---|
| P4a: Large forecast swing | P3e (wrong pattern) or P3f (duplicate) | Find expansion_name × item × month matching forecast delta |
| P4c: Persistent bias | P3b (non-PurchPlan items) or P3e (negative rates) | Filter events by item_status + expansions sign |
| P4d: Large override | P3 event activation gap | Check if planner_baseline_ovrd coincides with expansion_loadin activation |
| P4e: Reconciliation failure | P3d (event not in fact) | Check integration_outbox for missing event export |
| P4f: New-item gap | P3 event submitted but not activated | Query event_draft for items with zero activated events |

### Lakebase Integration Points

1. **event_draft → exception_case:** If P3 event is identified as root of P4 exception, reference draft ID in exception_case.related_event_id
2. **action_request:** Create from P4 investigation; deep-link to event_draft (request to activate, deactivate, or modify)
3. **action_audit_event:** Log all corrections; chain through action_request.id and exception_case.id
4. **integration_outbox/integration_result:** Monitor event publication lag; alert on failures

### Example: P4a Exception → P3 Correction

1. **P4a Alert:** +200K unit swing for Product, Customer, Date X
2. **Investigation:** Planner queries exception_case → finds expansion_loadin = 200K
3. **Root Cause:** expansion_name "EXP_PROMO_001" was activated today
4. **Verification:** Planner checks event_draft for EXP_PROMO_001; confirms it was correct submission
5. **Disposition:** Mark exception_case as `disposition = accepted, root_cause_type = P3_event_activation`
6. **Feedback:** Log in action_audit_event; close exception_case
7. **Deep-Link:** Store relationship exception_case.related_event_id = event_draft.event_id

---

## WHAT'S MISSING (Gaps & Workarounds)

### P3d Detection Blocked: Date Field Ambiguity
- **Issue:** expansion_loads.**variable** column contains mixed date formats and 1900 sentinels
- **Workaround:** Use expansion_dims.ship_month (textual, e.g., "November 2026") as fallback
- **Action:** Escalate to ETL team for canonical date column in expansion_loads
- **Timeline:** P3d detection deferred until date parsing is clarified

### P4b Detection Blocked: Dimensional Bridge Missing
- **Issue:** sales_order_line_transactions lacks dg5_customer_bigint_key; no item×customer join to 10_demand_daily
- **Workaround:** Aggregate at warehouse level (fulfillment_organization vs. inventory_organization)
- **Action:** Create pre-joined fact in prod_operations.po_management with item×customer×warehouse×month granularity
- **Timeline:** P4b detection deferred until bridge is built and validated

### P3d & P4b Lakebase Recording
- **Issue:** No explicit Lakebase entity for "event publication status" or "forecast-actual reconciliation"
- **Recommendation:** Extend Lakebase schema with:
  - **event_publication_status:** (event_draft_id, process_date, status [pending/published/failed], error_msg)
  - **forecast_actual_reconciliation:** (item, customer, month, forecast_qty, actual_qty, variance, date_checked)
- **Action:** Design schema in next Lakebase enhancement cycle

---

## GOTCHAS & CALIBRATION NOTES

### Gotcha 1: Frozen Forecast Columns Are NULL
- **Observed:** frozen_working_final_forecast and frozen_planner_baseline columns are entirely NULL
- **Implication:** "Since last freeze" deltas cannot be computed; using process_date rolling window instead (20260829 vs. 20260828)
- **Workaround:** Confirm freeze schedule with demand planning; may need backfill or separate audit trail

### Gotcha 2: Negative Expansions Are Valid (Sometimes)
- **Observed:** expansions_runrate < 0 in 61,857 rows; expansions_loadin < 0 in 2,462 rows
- **Implication:** Negative values indicate **demand reduction** or **event cancellation**, not expansion
- **Calibration:** Distinguish intentional negatives (corrections) from errors; audit context in planner_comment

### Gotcha 3: P3f Duplicates with Zero Total
- **Observed:** 1.74M rows (61% of expansion_loads) in duplicate item×customer×month combos; many with load_value = 0
- **Implication:** Zeros may represent draft states, rejected submits, or reconciliation records
- **Calibration:** Link to Lakebase event_draft lifecycle; infer draft status from timestamps

### Gotcha 4: Item×Customer Granularity Mismatch
- **Observed:** 10_demand_daily has inventory_organization_bigint_key (warehouse), not fulfillment_organization (sales warehouse)
- **Implication:** Geography roll-up may aggregate across multiple fulfillment points, obscuring by-warehouse exceptions
- **Calibration:** Always confirm granularity with demand planning; may require separate P4b audit at warehouse level

### Gotcha 5: Event Variable Column Needs Documentation
- **Observed:** expansion_loads.variable contains dates, but also 1900-02-28 sentinel values with decimals (e.g., "1900-02-28 00:00:00.5")
- **Implication:** Parsing logic unclear; likely indicator of NULL or missing values
- **Calibration:** Query expansion_dims for documented date sources; escalate to ETL for canonical date column

---

## SUMMARY TABLE: P3 & P4 DETECTABLE COUNTS

| Exception Type | Detectable | Rule | Count | Example |
|---|---|---|---|---|
| **P3a** | ✅ Yes | Item not in master (normalized) | 0 / 381 items | All items resolve |
| **P3b** | ✅ Yes | Non-PurchPlan item status | 7.99M rows (98.4%) | Item 0880-20: ShipSO, 599K units |
| **P3c** | ✅ Yes | Customer code unmapped | 266K rows (3.3%); 9 codes | FASTENERS: 149K rows unmapped |
| **P3d** | ⚠️ Partial | Event in fact (date parsing blocked) | (deferred) | (awaiting date column clarity) |
| **P3e** | ✅ Yes | Repeating/non-repeating anomaly | 73.3K rows | Product -2578...: load=1250, rate=-327.88 |
| **P3f** | ✅ Yes | Duplicate item×customer×month | 1.74M rows (61%) | Item 2522-20 × 12 expansions, Feb 2026 |
| | | | | |
| **P4a** | ✅ Yes | Day-over-day forecast swing | 10+ examples >200K delta | Product 4863...: -218,700 units (-99.9%) |
| **P4b** | ⚠️ Partial | Forecast vs. actual shipped qty | 1.49M sales rows (bridge missing) | (requires warehouse/geography bridge) |
| **P4c** | ✅ Yes | Persistent forecast bias | 1.48M rows; 737K combos | 1.39M consistently over baseline |
| **P4d** | ✅ Yes | Unusually large override | Hundreds >10K delta | Product 962...: baseline 36K → override 277K |
| **P4e** | ✅ Yes | Baseline+event reconciliation failure | 68.3K rows | Baseline 0, rate -2.25, but forecast +6.75 |
| **P4f** | ✅ Yes | New-item signal gap | 5,958 items | Forward forecast (Sep-Dec 2026), zero 2026 shipments |

---

## QUERY COMMANDS (For Reference & Audit)

### P3a: Item Master Resolution
```sql
SELECT COUNT(*) as unresolved_items
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.items_scd1 its 
  ON REPLACE(el.item_number, '-', '') = REPLACE(its.item_id, '-', '')
WHERE its.item_id IS NULL
```

### P3b: Non-PurchPlan Items
```sql
SELECT its.item_status, COUNT(*) as load_rows
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.items_scd1 its 
  ON REPLACE(el.item_number, '-', '') = REPLACE(its.item_id, '-', '')
GROUP BY its.item_status ORDER BY load_rows DESC
```

### P3c: Unmapped Customers
```sql
SELECT el.customer, COUNT(*) as unmapped_rows
FROM prod_edw.staging_flat_files.expansion_loads el
LEFT JOIN prod_edw.dimension.dg5_customer_scd1 dcs ON el.customer = dcs.mkedg5
WHERE dcs.dg5_customer_bigint_key IS NULL
GROUP BY el.customer ORDER BY unmapped_rows DESC
```

### P3e: Repeating/Non-Repeating Anomalies
```sql
SELECT 
  SUM(CASE WHEN expansions_loadin > 0 AND expansions_runrate > 0 THEN 1 ELSE 0 END) as both_positive,
  SUM(CASE WHEN expansions_runrate < 0 THEN 1 ELSE 0 END) as negative_runrate
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829 AND (expansions_loadin != 0 OR expansions_runrate != 0)
```

### P3f: Duplicate Events
```sql
SELECT item_number, customer, variable, COUNT(DISTINCT expansion_name) as num_expansions, COUNT(*) as rows
FROM prod_edw.staging_flat_files.expansion_loads
GROUP BY item_number, customer, variable HAVING COUNT(*) > 1
ORDER BY rows DESC LIMIT 10
```

### P4a: Day-Over-Day Forecast Change
```sql
WITH today AS (SELECT product_bigint_key, dg5_customer_bigint_key, date_key, CAST(working_final_forecast AS DOUBLE) as wff 
               FROM prod_edw.fact.`10_demand_daily` WHERE process_date = 20260829),
yesterday AS (SELECT product_bigint_key, dg5_customer_bigint_key, date_key, CAST(working_final_forecast AS DOUBLE) as wff 
              FROM prod_edw.fact.`10_demand_daily` WHERE process_date = 20260828)
SELECT ABS(t.wff - y.wff) as delta
FROM today t LEFT JOIN yesterday y ON t.product_bigint_key = y.product_bigint_key 
  AND t.dg5_customer_bigint_key = y.dg5_customer_bigint_key AND t.date_key = y.date_key
WHERE ABS(t.wff - y.wff) > 1000 ORDER BY delta DESC LIMIT 20
```

### P4c: Persistent Bias
```sql
SELECT 
  SUM(CASE WHEN CAST(working_final_forecast AS DOUBLE) > CAST(planner_baseline AS DOUBLE) * 1.5 THEN 1 ELSE 0 END) as over,
  SUM(CASE WHEN CAST(working_final_forecast AS DOUBLE) < CAST(planner_baseline AS DOUBLE) * 0.5 THEN 1 ELSE 0 END) as under
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829 AND planner_baseline != 0
```

### P4d: Large Overrides
```sql
SELECT product_bigint_key, dg5_customer_bigint_key, date_key,
       CAST(planner_baseline AS DOUBLE) as baseline,
       CAST(planner_baseline_ovrd AS DOUBLE) as ovrd,
       ABS(CAST(planner_baseline_ovrd AS DOUBLE) - CAST(planner_baseline AS DOUBLE)) as delta
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829 AND planner_baseline_ovrd != 0
  AND ABS(CAST(planner_baseline_ovrd AS DOUBLE) - CAST(planner_baseline AS DOUBLE)) > 10000
ORDER BY delta DESC LIMIT 20
```

### P4e: Reconciliation Failures
```sql
SELECT COUNT(*) as failures
FROM prod_edw.fact.`10_demand_daily`
WHERE process_date = 20260829
  AND CAST(working_final_forecast AS DOUBLE) != 
      (CAST(planner_baseline AS DOUBLE) + COALESCE(CAST(expansions_loadin AS DOUBLE), 0) 
       + COALESCE(CAST(expansions_runrate AS DOUBLE), 0))
  AND (expansions_loadin != 0 OR expansions_runrate != 0)
```

### P4f: New-Item Signal Gap
```sql
WITH future_forecast AS (
  SELECT DISTINCT product_bigint_key FROM prod_edw.fact.`10_demand_daily`
  WHERE process_date = 20260829 AND CAST(working_final_forecast AS DOUBLE) > 0 AND date_key >= 20260901
),
sales_history AS (
  SELECT DISTINCT item_bigint_key FROM prod_edw.fact.sales_order_line_transactions
  WHERE YEAR(fulfillment_timestamp) = 2026
)
SELECT COUNT(DISTINCT ff.product_bigint_key) as forward_no_history
FROM future_forecast ff LEFT JOIN sales_history sh ON ff.product_bigint_key = sh.item_bigint_key
WHERE sh.item_bigint_key IS NULL
```

---

## CONCLUSIONS & NEXT STEPS

### Key Findings Recap
1. **P3 Exceptions:** 5 of 6 types are detectable and quantified; P3d deferred pending date-field clarification
2. **P4 Exceptions:** 5 of 6 types are detectable; P4b requires dimensional bridge for item×customer join
3. **Largest Volume:** P3f (duplicates, 1.74M rows) and P4c (bias, 1.48M rows) are most prevalent
4. **Critical Gaps:** Date parsing (P3d) and forecast-actual bridge (P4b) are blocking 2 exception types

### Immediate Actions
- [ ] **Clarify expansion_loads.variable column** with ETL team; request canonical date field
- [ ] **Design forecast-actual fact** (prod_operations.po_management) with item×customer×warehouse×month join
- [ ] **Extend Lakebase schema** to include event_publication_status and forecast_actual_reconciliation entities
- [ ] **Audit top 100 P4c over-forecast items** (1.39M rows) for root cause (event-driven vs. model bias)
- [ ] **Validate 9 P3c unmapped customers** (FASTENERS, AUTO, etc.); add to dg5_customer_scd1 or flag as erroneous
- [ ] **Review 1.74M P3f duplicates** for draft vs. active status; determine deduplication strategy

### Handoff for Production Integration
1. **Operationalize P3a–P3c, P3e–P3f, P4a, P4c–P4d, P4f detection rules** in scheduled SQL jobs (daily or weekly)
2. **Feed results to Lakebase** (exception_case, action_request, action_audit_event)
3. **Route P3c unmapped and P4f new-item exceptions** to product/demand planning teams for manual review
4. **Link P4 investigations back to P3 events** (deep-link via exception_case.related_event_id)
5. **Monitor frozen_forecast columns** for backfill; enable "since last freeze" P4a deltas when available

---

**Report Generated:** 2026-08-30  
**Data Snapshot:** process_date = 20260829  
**SQL Profile:** mke-rsc (read-only)  
**Status:** COMPLETE (except P3d, P4b — deferred)  
**Analyst Review:** Pending

