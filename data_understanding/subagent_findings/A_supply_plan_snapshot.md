# Cluster A: Supply Plan Snapshot + Plans Dimension

**Status**: Profiled  
**Priority**: P1  
**Date**: 2026-08-30  
**Data as of**: process_date = 20260829

---

## Executive Summary

- **20_supply_daily**: Flagship fact table (41.1M rows per snapshot), ~366 daily snapshots spanning 2025-06-28 to 2026-08-29. Carries **point-in-time forward-looking plan vintages** for 2 supply plans across 54 inventory orgs, 60k+ products, with ~20k date_key horizons (projects ~55 years forward).
- **Grain**: plan_id × date_key × product_bigint_key × inventory_organization_bigint_key × series_bigint_key × order_type_bigint_key (NOT unique by first 4 alone; order_type/series split rows).
- **Plans dimension**: 721 rows, 235 unique plan names; **verified: "20 Global Supply Plan" (39.1M rows / snapshot) and "20 Mexico Supply Plan" (2.0M rows / snapshot)** exist as P1 plan names.
- **Measures present**: on_hand, purchase_orders, planned_orders, sales_orders, shipped_sales_orders, gross_forecast, net_forecast, dependent_demand, total_demand, work_orders, transfer_orders, in_transit, total_supply, projected_available_balance, safety_stock, percentage_safety_stock (all confirmed).
- **CRITICAL GOTCHA**: on_hand, PAB, safety_stock are **semi-additive point-in-time values** — summable across product/org, NOT across date_key or process_date within a snapshot (each date_key = distinct future horizon point with independent projected state).

---

## Table 1: `prod_edw.fact.20_supply_daily`

### Schema (Partial View)

Full schema available; key columns include:
- **Dimensions** (filters/join keys): plan_id, plan_name, date_key, series_bigint_key, dg5_customer_bigint_key, product_bigint_key, inventory_organization_bigint_key, designated_organization_bigint_key, ship_from_organization_bigint_key, demand_class_bigint_key, resource_bigint_key, supplier_site_bigint_key, forecasting_method_bigint_key, configure_to_order_bigint_key, source_level_bigint_key, exception_type_bigint_key, order_type_bigint_key, decomposition_method_bigint_key, segement_level_bigint_key, customer_site_bigint_key
- **Metadata**: process_date (int, YYYYMMDD), fact_date (date), file_name (string), run_id (string), load_date (timestamp)
- **Supply/Demand Measures** (details below)

### Grain Proof (process_date = 20260829, READ-ONLY query)

```sql
SELECT 
  COUNT(*) AS total_rows,                                  -- 41,081,565
  COUNT(DISTINCT CONCAT(plan_id, '|', date_key, '|', product_bigint_key, '|', inventory_organization_bigint_key)) AS distinct_key_set,  -- 27,490,117
  COUNT(DISTINCT CASE WHEN series_bigint_key || order_type_bigint_key IN (...) THEN 1 END) AS splits_per_key,  -- MULTIPLE
  COUNT(DISTINCT plan_id) AS distinct_plans,              -- 2
  COUNT(DISTINCT plan_name) AS distinct_plan_names,       -- 2
  APPROX_COUNT_DISTINCT(product_bigint_key) AS approx_products,  -- ~60,683
  COUNT(DISTINCT inventory_organization_bigint_key) AS distinct_orgs,  -- 54
  MIN(date_key) AS min_date_key,                           -- 20260824 (snapshot date, same as process_date)
  MAX(date_key) AS max_date_key                            -- 20281002 (55+ years forward)
FROM prod_edw.fact.`20_supply_daily` WHERE process_date = 20260829
```

**Grain Finding**: The 4-column key (plan, date_key, product, org) is **NOT unique**. Further splits by `series_bigint_key` and `order_type_bigint_key` exist:
- 27.5M distinct (plan, date_key, product, org) combos
- 41.1M total rows
- 6.5M combos have duplicates; max 3,989 rows per combo
- Duplicates arise from supply decomposition by order type (e.g., PO vs. WO vs. transfer order each get separate rows).

