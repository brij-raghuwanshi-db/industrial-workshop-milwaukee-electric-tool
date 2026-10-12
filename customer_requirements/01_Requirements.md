%md
# Demand Planning Event Forecast App — Functional Requirements

## Overview

This application replaces the existing Excel-based process for collecting demand planning forecasts for non-repeating and repeating events. These are incremental forecasts above the baseline, typically driven by intelligence from customer or sales team coordination (e.g., store expansions, new product bay rollouts, promotional programs).

**Output tables:**
* `prod_edw.staging_flat_files.expansion_dims`
* `prod_edw.staging_flat_files.expansion_loads`

**Downstream system:** Oracle Demand Planning Cloud Fusion

**Platform:** Databricks App (Streamlit prototype)

---

## 1. Event Management

### 1.1 Event Identity
* **EXP ID**: Auto-generated sequential integer. Each new event = max(existing ID) + 1. Immutable once assigned.
* **Event Name**: Freeform text entered by the planner.
* **Event Type**: User selects one or both:
  * **Non-repeating event** (formerly "Expansion Load In") — one-time stocking volume excluded from statistical forecast history
  * **Repeating event** (formerly "Run Rate") — ongoing volume retained in forecast history

### 1.2 Event Status (Three-state lifecycle)

| Status | Behavior |
| --- | --- |
| In Progress | Draft — planner still working; NOT exported to output tables |
| Active | Finalized — included in daily output to Oracle |
| Deactivated | Soft-delete — removed from output; data retained in staging |

### 1.3 Event Locking
* Only one planner can edit an event at a time.
* Other users can view but not modify a locked event.
* Lock released on save/close or via timeout.

### 1.4 Audit Trail
* **Created by** (user identity + timestamp)
* **Last modified by** (user identity + timestamp)
* **Change log**: Granular tracking of who changed what value, when, and before/after state (item/month/field level)

---

## 2. Event Header (Metadata)

| Field | Description | Behavior |
| --- | --- | --- |
| Number of Stores | Stores impacted by the event | Input by planner; used in Forecast Builder calculations |
| Ship Date | Planned ship date | Input by planner; informational for analysis |
| Ship Month | Derived from Ship Date | Auto-populated |
| Set Month | Month the product is set on shelf | Input by planner; informational for analysis |
| Organization | Oracle ship-from distribution center code | Auto-populated (2012 default; 2120 for Mexico/THD MEX); overridable |
| Tags | Categorization labels | Multi-select; for filtering/reporting |
| Comments/Notes | Freeform text | For collaboration context |

---

## 3. Customer Selection

### 3.1 Multi-Select Enhancement
* Users can select **multiple customers** per event (enhancement over single-select in Excel).
* Source: `prod_edw.dimension.dg5_customer_scd1`

### 3.2 Hierarchy Level Input
The customer hierarchy has 6 levels:

| Level | Description | Example |
| --- | --- | --- |
| mkedg0 | 3rd Party vs Intercompany | 3rd Party |
| mkedg1 | Geography | DOM, CAN |
| mkedg2 | Channel (THD vs non-THD) | OTD, CAN THD |
| mkedg3 | Sub-channel | HDW, IC FLD |
| mkedg4 | Category | FARM, HDW |
| mkedg5 | Individual customer code (output grain) | ACE, BLAINS, THD CAN |

**Workflow:**
1. User selects which customers are impacted
2. User selects the hierarchy level to provide input at
3. User enters forecast values at that level
4. App disaggregates to mkedg5 for output

### 3.3 Disaggregation
* **Method**: Ratio-based — each mkedg5's share = its measure value / total measure value for the group
* **Available measures** (from `prod_edw.fact.10_demand_daily`):
  * `working_final_forecast`
  * `planner_baseline_forecast`
  * (4-5 additional measures TBD — fast follow)
* **Output grain**: One row per mkedg5 per item per month

---

## 4. Item Entry

### 4.1 Input Method
* Freeform entry (planners work from lists provided by Sales/Marketing)
* Bulk import (paste from Excel)
* Items are existing SKUs from the Item Master

### 4.2 Validation
* Validate against `prod_edw.dimension.items_scd1`
* **Primary rule**: `item_status_description` must indicate Status 20
* **Behavior**: Warning flag (non-blocking) — items that fail can still be saved but are flagged
* **Extensibility**: Additional validation criteria to be added later

> ⚠️ **Action Item**: Confirm exact field/value logic with analytics engineering team after prototype.

---

## 5. Time Dimension

* **Start month**: User-selected (first of month)
* **End month**: User-selected; maximum = first of the month 23 calendar months from today
  * Example: If today is 7/27/2026, max end date = 8/1/2028
* **Granularity**: Monthly buckets
* **Generation**: App auto-generates all months between start and end
* **Values**: Planner populates quantities where applicable; blanks are valid (no forecast for that month)

---

## 6. Forecast Values

* **Unit of measure**: Always quantity (units)
* **Two input modes**:
  1. **Direct entry** — Planner keys in predetermined values on the main page
  2. **Forecast Builder** — Separate page; calculates values from assumptions, pushes to main page
