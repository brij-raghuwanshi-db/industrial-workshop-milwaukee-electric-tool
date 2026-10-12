%md
# Actuals Supply Plan — Detailed Requirements
## Milwaukee Tool — Supply Chain Analytics

**Project Owner:** Supply Planning Team 
**Related Systems:** Oracle Fusion, Databricks Snapshot Process, Control Tower 
**Cadence:** Weekly (aligned to Monday planning cycle)

---

## 1. Project Overview

### Objective
Develop an "Actuals" supply plan that compares **what we planned** versus **what actually happened**, enabling planners to quickly identify root causes for week-over-week changes.

### Problem Statement
Today, planners manually pull data from multiple systems to reconcile what was expected last week/month versus what occurred. This is time-consuming, error-prone, and limits root-cause analysis.

### Benefits & Value

| Benefit | Description | Measure of Success |
| --- | --- | --- |
| Efficiency | Reduce time spent gathering data from multiple systems | Hours saved per planner per week |
| Confidence | Enable planners to quickly identify root causes for changes | Time-to-insight reduction |
| Time Savings | Eliminate manual data pulls and reconciliation across systems | Elimination of manual Excel processes |
| Accuracy | Single source of truth for planned vs. actual comparisons | Reduced discrepancies in reporting |

---

## 2. Core Functionalities

### 2.1 Snapshot Capture

| # | Requirement | Description | Priority | Status |
| --- | --- | --- | --- | --- |
| 2.1.1 | Weekly snapshot cadence | Capture planned state every week (aligned to Monday planning cycle) | Must Have | Open |
| 2.1.2 | On Hand Inventory snapshot | Store current on-hand inventory positions by SKU/Org at point-in-time | Must Have | Open |
| 2.1.3 | Planned Purchase Orders snapshot | Capture open/planned PO quantities, expected receipt dates, supplier | Must Have | Open |
| 2.1.4 | Planned Customer Orders snapshot | Capture planned customer demand/sales orders by SKU/Org/week | Must Have | Open |
| 2.1.5 | Historical retention | Store snapshots indefinitely for historical comparison | Must Have | Open |
| 2.1.6 | Snapshot metadata | Tag each snapshot with capture date, source system version, run ID | Must Have | Open |

### 2.2 Connect to Existing Snapshot Process

| # | Requirement | Description | Priority | Status |
| --- | --- | --- | --- | --- |
| 2.2.1 | Integration with existing snapshot framework | Leverage current Databricks snapshot infrastructure (tables, scheduling) | Must Have | Open |
| 2.2.2 | Historical supply plan access | Connect to existing historical supply plan snapshots for comparison | Must Have | Open |
| 2.2.3 | Consistent grain | Ensure actuals data aligns at same grain as supply plan snapshots (SKU/Org/Week) | Must Have | Open |
| 2.2.4 | Snapshot versioning | Support ability to identify which snapshot version is being compared | Should Have | Open |

### 2.3 Compare Actuals to Prior Plan

| # | Requirement | Description | Priority | Status |
| --- | --- | --- | --- | --- |
| 2.3.1 | Week-over-week comparison | What happened this week vs. what was expected last week | Must Have | Open |
| 2.3.2 | Month-over-month comparison | What happened this month vs. what was expected last month | Should Have | Open |
| 2.3.3 | PO receipt actuals vs. plan | Compare actual PO receipts to planned PO receipts (quantity, timing) | Must Have | Open |
| 2.3.4 | Sales order actuals vs. plan | Compare actual sales orders shipped to planned customer orders | Must Have | Open |
| 2.3.5 | On-hand actuals vs. plan | Compare actual ending on-hand to projected available balance | Must Have | Open |
| 2.3.6 | Variance calculation | Calculate absolute and percentage variances between plan and actual | Must Have | Open |
| 2.3.7 | Root cause categorization | Categorize variances (demand change, supply delay, quality issue, etc.) | Should Have | Open |

### 2.4 Compare Live Plan to History

| # | Requirement | Description | Priority | Status |
| --- | --- | --- | --- | --- |
| 2.4.1 | Current plan vs. historical actuals | View current forward plan overlaid with historical actual performance | Must Have | Open |
| 2.4.2 | Plan accuracy trending | Track plan accuracy over time (how good are our forecasts/plans) | Should Have | Open |
| 2.4.3 | Bias detection | Identify systematic over/under-planning by SKU, category, or planner | Nice to Have | Open |