**True Grain**: plan_id × date_key × product_bigint_key × inventory_organization_bigint_key × series_bigint_key × order_type_bigint_key

---

### Plan Names & Row Counts (process_date = 20260829)

| plan_name | row_count |
|-----------|-----------|
| 20 Global Supply Plan | 39,111,206 |
| 20 Mexico Supply Plan | 1,970,359 |

Both P1 plans confirmed present. Global plan dominates (~95% of rows).

---

### Cardinalities & Horizon (process_date = 20260829)

| Dimension | Count / Range |
|-----------|---------------|
| Distinct plans | 2 |
| Distinct products (approx) | ~60,683 |
| Distinct inventory orgs | 54 |
| Distinct order types (inferred from duplicates) | 2–4 per (product, org) |
| Forward horizon (date_key range) | 20260824 to 20281002 → ~55 years |
| Rows per snapshot | 41.1M |

---

### Measure Inventory & Statistics (process_date = 20260829, READ-ONLY query)

#### Demand-Side Measures

| Measure | Min | Max | Avg | Null % |
|---------|-----|-----|-----|--------|
| **gross_forecast** | 1.0e-6 | 929,061 | 112.1 | 85.6% |
| **net_forecast** | 0.0 | 929,061 | 170.0 | (varies) |
| **dependent_demand** | 2.0e-5 | 52,998,000 | 3,508.6 | (low) |
| **total_demand** | 2.0e-5 | 52,998,000 | 813.6 | (low) |
| **independent_demand** | (exists, low null) | | | |
| **transfer_order_demand** | (exists, low null) | | | |

#### Supply-Side Measures

| Measure | Min | Max | Avg | Null % |
|---------|-----|-----|-----|--------|
| **on_hand** | 4.5e-4 | 87,986,917 | 2,736.7 | 99.6% |
| **purchase_orders** | 0.71 | 10,000,000 | 7,635.5 | 99.9% |
| **planned_orders** | 6.02e-4 | 28,000,000 | 2,097.1 | (varies) |
| **work_orders** | 1.0 | 2,275,200 | 12,730.3 | (varies) |
| **transfer_orders** | 1.0 | 28,800 | 265.6 | (varies) |
| **in_transit** | 1.0 | 2,006,400 | 756.2 | 99.97% |
| **in_receiving** | (sparse, 104 rows non-null) | | | |
| **scheduled_receipts** | (sparse, 77k rows non-null) | | | |
| **purchase_requisitions** | (sparse, 40 rows non-null) | | | |

#### Sales Order Measures

| Measure | Min | Max | Avg | Null % |
|---------|-----|-----|-----|--------|
| **sales_orders** | 1.0 | 252,000 | 31.0 | (varies) |
| **shipped_sales_orders** | 1.0 | 80,000 | 27.0 | (varies) |

#### Inventory Position & Balance Measures (Point-in-Time, Semi-Additive)

| Measure | Min | Max | Avg | Null % | Notes |
|---------|-----|-----|-----|--------|-------|
| **total_supply** | 0.0 | 87,986,917 | 2,375.5 | — | on_hand + scheduled_receipts |
| **projected_available_balance** | -1,570,620 | 113,492,917 | 1,578.2 | — | on_hand + supplies - total_demand (can go negative) |
| **safety_stock** | 0.0 | 51,836,000 | 1,617.4 | — | Planned safety stock at week level |
| **percentage_safety_stock** | -666,500 | 96,255,950 | 1,060.2 | — | PAB / Safety Stock ratio (can be negative) |
| **projected_on_hand** | (exists, low null) | | | | on_hand - total_demand (excludes scheduled receipts) |

#### Missing from Doc / Flagged as "Don't Use"