* **Override**: After Forecast Builder populates values, planner can manually override any cell

---

## 7. Forecast Builder (Separate Page)

### 7.1 Inputs

| Field | Scope | Description |
| --- | --- | --- |
| Number of Stores | Header or Line | Stores in the event |
| Load Per Store | Header or Line | Initial stocking qty per store (non-repeating) |
| ASPV | Header or Line | Average monthly run rate per store (repeating) |
| Confidence | Header or Line | Informational indicator of inclusion likelihood |
| Lift | Header or Line | Provided externally by Sales/Marketing; reference only |

* Header-level values apply uniformly to all items
* Line-level values override header when provided (per-item specificity)

### 7.2 Calculations
* **Non-repeating event value** = `# stores × Load Per Store` → placed on the start date
* **Repeating event value** = `# stores × ASPV` → spread across all monthly periods

### 7.3 Workflow
1. Planner enters assumptions in Forecast Builder
2. App calculates values
3. Values are pushed to the main data entry page
4. Planner can override individual item/month values on the main page

---

## 8. Output Specification

### 8.1 Target Tables

**`prod_edw.staging_flat_files.expansion_dims`**

| Column | Type | Description |
| --- | --- | --- |
| number_of_expansion_stores | STRING | Number of stores |
| ship_date | TIMESTAMP | Ship date |
| ship_month | STRING | Ship month (e.g., "March 2026") |
| set_month | STRING | Set month (e.g., "April 2026") |
| file_name | STRING | Event identifier (e.g., "EXP001115 PPE 2 Bay.xlsx") |
| file_index | INT | Row index |
| hash_diff | STRING | Hash for change detection |
| run_id | STRING | Batch run identifier |
| record_source | STRING | Source system identifier |
| load_date | TIMESTAMP | Load timestamp |

**`prod_edw.staging_flat_files.expansion_loads`**

| Column | Type | Description |
| --- | --- | --- |
| expansion_name | STRING | Event name |
| item_number | STRING | SKU/item number |
| customer | STRING | mkedg5 customer code |
| variable | STRING | Monthly date bucket (e.g., "2026-08-01 00:00:00") |
| load_value | STRING | Quantity (units) |
| file_name | STRING | Event identifier |
| file_index | INT | Row index |
| hash_diff | STRING | Hash for change detection |
| run_id | STRING | Batch run identifier |
| record_source | STRING | Source system identifier |
| load_date | TIMESTAMP | Load timestamp |

### 8.2 Output Rules
* Only **Active** events are exported
* **Daily batch**: Truncate and reload all active events
* **Timing**: Must be complete before 5PM pickup by data warehouse team
* **Grain**: One row per mkedg5 per item per month

> ⚠️ **Design Decision**: Truncate/reload vs. incremental merge — developer to evaluate for production.

---

## 9. Enhancements (Beyond Current Excel Process)

### 9.1 Core Enhancements
* Multi-select customer (vs. single in Excel)
* Customer hierarchy level input with disaggregation
* Forecast Builder with header/line-level assumptions
* Event status lifecycle (In Progress / Active / Deactivated)
* Event-level locking for concurrent users
* Full audit trail with change tracking

### 9.2 UX Enhancements
* Search/filter events by name, customer, status, date range
* Bulk import of items (paste from Excel)
* Duplicate event as template for new events
* Export to Excel for stakeholder sharing
* Comments/notes per event
* Tagging/categorization for filtering and reporting
* Bulk status changes (activate/deactivate multiple events)

### 9.3 Analytical Enhancements
* **Summary dashboard**: Aggregate incremental forecast across all active events by customer/month
* **Baseline comparison**: Show `planner_baseline_forecast` alongside event input
* **Validation summary**: Pre-publish checklist of all warnings/errors across active events

### 9.4 Operational Enhancements
* Notifications/alerts (batch run success/failure)
* Auto-deactivation for events past their date range (→ Completed/Expired status)

---

## 10. Users & Access

* **Primary users**: Demand planners on the demand team
* **Access model**: All planners can see all events; edit restricted by event lock
* **No approval workflow**: Submission by planner = ready to load
* **Concurrent usage**: Multiple planners work on different events simultaneously

---

## 11. Terminology (Rebranding)

| Old Term | New Term |
| --- | --- |
| Expansion | Event |
| Expansion Load In | Non-repeating event |
| Run Rate | Repeating event |

---

## 12. Open Items & Action Items

| # | Item | Owner |
| --- | --- | --- |
| 1 | Confirm item validation field/value logic (item_status_description = Status 20) | Analytics Engineering |
| 2 | Define additional item validation criteria | Business / Analytics Engineering |
| 3 | Define 4-5 additional disaggregation measures | Demand Planning |
| 4 | Evaluate truncate/reload vs. incremental merge for production | Developer |
| 5 | Define notification recipients and channels | Demand Planning |
| 6 | Define tagging taxonomy | Demand Planning |
| 7 | Platform decision (Streamlit vs. alternative) for production | App Development Team |