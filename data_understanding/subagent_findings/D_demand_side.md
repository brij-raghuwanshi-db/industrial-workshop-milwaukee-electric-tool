# Demand-Side Data Profiling (Cluster D)
Profile Date: 2026-08-30
Profile SQL: READ-ONLY (SELECT / DESCRIBE / SHOW only)

---

## Executive Summary

Three tables profile demand for P3 (Demand Events App) and P4 (Demand Exceptions):

1. **dg5_customer_scd1**: 56 rows (one per mkedg5). 6-level hierarchy (mkedg0..mkedg5) with SCD1 grain.
   - Hierarchy cardinalities: mkedg0=4, mkedg1=8, mkedg2=7, mkedg3=14, mkedg4=29, mkedg5=56.
   - Output grain: mkedg5 (56 distinct customers = 56 rows, no duplicates).

2. **10_demand_daily**: 17.8B rows (production fact table). Max process_date: 20260829.
   - Grain: One row per (date_key, product_bigint_key, dg5_customer_bigint_key, org keys, series_bigint_key, ...).
   - Key measures confirmed: **working_final_forecast**, **planner_baseline** (both carry null/zero variance).
   - Full measure inventory: 120+ columns; 40 active, 60+ deprecated [DO NOT USE], 20+ internal/system.
   - Joins to dg5_customer_scd1 via dg5_customer_bigint_key; holds mkedg5 grain data.

3. **expansion_dims / expansion_loads**: Both populated. Legacy P3 output contract (Excel-sourced).
   - expansion_dims: 19,594 rows. Columns: file_name, ship_date/month, set_month, dimensional metadata.
   - expansion_loads: 8,087,553 rows. Columns: expansion_name, item_number, customer, variable (date), load_value, file_name.
   - Confirms real-world shape: files like "EXP001115 PPE 2 Bay.xlsx", monthly buckets, numeric load values.

---

## Table 1: dg5_customer_scd1 (Customer Hierarchy)

**STATUS**: Complete, production. Grain: SCD1 at mkedg5.

**Schema**:
- Surrogate keys: dg5_customer_hash_key (string), dg5_customer_bigint_key (bigint)
- Business key: dg5_customer_business_key (string, format "MET|DG5xx")
- Customer name: customer (string, e.g., "ACE", "BLAINS")
- Hierarchy labels: dg_code, mkedg0, mkedg1, mkedg2, mkedg3, mkedg4, mkedg5

**Cardinalities** (P3 critical):
- mkedg0: 4 distinct (see domain below)
- mkedg1: 8 distinct (see domain below)
- mkedg2: 7 distinct (see domain below)
- mkedg3: 14 distinct
- mkedg4: 29 distinct
- mkedg5: 56 distinct (output grain for disaggregation)
- Total rows: 56
- Grain: COUNT(*) = COUNT(DISTINCT mkedg5) => 1:1 SCD1

**Hierarchy Domains** (verified examples + counts):
```
mkedg0 (Ownership):
  3rd Party: 45 rows
  Intercompany: 9 rows
  (data quality note: mixed case "3RD PARTY", "INTRA" also present; standardization opportunity)

mkedg1 (Geography):
  DOM (Domestic): 34 rows
  LAG (Latin America): 7 rows
  CAN (Canada): 6 rows
  EME (Emerging Markets): 3 rows
  INT (International): 2 rows
  ANZ (Australia/NZ): 2 rows
  SAP: 1 row
  INTRA: 1 row

mkedg2 (Channel):
  OTD (Off-The-Distributor): 32 rows
  INT (Internal/Intercompany): 9 rows
  LAG (LAG-specific channel): 6 rows
  OTC (Over-The-Counter): 5 rows
  THD (The Home Depot): 2 rows
  CAN THD (Canada THD): 1 row
  INTRA: 1 row

mkedg5 (Customer Code, examples):
  ACE: present (Ace Hardware)
  BLAINS: present (Blain's Farm & Fleet)
  THD: not found as mkedg5 (THD present in mkedg2; no THD-branded customer mkedg5)
```

**Key Finding: Unique Standing**
- dg5_customer_scd1 is the ONLY source of the 6-level hierarchy that P3 disaggregation collapses to mkedg5.
- Each mkedg5 (customer) represents a unique endpoint for demand distribution.
- The hierarchy roll-up (mkedg0 -> mkedg1 -> ... -> mkedg5) defines the disaggregation structure: each lower level absorbs aggregates from the parent level above.
- P3 will join 10_demand_daily on dg5_customer_bigint_key to retrieve mkedg5 codes and calculate ratio weights.