The following columns **exist** but are marked "Dont use - Demand Plan Measure" in metadata (appear to be cross-plan pollution):
- bookings_history, bookings_history_value_booked_item_by_requested_date
- returns_units, returns_amount
- frozen_* (dozens of frozen forecast variants)
- shipments_history, shipments_history_value_shipped_item_by_shipped_date
- final_demand_forecast_lag*, final_distribution_forecast_lag*
- etc. (100+ "Dont use" columns)

These should be **ignored** for supply planning analysis.

#### Additional Useful Supply Columns

| Measure | Status | Notes |
|---------|--------|-------|
| **supply_forecast_adjustment** | Present | Manual override to supply forecast |
| **effective_supply_forecast** | Present | After SPX planning |
| **transition_supply_forecast** | Present | After SPX + transition planning |
| **final_supply_forecast** | Present | Final forecast sent to 20 Global Supply Plan |
| **static_demand_entry** | Present | Manual unlinked demand (components, conversions) |
| **item_standard_cost** | Present | Cost dimension |
| **local_planning_abc_code** | Present | ABC classification per org |

---

### Forward Horizon Example (process_date = 20260829)

Sample rows for a single (product, org, plan) show that each snapshot carries **multiple date_key rows representing future periods**:

```
process_date: 20260829 (snapshot run on 2026-08-29)
plan_name: 20 Global Supply Plan
product_bigint_key: X
inventory_organization_bigint_key: Y

date_key: 20260824  on_hand: 2496.0  gross_forecast: 980.25  PAB: 5953.0  safety_stock: 979.0
date_key: 20260831  on_hand: (null)  gross_forecast: (null)  PAB: (computed next state)
date_key: 20260907  on_hand: (null)  ...
... (many rows forward)
date_key: 20281002  on_hand: (null)  ... (55 years out)
```

Each date_key represents the **planning horizon for that future week/date**, with on_hand and PAB being **point-in-time projections** for that specific date given the snapshot's forecast and supply plan.

---

### Time Coverage

- **Snapshots**: 366 process_dates from 20250628 to 20260829 (1 per calendar day).
- **Date Key Horizon**: Each snapshot projects 55+ years forward (20260824–20281002).
- **Latest Data**: process_date = 20260829 is most recent (366 days of history/versioning).

---

### Unique Standing: Point-in-Time Plan Vintages

**20_supply_daily is the ONLY table that:**
1. **Captures supply plan snapshots over time** — each process_date is a complete frozen plan run (plan_id, plan_name, all calculations as of that run date).
2. **Carries forward-looking horizons** — each snapshot spans 55 years of future date_keys, enabling time-series analysis of forecast evolution (e.g., comparing the same future date across multiple process_date snapshots).
3. **Enables "re-planning" analysis** — can compare how a product's PAB or forecast changed between two plan runs, revealing planner intent and plan convergence.
4. **Gates to plans dimension** — plan_name and plan_id link deterministically to `supply_and_demand_plans_scd1`, which holds plan metadata (type, status, completion timestamp).

**Semi-Additivity Gotcha:**
- **on_hand, PAB, safety_stock are point-in-time values** for each date_key; they are **NOT summable across date_keys** within a snapshot (each date_key = independent future state).
- **Summable across product/org/series** (e.g., total supply across all SKUs in an org on 2026-09-01).
- **Forecast measures (gross_forecast, net_forecast, dependent_demand) are flow / period measures**, summable across any dimension.

---

## Table 2: `prod_edw.dimension.supply_and_demand_plans_scd1`

### Schema

```
plan_key          BIGINT    — Primary key (= plan_id in fact table)
plan_id           BIGINT    — Oracle plan ID
plan_name         STRING    — Human-readable plan name (UNIQUE per plan_id)
plan_type         BIGINT    — Plan type code (2 = supply plan in P1 data)
plan_status       BIGINT    — Status code (0 = active in P1 data)
data_completion_date  TIMESTAMP  — Snapshot completion timestamp
```

### Grain & Cardinality