%md
## 3. Data Sources

### 3.1 Existing Snapshot Infrastructure (CONFIRMED)

**Primary Fact Table:** `prod_edw.fact.20_supply_daily` 
**Dashboard Reference:** [Supply Historical Snapshots](https://adb-3423969507737722.2.azuredatabricks.net/dashboardsv3/01f122142f8a15b5a97d5c812f727feb/published)

This table already captures **daily snapshots** of the full supply plan. The `process_date` column (INT, format `yyyyMMdd`) identifies which snapshot date the row belongs to.

**Plan Filtering Logic:**
- Plan Name = `'20 Global Supply Plan'` for all orgs except 2120
- Plan Name = `'20 Mexico Supply Plan'` for org 2120

### 3.2 Source Tables (Confirmed from Dashboard)

| # | Data Element | Table | Join Key | Purpose |
| --- | --- | --- | --- | --- |
| 3.2.1 | Supply Plan Snapshots (all measures) | `prod_edw.fact.20_supply_daily` | `process_date` (snapshot), `date_key`, `product_bigint_key`, `inventory_organization_bigint_key` | Core snapshot data with on_hand, purchase_orders, planned_orders, sales_orders, shipped_sales_orders, total_demand, total_supply, PAB, safety_stock |
| 3.2.2 | Item Attributes | `prod_edw.dimension.items_scd1` | `item_bigint_key` = `product_bigint_key` | Item ID, selling item, status, COO, PL hierarchy, ABC code |
| 3.2.3 | Date Dimension | `prod_edw.dimension.date_scd1` | `date_key` | Converts date_key to date_value for calendar alignment |
| 3.2.4 | Organization | `prod_edw.dimension.inventory_organization_scd1` | `inventory_organization_bigint_key` | Organization code (DC/Org level) |
| 3.2.5 | Series/Supplier Attributes | `prod_operations.edw_extension.dim_series_ext_vw` | `series_bigint_key` | Supplier name/site, planner, lead times, standard cost, MOQ, lot multiplier |
| 3.2.6 | Plan Names | `prod_edw.dimension.supply_and_demand_plans_scd1` | `plan_id` | Filters to correct plan (20 Global vs 20 Mexico) |

### 3.3 Available Measures in Snapshot Table

These measures are already captured daily in `20_supply_daily`:

| Category | Measures | Notes |
| --- | --- | --- |
| Demand | `gross_forecast`, `net_forecast`, `sales_orders`, `shipped_sales_orders`, `dependent_demand`, `total_demand` | `shipped_sales_orders` = actuals signal |
| Supply | `planned_orders`, `purchase_orders`, `work_orders`, `transfer_orders`, `in_transit`, `total_supply` | `purchase_orders` = planned receipts |
| Inventory | `on_hand`, `projected_available_balance` | `on_hand` = current inventory position |
| Safety Stock | `safety_stock`, `percentage_safety_stock` | SS targets |

### 3.4 Transactional Actuals Tables (CONFIRMED)

These are the separate transaction-level data sources for actuals:

#### 3.4.1 PO Receipts — `prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions`

| Attribute | Detail |
| --- | --- |
| Source System | Oracle Fusion ERP (RCV_TRANSACTIONS) |
| Key Columns | `quantity`, `transaction_date`, `transaction_type`, `po_header_id`, `po_line_id`, `item_id`, `organization_id`, `country_of_origin_code` |
| Grain | Individual receipt transaction (one row per receipt event) |
| Notes | Raw staging table from Oracle. Contains actual received quantities and receipt dates. Use `transaction_type` to filter for receipts vs. returns. |
| Status | **Available** |

> **Note:** `prod_edw.fact.purchase_order_delivery` exists but is **marked for deprecation**. Do NOT build dependencies on it. Use `receiving_receipt_transactions` or identify the replacement fact table.

#### 3.4.2 Sales Shipments — `prod_edw.fact.sales_order_line_transactions`

| Attribute | Detail |
| --- | --- |
| Source System | Oracle ERP, AX (Microsoft Dynamics AX), JDE |
| Key Columns | `shipped_quantity`, `order_quantity`, `fulfillment_timestamp`, `item_bigint_key`, `fulfillment_organization_bigint_key`, `sales_fulfillment_line_status`, `order_date_key`, `requested_ship_date_key` |
| Grain | Sales order fulfillment line (one row per shipment event per order line) |
| Join Keys | `item_bigint_key` -> `items_scd1`, `fulfillment_organization_bigint_key` -> `inventory_organization_scd1` |
| Filters | `order_type` = 'Standard' (exclude returns, credit memos, no-charge), `sales_fulfillment_line_status` for shipped lines |
| Status | **Available** |

#### 3.4.3 On-Hand Inventory — `prod_edw.fact.inventory_days_on_hand`

| Attribute | Detail |
| --- | --- |
| Source System | Oracle Fusion |
| Key Columns | `on_hand_qty`, `on_hand_cost`, `date_key`, `process_date`, `item_bigint_key`, `inventory_organization_bigint_key`, `series_bigint_key`, `standard_cost` |
| Grain | Item / Organization / Date (daily snapshot of inventory position) |
| Join Keys | `item_bigint_key` -> `items_scd1`, `inventory_organization_bigint_key` -> `inventory_organization_scd1` |
| Additional Measures | `six_months_scop_qty`, `six_months_scop_cost`, `work_order_wip_cost`, `received_not_put_away_cost`, `in_transit_cost` |
| Status | **Available** |

#### 3.4.4 Additional Supporting Tables (Identified)

| Table | Purpose | Status |
| --- | --- | --- |
| `prod_edw.fact.order_line_fulfillment_accumulating_snapshot` | Accumulating snapshot tracking full order lifecycle (booking through fulfillment) | Available - may be useful for order-level metrics |
| `prod_edw.fact.customer_shipments` | Customer-facing shipment records | Available - needs investigation |
| `prod_edw.fact.inventory_material_transaction` | Detailed inventory movements (receipts, issues, transfers, adjustments) | Available - useful for root cause categorization |
| `prod_edw.staging_oracle_fusion_erp.inventory_on_hand_temporal` | Temporal on-hand balances with `date_received` field | Available - alternative on-hand source |
| `prod_edw.fact.purchase_orders` | Purchase order header/line details | Available - for PO context (expected dates, qty ordered) |

### 3.5 Actuals Data Model — How Tables Connect

```
                    PLAN (What We Expected)
                    ========================
                    prod_edw.fact.20_supply_daily
                      process_date = prior Monday
                      date_value = target week
                      Measures: purchase_orders, sales_orders,
                        on_hand, projected_available_balance
                             |
                             |  COMPARE
                             v
                    ACTUALS (What Actually Happened)
                    ================================
    PO Receipts:    receiving_receipt_transactions
                      transaction_date within target week
                      SUM(quantity) by item/org/week
                             +
    Sales Shipped:  sales_order_line_transactions
                      fulfillment_timestamp within target week
                      SUM(shipped_quantity) by item/org/week
                             +
    On-Hand:        inventory_days_on_hand
                      process_date = week end date
                      on_hand_qty by item/org
```

> **Key Insight:** With these transactional tables confirmed, we have a complete picture. The plan comes from `20_supply_daily` (prior snapshot's forward view), and actuals come from three independent transactional sources. This provides true transaction-level granularity rather than relying solely on snapshot day-0 values.

### 3.5 Key Questions to Resolve (Updated)

| # | Question | Context | Status |
| --- | --- | --- | --- |
| Q1 | ~~What is the existing snapshot table structure?~~ | **RESOLVED** - `prod_edw.fact.20_supply_daily` with `process_date` as snapshot identifier | **Resolved** |
| Q2 | ~~Can PO receipt actuals be derived from snapshot day-0 values?~~ | **RESOLVED** - Using separate transactional table `receiving_receipt_transactions` for true receipt actuals | **Resolved** |
| Q3 | ~~How are sales order actuals defined?~~ | **RESOLVED** - `sales_order_line_transactions.shipped_quantity` with `fulfillment_timestamp` as the actuals signal | **Resolved** |
| Q4 | ~~What is the snapshot capture timing?~~ | **RESOLVED** - Snapshots are taken in the early morning (reflects prior day's end-of-day state) | **Resolved** |
| Q5 | ~~Are there existing transformations/gold tables?~~ | **RESOLVED** - Dashboard already implements two-snapshot comparison with scaffold pattern | **Resolved** |
| Q6 | ~~What granularity is needed for the comparison?~~ | **RESOLVED** - Aggregate to weekly level. Daily snapshots and transactions are summed/aligned to week (Monday start) for plan vs. actual comparison | **Resolved** |
| Q7 | ~~How far back does `process_date` go?~~ | **RESOLVED** - Need minimum 6 months of history for backfill. Must validate that `process_date` covers at least 6 months back (~26 weekly snapshots) | **Resolved** |
| Q8 | ~~Is `on_hand` in snapshot a point-in-time stock position or cumulative?~~ | **RESOLVED** - `on_hand` is a point-in-time stock position. Can be used directly as actual inventory level at any given snapshot date. | **Resolved** |

---

## 4. Data Architecture

### 4.1 Proposed Table Structure (Leveraging Existing Snapshot)

```
+-----------------------------------------------------------------------+
|                EXISTING SOURCE (ALREADY IN PLACE)                      |
|                                                                       |
|  prod_edw.fact.20_supply_daily                                        |
|    - Daily snapshots with process_date (yyyyMMdd)                     |
|    - Measures: on_hand, purchase_orders, planned_orders,              |
|      sales_orders, shipped_sales_orders, total_demand,                |
|      total_supply, projected_available_balance, safety_stock          |
|                                                                       |
|  Dimension Tables:                                                    |
|    - prod_edw.dimension.items_scd1                                    |
|    - prod_edw.dimension.date_scd1                                     |
|    - prod_edw.dimension.inventory_organization_scd1                   |
|    - prod_operations.edw_extension.dim_series_ext_vw                  |
|    - prod_edw.dimension.supply_and_demand_plans_scd1                  |
+-----------------------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------------------+
|                SILVER / ACTUALS CONSOLIDATION (NEW)                    |
|                                                                       |
|  actuals_weekly_summary                                               |
|    - Aggregates snapshot day-0 values to weekly grain                 |
|    - Grain: item_id / organization_code / week_start_date             |
|    - Measures: actual_on_hand, actual_po_received,                    |
|      actual_shipped, actual_total_demand                              |
|                                                                       |
|  planned_weekly_summary                                               |
|    - Prior week's forward projections (what was planned)              |
|    - Grain: item_id / organization_code / week_start_date /           |
|      snapshot_date                                                    |
|    - Measures: planned_on_hand, planned_po, planned_shipped,          |
|      planned_total_demand                                             |
+-----------------------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------------------+
|                GOLD / COMPARISON (NEW)                                 |
|                                                                       |
|  plan_vs_actual                                                       |
|    - Joined: planned (from prior snapshot) vs actual (from current)   |
|    - Grain: item_id / organization_code / week_start_date             |
|    - Includes: variance_abs, variance_pct, variance_category          |
|                                                                       |
|  plan_accuracy_metrics                                                |
|    - Aggregated accuracy KPIs over time                               |
|                                                                       |
|  variance_summary                                                     |
|    - Category/supplier/planner level rollups                          |
+-----------------------------------------------------------------------+
```

### 4.2 Key Design Decisions

| # | Decision | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| D1 | Snapshot storage strategy | (a) Build new actuals tables from existing `20_supply_daily` (b) Create views on top of existing table | (a) Build silver/gold tables that pre-join and aggregate - avoids expensive repeated joins on the large fact table | **Decided** |
| D2 | Week definition | (a) ISO week (b) Monday-Sunday (c) Align to planning calendar | (b) Monday-Sunday. Week starts Monday, ends Sunday. Monday morning snapshot reflects Sunday EOD state. | **Decided** |
| D3 | Point-in-time for actual | (a) Use latest `process_date` snapshot day-0 values (b) Use Sunday snapshot for prior week | (a) Use Monday snapshot (`process_date`) where `date_value` = snapshot date (day-0 = current reality). Monday AM snapshot reflects Sunday EOD state. | **Decided** |
| D4 | Backfill strategy | (a) Load all history from `20_supply_daily` (b) Rolling 52 weeks (c) Incremental from go-live | Backfill 180 days (6 months / ~26 weekly snapshots). Do not load beyond 180 days. Incremental weekly appends going forward. | **Decided** |
| D5 | Catalog/Schema location | `prod_edw.fact` (alongside source) vs. `prod_operations` (alongside extensions) | `prod_operations` - this is a derived/analytical layer, not raw EDW | **Decided** |
| D6 | Actuals definition | (a) Day-0 values from current snapshot (b) Separate transactional actuals | Start with (a) day-0 snapshot values as baseline actuals; layer in (b) transactional sources for PO receipt timing and shipment detail as needed | **Decided** |

### 4.3 Comparison Pattern (From Existing Dashboard)

The Supply Historical Snapshots dashboard already implements a **two-snapshot comparison** using a scaffold + window function pattern:

```sql
-- Existing pattern in dashboard:
-- 1. Filter to two snapshot dates (first_snapshot, second_snapshot)
-- 2. Aggregate measures by item_id / snapshot_date / date_value / organization_code
-- 3. Create scaffold (CROSS JOIN of all keys x both snapshots)
-- 4. LEFT JOIN actuals to scaffold (fills NULLs where one snapshot has data the other doesn't)
-- 5. Window functions pivot attributes/measures into first/second columns
```

This same pattern can be adapted for the Actuals project:
- **"First Snapshot"** = Prior week's plan (the projection made last Monday for this week)
- **"Second Snapshot"** = Current week's snapshot (day-0 values = what actually happened)


%md
## 5. Comparison Logic & Metrics

### 5.1 Plan vs. Actual Comparison Model

**Core comparison structure:**
```
FOR each (SKU, Org, Week):
    planned_value  = snapshot[metric, snapshot_date = prior_week]
    actual_value   = actuals[metric, week = current_week]
    variance_abs   = actual_value - planned_value
    variance_pct   = (actual_value - planned_value) / planned_value * 100
```

### 5.2 Metrics to Compare

| # | Metric | Planned Source | Actual Source | Variance Calc | Unit |
| --- | --- | --- | --- | --- | --- |
| M1 | PO Receipts | Planned PO qty from prior snapshot | Actual qty received this week | Actual - Planned | Units |
| M2 | Sales Orders Shipped | Planned SO qty from prior snapshot | Actual qty shipped this week | Actual - Planned | Units |
| M3 | Ending On Hand | Projected PAB from prior snapshot | Actual on-hand at week end | Actual - Planned | Units |
| M4 | PO Timing | Expected receipt week from prior snapshot | Actual receipt week | Weeks early/late | Weeks |
| M5 | Demand vs. Plan | Planned demand from prior snapshot | Actual demand received | Actual - Planned | Units |

### 5.3 Variance Categories (Root Cause Framework)

| Category | Description | Examples |
| --- | --- | --- |
| Supply Timing | PO arrived early or late vs. plan | Supplier delay, early shipment, port congestion |
| Supply Quantity | PO qty received differs from planned | Partial shipment, over-shipment, quality rejection |
| Demand Change | Actual demand differs from planned | New orders, cancellations, order date changes |
| Inventory Adjustment | On-hand changed outside of normal flow | Cycle count adjustments, damage, write-offs |
| Plan Change | The plan itself was modified mid-week | Planner override, rebalancing, expedite decision |

---

## 6. Use Cases & User Stories

### 6.1 Primary Use Cases

| # | As a... | I want to... | So that... | Priority |
| --- | --- | --- | --- | --- |
| UC1 | Supply Planner | See what POs were expected last week vs. what actually received | I can identify supplier delivery issues immediately on Monday | Must Have |
| UC2 | Supply Planner | Compare my ending on-hand to what was projected | I understand why my inventory position changed unexpectedly | Must Have |
| UC3 | Supply Planner | View demand actuals vs. what was in the plan | I can separate demand-driven variance from supply-driven variance | Must Have |
| UC4 | Planning Manager | See plan accuracy trending over weeks/months | I can identify systematic planning issues by category or planner | Should Have |
| UC5 | Supply Planner | Compare current live plan to last week's snapshot | I know what changed in the plan and why | Must Have |
| UC6 | Supply Planner | Drill into a specific SKU's history over multiple weeks | I can see patterns (e.g., a supplier consistently late) | Should Have |

### 6.2 Example Workflow (Monday Morning)

```
1. Planner opens Actuals view on Monday morning
2. System shows: "Last week's plan vs. what happened"
   - POs expected to arrive: 150 lines
   - POs actually received: 132 lines (88% on-time)
   - 18 lines late → drill into which suppliers / SKUs
3. Planner identifies:
   - Supplier A: 5 late POs (container delayed)
   - Supplier B: 3 short-shipped POs (quality issue)
4. Planner takes action:
   - Expedite replacement POs for Supplier B
   - Adjust forward plan for Supplier A delays
5. Planner validates:
   - Current live plan reflects the adjustment
   - Next week's expected receipts are updated
```


%md
## 7. Technical Requirements

### 7.1 Data Pipeline Requirements

| # | Requirement | Description | Priority |
| --- | --- | --- | --- |
| T1 | Automated weekly snapshot capture | Pipeline runs every Monday (or configurable day) to capture actuals for prior week | Must Have |
| T2 | Idempotent processing | Re-running the pipeline for a given week does not create duplicates | Must Have |
| T3 | Late data handling | Support for data arriving after the snapshot window closes | Should Have |
| T4 | Source system alignment | Capture actuals at the same point-in-time as the supply plan snapshot | Must Have |
| T5 | Data validation | Validate row counts, null checks, and referential integrity on each run | Must Have |
| T6 | Alerting on failure | Notify team if pipeline fails or data quality checks fail | Must Have |
| T7 | Backfill capability | Support historical backfill for initial load and gap-filling | Must Have |

### 7.2 Performance & Scale

| # | Requirement | Estimate |
| --- | --- | --- |
| P1 | SKU count | ~XX,XXX active SKUs (TBD) |
| P2 | Org count | ~XX orgs (TBD) |
| P3 | Weekly snapshot size | Estimate: SKUs x Orgs x Metrics = TBD rows per week |
| P4 | Historical depth | Initial backfill: 180 days (~26 weeks). Retain indefinitely going forward. |
| P5 | Query performance | Plan vs. Actual comparison for single SKU < 5 seconds |
| P6 | Aggregation performance | Category-level summary across all SKUs < 30 seconds |

### 7.3 Integration Points

| # | System | Direction | Purpose | Method |
| --- | --- | --- | --- | --- |
| I1 | Oracle Fusion | Inbound | PO, SO, Inventory data | Existing Databricks ingestion pipelines |
| I2 | Existing Snapshot Process | Inbound | Historical supply plan snapshots | Direct table read |
| I3 | Control Tower App | Outbound | Surface actuals comparison in planner UI | TBD (API / direct table read) |
| I4 | Exception Queue | Outbound | Feed variance-based exceptions | Delta table / event trigger |

---

## 8. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
- [x] Identify and document existing snapshot tables/schemas (DONE - `20_supply_daily` + dimensions)
- [x] Identify transactional actuals source tables (DONE - receipts, shipments, on-hand)
- [x] Define architecture decisions (DONE - D1 through D6 all decided)
- [ ] Define actuals table schemas in `prod_operations` (silver layer)
- [ ] Build pipeline to capture weekly On Hand actuals from `inventory_days_on_hand`
- [ ] Build pipeline to capture weekly PO Receipt actuals from `receiving_receipt_transactions`
- [ ] Build pipeline to capture weekly Sales Shipped actuals from `sales_order_line_transactions`
- [ ] Create initial `plan_vs_actual` gold table (join logic)
- [ ] Backfill 180 days of history

### Phase 2: Comparison & Visualization (Weeks 4-6)
- [ ] Implement variance calculation logic
- [ ] Build plan vs. actual comparison views
- [ ] Create summary dashboards (category-level, planner-level)
- [ ] Validate against manual process (parallel run)

### Phase 3: Integration & Enrichment (Weeks 7-9)
- [ ] Connect to Control Tower or planning app UI
- [ ] Add root cause categorization framework
- [ ] Implement plan accuracy trending
- [ ] Add alerting for large variances

### Phase 4: Optimization & Scale (Weeks 10+)
- [ ] Performance tuning for historical queries
- [ ] Add drill-down capabilities (supplier, category, planner)
- [ ] Historical backfill
- [ ] User feedback incorporation

---

## 9. Open Items & Decisions Needed

### Resolved Items

| # | Item | Resolution |
| --- | --- | --- |
| ~~O1~~ | ~~Identify existing snapshot table names and schemas~~ | **RESOLVED** - `prod_edw.fact.20_supply_daily` with `process_date` (yyyyMMdd). Confirmed via Supply Historical Snapshots dashboard. |
| ~~O2~~ | ~~Define week boundary for actuals~~ | **RESOLVED** - Monday-Sunday. Monday AM snapshot reflects Sunday EOD state. |
| ~~O3~~ | ~~Confirm Oracle source tables for PO receipts and SO shipments~~ | **RESOLVED** - PO Receipts: `prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions`. Sales Shipped: `prod_edw.fact.sales_order_line_transactions`. On-Hand: `prod_edw.fact.inventory_days_on_hand`. |
| ~~O4~~ | ~~Determine catalog/schema for new actuals tables~~ | **RESOLVED** - `prod_operations` (derived/analytical layer). |
| ~~O5~~ | ~~Confirm SKU/Org grain~~ | **RESOLVED** - Item/Organization level (same grain as `20_supply_daily`), aggregated to weekly. |

### Remaining Open Items (with Recommendations)

| # | Item | Owner | Recommendation | Notes |
| --- | --- | --- | --- | --- |
| ~~O6~~ | ~~Define plan accuracy KPIs and thresholds~~ | Planning Manager | **DECIDED:** PO On-Time Receipt Rate >85% (+/-1 week). PO Quantity Accuracy >90% (+/-10%). On-Hand MAPE <15%. Demand Accuracy >80% (+/-20%). Stratify by ABC code (tighter for A items). Refine after 4-6 weeks of data. | **Resolved** |
| ~~O7~~ | ~~UI/Visualization approach~~ | TBD | **DECIDED:** Phase 1: Standalone AI/BI Dashboard (modeled after existing Supply Historical Snapshots pattern). Phase 2: Control Tower integration once validated. | **Resolved** |
| O8 | Define variance threshold for alerting/exceptions | Planning Team | **Tier 1 (Monitor):** >15% variance on any metric. **Tier 2 (Alert):** >30% variance OR >$50K cost impact. **Tier 3 (Escalate):** >50% variance OR >$200K cost impact OR missed safety stock. | Thresholds should differ by ABC code: A-items get tighter thresholds (10%/20%/40%), C-items get looser (25%/50%/75%). Use `applied_standard_cost` from `dim_series_ext_vw` for cost impact calculations. |
| O9 | Confirm `receiving_receipt_transactions` is the long-term PO receipt source | Data Engineering | **Recommendation:** Use `receiving_receipt_transactions` for now, but open a ticket with the EDW team to confirm the deprecation replacement for `purchase_order_delivery`. If a new fact table is planned, design the silver layer with an abstraction so the source can be swapped without downstream impact. | Build the silver table with a clear interface contract (item_id, org, week, qty_received) so the underlying source can change without breaking the gold layer. |
| O10 | Validate `process_date` covers full 180 days for backfill | Data Engineering | **Recommendation:** Run a quick validation query: `SELECT MIN(process_date), MAX(process_date), COUNT(DISTINCT process_date) FROM prod_edw.fact.20_supply_daily`. Also validate the transactional tables cover the same window. If gaps exist, document them and adjust backfill scope. | Should be a 5-minute validation task. Block Phase 1 pipeline build until confirmed. |

---

## 10. Success Criteria

| # | Criteria | Measurement | Target |
| --- | --- | --- | --- |
| S1 | Planner adoption | % of planners using tool weekly | >80% within 4 weeks of launch |
| S2 | Time savings | Hours saved per planner per week on reconciliation | >2 hours/week |
| S3 | Data accuracy | Match rate between tool output and manual validation | >99% |
| S4 | Freshness | Data available by Monday AM for prior week actuals | Before 8 AM Monday |
| S5 | Root cause identification | % of large variances with assigned root cause | >70% within first month |