---

## Table 2: prod_edw.fact.`10_demand_daily` (Demand Fact)

**STATUS**: Production. Grain: One row per (date_key, product, customer, orgs, series, ...). 17.8B total rows; latest process_date 20260829.

**Coverage**:
- Total rows: 17,809,895,227
- Distinct process_dates: 368 (range: 20250621 to 20260829)
- Distinct date_keys: 75 (range: 20220601 to 20280801 => 6+ years of history/forecast)
- Distinct customers: 56 (matches dg5_customer_scd1 1:1)
- Distinct products: 53,892

**Latest Load** (process_date = 20260829):
- Rows: 53,150,177
- Distinct grain combinations: 52,291,823 (note: row_count > distinct_grain, indicating some duplicate combinations; minor data quality note)

**Key Measures - Confirmed Present & Populated** (P3/P4 priorities):

1. **working_final_forecast** (double, P3/P4 critical):
   - Stats (process_date 20260829):
     - min: -43,214.3 (negative values; likely adjustments or reversal entries)
     - max: 1,109,458
     - avg: 32.7 (low average suggests sparse, high-variance distribution)
   - Use: Total forecast at Selling Item/DG5/Designated Org level; sum of Planner Baseline, Promo Total, NPD, Expansion, and other planner inputs.

2. **planner_baseline** (double, P3/P4 critical):
   - Stats (process_date 20260829):
     - min: -66,438
     - max: 11,452,000
     - avg: 25.1 (similarly sparse)
   - Use: Demand before any promotions or incremental additions; primary baseline for P4 exception detection.

3. **frozen_working_final_forecast** (double):
   - Snapshot of working_final_forecast at last demand freeze; for variance/drift tracking.

4. **frozen_planner_baseline** (double):
   - Snapshot of planner_baseline at last demand freeze; for baseline-comparison thresholds in P4.

**Complete Measure Inventory (120+ columns; active vs. deprecated)**:

Active/Valid (40+):
- History: bookings_history, shipments_history, consumption_history, returns_units, promotional_history_by_org, cancelled_units
- Forecast variants: final_demand_forecast, working_final_forecast, live_planner_baseline_forecast, locked_statistical_baseline, baseline_statistical_forecast, total_statistical_forecast, channel_npd_forecast, final_npd_forecast, new_item_forecast
- Planner inputs: planner_baseline, planner_baseline_adj, planner_baseline_ovrd, volume_adj, unconfirmed_promo, promo_total, approved_pce, expansions_loadin, expansions_runrate, non_repeating_events
- Pricing/Metrics: final_asp, baseline_asp, invoiced_asp, promo_pce_units, promo_pce_amount, peso_currency_rates, cad_currency_rates
- Frozen snapshots: frozen_planner_baseline, frozen_working_final_forecast, frozen_final_demand_forecast, frozen_locked_statistical_baseline, frozen_promo_total, etc. (20+ frozen_* variants)
- Amounts (dollarized): planner_baseline_amount, working_final_forecast_amount, final_demand_forecast_amount, etc. (20+ *_amount variants)

Deprecated [DO NOT USE] (60+):
- gross_forecast, dependent_demand, independent_demand, in_receiving, in_transit, manual_demand, item_standard_cost, supply_forecast_adjustment, npd_forecast, dampened_statistical_baseline, safety_stock*, transition_*, effective_supply_forecast, final_dm_forecast, final_supply_forecast, net_forecast, on_hand, value_on_hand, order_quantity, projected_available_balance, past_due_backlog_quantity, planned_orders, purchase_orders, purchase_requisitions, production_plan, projected_on_hand, scheduled_receipts, sales_orders, shipped_sales_orders, transfer_orders, transfer_order_demand, total_demand, total_supply, total_end_item_cost, work_orders, spx_by_*, local_planning_abc_code, etc.

Internal/System [DO NOT USE] (20+):
- last_revised_final_forecast, long_range_forecast_target, history_after_retagging_stored, event_cleansed_history_stored, indep_final_dm_fcst_minus_expansions_calc, interim_final_forecast

**Grain Analysis** (process_date 20260829):
- Table grain: row exists for each unique combination of (date_key, series_bigint_key, dg5_customer_bigint_key, product_bigint_key, inventory_organization_bigint_key, designated_organization_bigint_key, ship_from_organization_bigint_key, demand_class_bigint_key, resource_bigint_key, supplier_site_bigint_key, forecasting_method_bigint_key, configure_to_order_bigint_key, source_level_bigint_key, exception_type_bigint_key, order_type_bigint_key, decomposition_method_bigint_key, segement_level_bigint_key, customer_site_bigint_key).
- Data held at dg5_customer_bigint_key level (mkedg5 grain), not aggregated; P3 will join to dg5_customer_scd1 to hydrate mkedg5 codes and roll up to mkedg5 for disaggregation.