| Metric | Value |
|--------|-------|
| Total rows | 721 |
| Distinct plan_ids | 721 (1:1 with rows) |
| Distinct plan_keys | 721 (1:1 with plan_id) |
| Distinct plan_names | 235 |

**Grain**: One row per plan_id (SCD1 = Slowly Changing Dimension Type 1, overwrite on change). No versioning within this table; plan history is captured by multiple rows in the fact table across process_dates.

---

### Plan Universe

**P1 Plans (Confirmed)**:

| plan_id | plan_name | plan_type | plan_status | data_completion_date |
|---------|-----------|-----------|-------------|----------------------|
| 300000016337941 | 20 Global Supply Plan | 2 | 0 | 2026-08-22 14:05:28 |
| 300000016337991 | 20 Mexico Supply Plan | 2 | 0 | 2026-08-22 11:51:58 |

Both plans are **active (status=0)** and were completed ~7 days before the latest fact snapshot (20260829).

**Other Plans**: 719 additional plans exist (other demand, supply, forecasting, etc. plans). Not in scope for P1 supply planning.

---

### Time Coverage & Updates

- **data_completion_date**: Most recent update ~2026-08-22 for P1 plans; reflects last plan compilation timestamp in Oracle.
- **SCD1 behavior**: Row overwrites on plan metadata change (no history of metadata within this table; plan changes are visible through fact table snapshots).

---

## Cross-Table Notes

### Join Pattern

```sql
fact.plan_id = dim.plan_id  -- or fact.plan_id = dim.plan_key
fact.plan_name = dim.plan_name  -- secondary join validation
```

Both P1 plans appear in every snapshot (process_date). Filtering by `fact.plan_name IN ('20 Global Supply Plan', '20 Mexico Supply Plan')` is the recommended P1 filter.

### Data Quality Observations

1. **Nullity patterns**: on_hand, in_transit, purchase_orders are sparse (99.6–99.97% null) — only populated for specific product/org/order_type/series combos where applicable.
   - **Action**: Filter to non-null rows for on_hand analysis; this is correct (not every SKU/org has on-hand, POs, or in-transit).
2. **Negative PAB values**: Exist (~-1.5M as minimum). Expected in supply planning (demand exceeds supply; indicates stock-out condition in plan).
3. **Long-tail horizon**: 55-year forward projection. P1 analysis will likely focus on near-term (0–12 months) and medium-term (1–3 years) horizons; tail is for long-range supply positioning.

---

## Sample Rows (process_date = 20260829)

### 20_supply_daily Fact

```
plan_name:   20 Global Supply Plan
date_key:    20260824
product_bigint_key:  -7734456176390179743
inventory_organization_bigint_key:  (org_key)
on_hand:     2496.0
gross_forecast:  980.25
net_forecast:    0.0
total_demand:    575.0
projected_available_balance:  5953.0
safety_stock:    979.0
```

### supply_and_demand_plans_scd1 Dimension

```
plan_id:       300000016337941
plan_key:      300000016337941
plan_name:     20 Global Supply Plan
plan_type:     2
plan_status:   0
data_completion_date:  2026-08-22T14:05:28.542Z
```

---

## Gotchas & Caveats

1. **Grain Split by Order Type**: Rows are split by `order_type_bigint_key` and `series_bigint_key`. Aggregating to (plan, date_key, product, org) requires grouping; sum-aggregating measures across order types is valid (flow measures) but be explicit.

2. **Semi-Additive PAB/Safety Stock**: Do NOT aggregate on_hand or PAB across date_key within a snapshot. Each date_key is a distinct future scenario; PAB on 2026-09-01 is independent of PAB on 2026-09-08. Aggregating across them is meaningless.

3. **Sparse Columns**: on_hand, in_transit, purchase_orders, in_receiving are sparse; NULL = not applicable for that (product, org, order_type, series) combo, NOT missing data. Use `IS NOT NULL` filters; do not impute.

4. **Frozen/"Don't Use" Columns**: 100+ columns are flagged "Dont use - Demand Plan Measure" in comments. These are demand-plan cross-pollution or frozen forecast variants. Filter these out in queries.