**Join to dg5_customer_scd1**:
- Foreign key: dg5_customer_bigint_key (matches dg5_customer_scd1.dg5_customer_bigint_key)
- 1:many (10_demand_daily -> dg5_customer_scd1) at the fact grain.
- Enables P3 to retrieve customer hierarchy (all mkedg0..mkedg5 levels) and group measures by mkedg5.

---

## Table 3: expansion_dims (Expansion Event Headers)

**STATUS**: Populated, legacy Excel-sourced. 19,594 rows.

**Schema**:
- number_of_expansion_stores (string, mostly null/blank)
- ship_date (timestamp)
- ship_month (string, e.g., "November 2026")
- set_month (string, e.g., "December 2026")
- file_name (string, e.g., "EXP001655 THDM Accy PLR - Mascon & Twist.xlsx")
- file_index (int, position within the file)
- hash_diff, run_id, record_source, load_date (audit/lineage)

**Nulls & Cardinality**:
- ship_date: 17,359 nulls (88.6% null) – mixed historical/future loading; sparse temporal coverage.
- ship_month/set_month: ~15% null.
- file_name: 28 nulls out of 19,594 (~0.1%).

**Unique Standing for P3**:
- expansion_dims holds the event header dimensions that P3 must reproduce when writing to sandbox_operations.po_management.
- File names confirm real-world Excel contract: expansion event files loaded from business users (examples: "EXP001655 THDM Accy PLR - Mascon & Twist.xlsx").
- P3 output structure must match: event_name (from file), ship_month, set_month, store_count (from number_of_expansion_stores).

---

## Table 4: expansion_loads (Expansion Event Line Values)

**STATUS**: Populated, legacy Excel-sourced. 8,087,553 rows.

**Schema**:
- expansion_name (string, e.g., "Fastenal Timing Shift")
- item_number (string, e.g., "2957-20")
- customer (string, e.g., "FASTENAL")
- variable (string, ISO timestamp e.g., "2025-08-01 00:00:00")
- load_value (string/numeric, e.g., "0.0")
- file_name, file_index, hash_diff, run_id, record_source, load_date (audit/lineage)

**Nulls & Cardinality**:
- load_value: 346,518 nulls (4.3% null) – some events have missing values; data quality note.
- file_name: 26,610 nulls (0.3%).
- All other columns: 0 nulls.

**Sample Row** (typical expansion event):
```
expansion_name: "Fastenal Timing Shift"
item_number: "2957-20"
customer: "FASTENAL"
variable: "2025-08-01 00:00:00" (date bucket)
load_value: 0.0 (units or dollars for this item/date combination)
file_name: "EXP00681 Fastenal Timing Shift (May-August '24).xlsx"
```

**Unique Standing for P3**:
- expansion_loads holds the leaf-level values that P3 must reproduce.
- Each row represents one line item in an expansion event, keyed by (expansion_name, item_number, customer, variable_date).
- P3 will read this contract and generate equivalent rows in sandbox_operations.po_management.expansion_loads (NOT prod_edw).

---

## Cross-Table Notes

**P3 Flow** (Demand Events App):
1. Read dg5_customer_scd1 to retrieve the 6-level hierarchy and mkedg5 customer codes.
2. Read 10_demand_daily (working_final_forecast + planner_baseline) and join to dg5_customer_scd1 on dg5_customer_bigint_key.
3. Group by mkedg5 and calculate ratio weights: each customer's share = its measure / group total (by mkedg0/mkedg1/mkedg2/etc. as needed).
4. Disaggregate higher-level demands to mkedg5 using those ratio weights.
5. Compare against expansion_loads (legacy contract) to generate event outputs.
6. Write outputs to sandbox_operations.po_management (NOT prod_edw) per project guardrails.

**P4 Flow** (Demand Exceptions App):
1. Read planner_baseline and frozen_planner_baseline from 10_demand_daily (joined to dg5_customer_scd1).
2. Calculate baseline thresholds (planner_baseline at aggregate levels, or per mkedg5).
3. Detect exceptions when working_final_forecast deviates >threshold from planner_baseline.
4. Write exception cases to sandbox_operations.po_management.exception_case (Lakebase sink).