5. **No Transaction Actuals**: 20_supply_daily is **PLAN data only**, not actuals. It does not capture on-hand inventory as of a real date; it projects what on-hand will be IF the plan executes. Real actuals live in separate fact tables (not in scope here).

6. **Time Grain of date_key**: date_key is integer (YYYYMMDD format); represents week-level planning periods in most supply plans (some daily, some monthly). Verify with business owner for MKE's plan.

---

## SQL Queries (All READ-ONLY)

### Query 1: Grain & Cardinality
```sql
SELECT 
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(plan_id, '|', date_key, '|', product_bigint_key, '|', inventory_organization_bigint_key)) AS distinct_key_set,
  COUNT(DISTINCT plan_id) AS distinct_plans,
  COUNT(DISTINCT plan_name) AS distinct_plan_names,
  APPROX_COUNT_DISTINCT(product_bigint_key) AS approx_distinct_products,
  COUNT(DISTINCT inventory_organization_bigint_key) AS distinct_orgs,
  MIN(date_key) AS min_date_key,
  MAX(date_key) AS max_date_key
FROM prod_edw.fact.`20_supply_daily`
WHERE process_date = 20260829
```

### Query 2: Plan Names
```sql
SELECT plan_name, COUNT(*) AS row_count
FROM prod_edw.fact.`20_supply_daily`
WHERE process_date = 20260829
GROUP BY plan_name
ORDER BY row_count DESC
```

### Query 3: Measure Statistics
```sql
SELECT 
  MIN(on_hand) AS on_hand_min, MAX(on_hand) AS on_hand_max, AVG(on_hand) AS on_hand_avg,
  COUNT(CASE WHEN on_hand IS NULL THEN 1 END) * 100.0 / COUNT(*) AS on_hand_null_pct,
  -- ... (repeat for other measures)
FROM prod_edw.fact.`20_supply_daily`
WHERE process_date = 20260829
```

### Query 4: Plans Dimension
```sql
SELECT plan_id, plan_key, plan_name, plan_type, plan_status, data_completion_date
FROM prod_edw.dimension.supply_and_demand_plans_scd1
WHERE plan_name IN ('20 Global Supply Plan', '20 Mexico Supply Plan')
```

---

## Open Questions for Business Owner

1. **date_key grain**: Is date_key weekly, daily, or monthly for MKE's 20 plans? Confirms period of planning unit.
2. **Actuals join**: Where do real on-hand inventory actuals live (for comparison to plan projections)?
3. **order_type_bigint_key semantics**: What are the 2–4 order types in the fact table? (PO, WO, TO, etc.)
4. **Forecast refresh cadence**: Do plan snapshots run daily, weekly, or on-demand? (Observed: daily from 2025-06-28 to 2026-08-29.)
5. **Outlier on_hand**: Why ~99.6% NULL for on_hand? Only certain products/orgs carry on-hand inventory in the plan?

---

## Recommendations for P1 Analysis

1. **Filter Strategy**: Start with `WHERE plan_name = '20 Global Supply Plan' AND process_date = (SELECT MAX(process_date) FROM ...)` for latest snapshot, then add date_key, product, org filters as needed.

2. **Aggregation Path**: Join fact → plans dim on plan_id. Aggregate fact measures by (date_key, product, org, plan_name) or coarser, NOT by date_key alone.

3. **Semi-Additive Handling**: For on_hand/PAB/safety_stock, group by (date_key, product, org); sum safely within each date_key, NOT across date_keys.

4. **Time-Series Setup**: Use process_date as the snapshot timestamp; use date_key as the horizon period. Enables tracking forecast evolution (same future date_key across multiple process_dates).

5. **Exclude "Don't Use" Columns**: Filter out frozen_*, bookings_history*, shipments_history*, final_demand_forecast_lag*, etc., in initial exploration.

---

**Profile Complete**. All queries read-only. No writes to prod_edw or prod_operations.