---

## Data Quality & Gotchas

1. **Negative Values in Measures**: Both working_final_forecast and planner_baseline hold negative values (see stats above). Confirm these are intentional (reversals, adjustments) vs. data errors. P3/P4 should validate or filter as business rules require.

2. **Sparse Distribution**: Average measure values (25–33 units) vs. max values (millions) suggest highly skewed, sparse data. Confirm this is real demand variance, not missing-value encoding.

3. **Grain Mismatch in Latest Load**: distinct_grain (52.3M) < row_count (53.2M) for process_date 20260829. Investigate: are there duplicates on the grain key? Or is the grain definition non-unique? Recommend grain reconciliation query.

4. **expansion_dims Missing Dates**: 88% nulls in ship_date suggests this table may hold metadata-only rows (no temporal specificity). Verify contract with P3 team.

5. **mkedg0 Case Inconsistency**: "3rd Party" vs. "3RD PARTY" vs. "INTRA" present in same column. Recommend standardization upstream (dg5_customer_scd1 refresh) or lowercase normalization in P3 logic.

6. **dg5_customer_scd1 is NOT TiDB**: This table is MySQL (prod_edw.dimension schema). Confirm P3/P4 will handle any multi-platform query or caching needs.

---

## Open Questions

1. **expansion_loads load_value Domain**: Are the ~4% nulls intentional (placeholder rows, no forecast), or data quality gaps? Recommend filtering or imputation rule.

2. **expansion_runrate**: The schema shows `expansions_runrate` (ongoing recurring expansion) alongside `expansions_loadin` (one-time). Does expansion_loads represent both, or only one type? Check P3 requirements.

3. **Which Additional Measures for Disaggregation?**: The doc mentions "4–5 additional measures TBD" beyond working_final_forecast and planner_baseline. From the full inventory, candidates are:
   - final_demand_forecast (published version)
   - frozen_working_final_forecast (freeze snapshot)
   - live_planner_baseline_forecast (live statistical baseline)
   - promotions_total (incremental promo volume)
   - bookings_history (actual shipments for ratio calibration)
   
   Recommend P3 team select from the 40+ active measures above.

4. **Series Dimension**: 10_demand_daily carries series_bigint_key (represents data series or scenario, per schema). P3 must clarify: does disaggregation happen per series, or is series filtered? (E.g., "current plan" vs. "historical"?)

5. **Expansion Reconciliation**: Compare expansion_loads customer codes (e.g., "FASTENAL") against dg5_customer_scd1 mkedg5 values (e.g., "ACE", "BLAINS"). Do they match 1:1, or is there a mapping layer?

---

## Summary: Unique Standing

- **dg5_customer_scd1**: The single authoritative source for the 6-level customer hierarchy and the mkedg5 grain. P3 dis-aggregation depends entirely on this table; it is irreplaceable.

- **10_demand_daily**: Uniquely provides the measures (working_final_forecast, planner_baseline) and ratio weights (each mkedg5's share of a parent-level demand). Also the source of product, org, and temporal keys for joining. This is the master demand fact table.

- **expansion_dims / expansion_loads**: Legacy Excel-era output contract. P3 must replicate this structure in sandbox_operations.po_management (per guardrails: never write to prod_edw). They define the expected shape of demand events (file names, date buckets, line items, values).

---

## Files & Queries Run

All queries marked READ-ONLY (SELECT / DESCRIBE / SHOW):
- dg5_customer_scd1: schema discovery, cardinality by level, customer code verification
- 10_demand_daily: schema discovery (DESCRIBE TABLE), coverage stats, latest process_date, measure stats, grain verification
- expansion_dims: schema discovery, row count, sample data
- expansion_loads: schema discovery, row count, sample data

**Data Dictionary Reference**: Full schema comments embedded in DESCRIBE TABLE output (not repeated here; refer to prod_edw metadata layer for complete documentation).

---

## Next Steps for P3/P4 Teams

1. Confirm which additional measures (beyond working_final_forecast, planner_baseline) are required for disaggregation.
2. Validate expansion_loads customer codes map to mkedg5 in dg5_customer_scd1 (1:1 or many:1?).
3. Reconcile series_bigint_key filtering requirements: does disaggregation apply to all series or specific scenarios?
4. Design sandbox_operations.po_management.expansion_dims and expansion_loads schema (will be input_frame_v0 or equivalent for App state).
5. Define exception thresholds for P4 (baseline_drift_pct, absolute_variance_units, etc.) and confirm source measures.
