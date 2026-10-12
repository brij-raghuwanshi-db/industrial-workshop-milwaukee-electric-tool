# Databricks notebook source
# MAGIC %md
# MAGIC # RC serving-layer weekly refresh
# MAGIC Rebuilds all `sandbox_operations.po_management.rc_*` tables from the latest Monday snapshot.
# MAGIC READ-ONLY on prod_edw/prod_operations; writes only to sandbox_operations.po_management.
# MAGIC Ordered build/01..14; ends with a reconciliation + populated-table gate that FAILS the run on drift or empty core tables.

# COMMAND ----------
# MAGIC %md ### 01_rc_run_control
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 01 · rc_run_control
-- Pins the snapshot every downstream rc_* table reads, so builds are deterministic & reconcilable.
-- WRITE TARGET: sandbox_operations.po_management  (READ-ONLY on prod_edw / prod_operations)
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_run_control AS
SELECT
  'wave0_plus'                                   AS run_label,
  (SELECT MAX(process_date) FROM prod_edw.fact.`20_supply_daily`)      AS supply_process_date,
  (SELECT MAX(process_date) FROM prod_edw.fact.`10_demand_daily`)      AS demand_process_date,
  '20 Global Supply Plan'                        AS supply_plan_name,
  20261130                                       AS forward_window_end,
  current_timestamp()                            AS build_ts;
""")
print("01_rc_run_control: done")

# COMMAND ----------
# MAGIC %md ### 02_rc_serving_sku_week
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 02 · rc_serving_sku_week  (THE SPINE)
-- One row per SKU × org × forward-week for the full 20 Global book at the pinned snapshot.
-- Reuses verified SQL: ER §7.1 (PAB / SS-at-lead-time), measures §2/§3 + ADR §7.1a (classifier).
-- WRITE TARGET: sandbox_operations.po_management   READ-ONLY on prod_edw / prod_operations.
--
-- Hazards honored: #1 product_bigint_key→item; #3 pin process_date; #6 backtick digit-tables;
--   #10 full plan-name string; #15 BOOLEAN lifecycle flags (=true); dim_series_ext_vw in prod_operations.edw_extension;
--   #17 (holds handled elsewhere). Bimodal lead time: per-SKU complete_lead_time, never averaged.

CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_serving_sku_week AS
WITH ctrl AS (SELECT * FROM sandbox_operations.po_management.rc_run_control),

-- ── base forward rows: full 20 Global book, pinned snapshot, forward window ──
--    ⚠ GRAIN: 20_supply_daily has up to 6 rows per item×org×date_key (finer sub-grain). Collapse to a clean
--    item×org×date_key grain FIRST: position measures (PAB/on_hand/SS) are per the plan row → take MAX (they
--    repeat), additive flows (demand/supply/receipts) → SUM. This prevents downstream fan-out inflation.
base AS (
  SELECT
    s.product_bigint_key, s.inventory_organization_bigint_key,
    MAX(s.designated_organization_bigint_key) AS designated_organization_bigint_key,
    MAX(s.series_bigint_key)                   AS series_bigint_key,
    s.date_key, s.process_date,
    MAX(s.projected_available_balance)         AS pab,
    MAX(s.on_hand)                             AS on_hand,
    MAX(s.safety_stock)                        AS safety_stock,
    SUM(s.total_demand)                        AS total_demand,
    SUM(s.total_supply)                        AS total_supply,
    SUM(s.scheduled_receipts)                  AS scheduled_receipts,
    SUM(s.independent_demand)                  AS independent_demand,
    SUM(s.dependent_demand)                    AS dependent_demand
  FROM prod_edw.fact.`20_supply_daily` s
  JOIN ctrl ON s.process_date = ctrl.supply_process_date
  WHERE s.plan_name = '20 Global Supply Plan'
    AND s.date_key BETWEEN ctrl.supply_process_date AND (SELECT forward_window_end FROM ctrl)
  GROUP BY s.product_bigint_key, s.inventory_organization_bigint_key, s.date_key, s.process_date
),

-- ── per-SKU×org aggregates: low point, first cross, chronicity within window ──
agg AS (
  SELECT product_bigint_key, inventory_organization_bigint_key,
         designated_organization_bigint_key, series_bigint_key,
         MIN(pab)                                          AS min_pab,
         MAX(safety_stock)                                 AS ss_max,
         MIN(CASE WHEN pab < safety_stock THEN date_key END) AS first_below_ss_week,
         MIN(CASE WHEN pab < 0 THEN date_key END)          AS first_neg_week,
         SUM(CASE WHEN pab < safety_stock THEN 1 ELSE 0 END) AS weeks_below_ss,
         COUNT(DISTINCT date_key)                          AS weeks_in_window,
         SUM(total_demand)                                 AS sum_demand,
         SUM(total_supply)                                 AS sum_supply,
         SUM(independent_demand)                           AS sum_indep_demand,
         SUM(dependent_demand)                             AS sum_dep_demand
  FROM base
  GROUP BY product_bigint_key, inventory_organization_bigint_key,
           designated_organization_bigint_key, series_bigint_key
),

-- ── item master (lifecycle — BOOLEAN flags, hazard #15) ──
itm AS (
  SELECT item_bigint_key, item AS item_id, selling_item_number, item_description,
         transition_sku_flag, is_npd_item
  FROM prod_edw.dimension.items_scd1
),

-- ── series ext (criticality/ABC, lead time, cost, managed-SS) — prod_operations.edw_extension ──
ser AS (
  SELECT series_bigint_key, inventory_abc_class, complete_lead_time,
         standard_cost, safety_stock_managed_flag
  FROM prod_operations.edw_extension.dim_series_ext_vw
),

-- ── committed unit value (stakes) — governed commitment fact, ONE row per item (avg unit cost) ──
--    NOTE: fact_sop_commitment is grained by DG5×org — collapse to one avg unit cost per item to avoid fan-out.
--    standard_cost (dim_series_ext_vw) is the primary unit cost; committed cost is a cross-check only.
cmt AS (
  SELECT item_bigint_key,
         AVG(frozen_blended_lag1_forecast_cost) AS committed_unit_cost
  FROM prod_operations.demand.fact_sop_commitment
  WHERE frozen_blended_lag1_forecast_cost > 0
  GROUP BY item_bigint_key
)

SELECT
  -- keys
  itm.item_id, itm.selling_item_number, itm.item_description,
  b.product_bigint_key, b.inventory_organization_bigint_key,
  b.designated_organization_bigint_key, b.series_bigint_key,
  b.date_key, b.process_date,
  -- position
  b.pab AS projected_available_balance, b.on_hand, b.safety_stock,
  -- derived gap (measures §3.1)
  (b.pab - b.safety_stock)                 AS ss_gap,
  GREATEST(0, b.safety_stock - b.pab)      AS shortfall_units,
  -- waterfall buckets (demand vs supply share of the gap; holds handled in drill)
  b.total_demand, b.total_supply, b.scheduled_receipts,
  b.independent_demand, b.dependent_demand,
  -- likely cause + confidence (dominance of demand vs supply pressure)
  CASE
    WHEN b.total_demand >= b.total_supply THEN 'Demand'
    ELSE 'Supply'
  END                                      AS likely_cause,
  ROUND(ABS(b.total_demand - b.total_supply) / NULLIF(b.total_demand + b.total_supply,0), 3) AS cause_confidence,
  -- stakes
  ser.standard_cost                        AS std_cost,
  GREATEST(0, b.safety_stock - b.pab) * COALESCE(cmt.committed_unit_cost, ser.standard_cost) AS committed_value,
  -- ═══════════ CLASSIFIER LAYER (ADR §7.1a) — per SKU×org, joined from agg ═══════════
  -- flag gate: an item is only "flagged" if it dips below safety stock at least once in the window
  -- severity (V1): healthy (never dips) / below-SS-target / projected-negative-PAB
  CASE WHEN a.weeks_below_ss = 0 THEN 'healthy'
       WHEN a.min_pab < 0 THEN 'projected-negative-PAB'
       ELSE 'below-SS-target' END                                                  AS severity_class,
  -- temporal (V10): chronic if below SS in >=6 of the forward weeks
  CASE WHEN a.weeks_below_ss >= 6 THEN 'chronic'
       WHEN a.weeks_below_ss >= 1 THEN 'acute' ELSE 'none' END                     AS temporal_class,
  -- recoverability (V13/ADR §7.1a): committed loss if lead time > days to first stockout. NEVER average lead time.
  CASE
    WHEN a.first_neg_week IS NULL THEN 'RECOVERABLE'
    WHEN ser.complete_lead_time IS NULL THEN 'UNKNOWN'
    WHEN ser.complete_lead_time >
         DATEDIFF(to_date(CAST(a.first_neg_week AS STRING),'yyyyMMdd'),
                  to_date(CAST(b.process_date AS STRING),'yyyyMMdd'))
      THEN 'UNRECOVERABLE' ELSE 'RECOVERABLE' END                                  AS recoverability_class,
  -- action verdict (V12): healthy never flags; dips-but-never-negative = DISMISS (cushion dip);
  --   projected negative = ACT; below-target-but-nonneg-with-real-risk = WATCH
  CASE
    WHEN a.weeks_below_ss = 0 THEN 'none'
    WHEN a.first_neg_week IS NOT NULL THEN 'ACT'
    WHEN a.min_pab >= 0 THEN 'DISMISS'
    ELSE 'WATCH' END                                                               AS action_verdict,
  -- convergence placeholder (filled by rc_scenario/pattern join later; 1 = single-cause default)
  1                                                                                AS convergence_score,
  -- damage-control path (V13): unrecoverable → TRANSFER if in-network excess else ALLOCATE
  CASE WHEN ser.complete_lead_time >
            DATEDIFF(to_date(CAST(a.first_neg_week AS STRING),'yyyyMMdd'),
                     to_date(CAST(b.process_date AS STRING),'yyyyMMdd'))
       THEN 'ALLOCATE-ACCEPT' ELSE 'n/a' END                                       AS damage_control_path,
  -- criticality (V22/DK-16)
  COALESCE(UPPER(ser.inventory_abc_class),'UNCLASSIFIED')                          AS criticality_class,
  -- demand class (V24/DK-18) — ADI proxy: share of forward weeks with independent demand
  CASE
    WHEN a.weeks_in_window = 0 THEN 'no-demand'
    WHEN a.sum_indep_demand = 0 THEN 'no-demand'
    WHEN a.sum_indep_demand > 0 AND a.weeks_below_ss * 1.0 / a.weeks_in_window < 0.2 THEN 'intermittent'
    ELSE 'smooth' END                                                             AS demand_class,
  -- lifecycle (V15/N1) — BOOLEAN flags
  CASE WHEN itm.is_npd_item = true THEN 'NPD'
       WHEN itm.transition_sku_flag = true THEN 'transition'
       ELSE 'mature' END                                                          AS lifecycle_class,
  -- intentional hold (V26/DK-20)
  CASE WHEN ser.safety_stock_managed_flag = 'Yes' THEN 'Yes' ELSE 'No' END        AS intentional_hold,
  -- meta / provenance
  b.process_date                            AS snapshot_date,
  current_timestamp()                       AS freshness_ts,
  '20 Global Supply Plan'                   AS plan_name,
  'verified'                                AS position_tier
FROM base b
JOIN agg a  ON b.product_bigint_key = a.product_bigint_key
           AND b.inventory_organization_bigint_key = a.inventory_organization_bigint_key
JOIN itm    ON b.product_bigint_key = itm.item_bigint_key
LEFT JOIN ser ON b.series_bigint_key = ser.series_bigint_key
LEFT JOIN cmt ON b.product_bigint_key = cmt.item_bigint_key
WHERE itm.item_id IS NOT NULL;
""")
print("02_rc_serving_sku_week: done")

# COMMAND ----------
# MAGIC %md ### 03_rc_scenario_membership
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 03 · rc_scenario_membership
-- The 26 catalog scenarios x their extracted member IDs as first-class rows (the user's ask).
-- Seed = the 1,560 live-extracted IDs (in_seed_catalog=true); joined to the spine to mark coverage.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_scenario_membership AS
WITH seed(scenario_code, scenario_title, activity, requirement_map, source_table, predicate_note, item_id) AS (
  VALUES
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-25-1252'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-27-0180'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-32-4171'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-32-4579'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-32-4815'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-40-0720'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-62-4082'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-73-1321'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-73-1410'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-16-W247'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-57-5166'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6122'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6624'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-90-1979'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','50-44-0260'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','604BL-XL'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','606B-XL'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','77-0204'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','3401-20'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','M650K-3632'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6157T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6204T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6262T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-47-5711'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','CPPLH2001'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','CPPL2201'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','BLO1436'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','F452G-XLD'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-89-2217T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2772A-21J'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2821-21J'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2161-21J'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','PN0006103'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','PN0006130'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','PN0006141'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-22-7718V'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-1047T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-9086T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-94-0613'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2779-750CUZ'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-2122T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-2124T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-4000T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-9052T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-9053T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','45-34-9101T'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-73-7920V'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2941-21Z'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-73-5021BY'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-73-5071BY'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2123-21HDJ'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6654'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-66-6672'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','2971-20M'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-89-4870K'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','49-90-1976'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-22-3260X'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','51-16-2651ZX'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-81-4780'),
('V1','Watchlist / top-missing items','Act 1','R3,R4,C.5.1','20_supply_daily','PAB<safety_stock, latest snapshot','48-81-7760'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-39-0601'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-39-0616'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-62-4074'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-62-4082'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1221'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1232'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1321'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1501'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-16-2650'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-57-5166'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-59-2200P'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-90-1979'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-93-7025'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','602HV-XL'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','606B-XL'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','83-3'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','MLBX78'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','TBRG-B'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','3401-20'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','204-SS'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','58-10-7021'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','M650K-3632'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-32-4089ZA'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','M102B-L-W'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','BLO1436'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','F452G-XLD'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','2772A-21J'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','2161-21J'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','3632-21PO'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','MT210X'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','PN0004637'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-22-7718V'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','2941-21Z'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-5021BY'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','3650-21PMAN'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-5071BY'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','2971-20M'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-90-1976'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','2118-20'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','3651-21XCW'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','MT203H'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','51-16-2651ZX'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-81-4780'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-81-7760'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','FG58-28-0696'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','58-31-8235'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-22-9486T'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-32-4289'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-22-8933V'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1097'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-1331'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-3151P'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-73-5072'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','48-89-4632'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-16-U001C'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-22-4036'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-66-5124'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-66-6376'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-66-6642'),
('V2','Hard projected stockout (PAB<0)','Act 4','R6,R7,D,PAB','20_supply_daily','PAB<0','49-94-4510'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4145'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4171'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4191'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4846'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4020'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4142'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5143'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4118'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-39-0551'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4194'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-20-9130'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4786'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4112'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-62-4061'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-62-4098'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-66-6503'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5420'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5220'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5235'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4862'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-52-1305'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5240'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4025'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-40-4355'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5550'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4189'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4244'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4397'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-44-0155'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4671'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4832'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-62-3010'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-28-1000'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4431'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4687'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4711'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4195'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4135'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5335'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-5720'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4597'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-5020'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-40-4108'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4394'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4115'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-44-0270'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-20-9111'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4442'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4614'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4163'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4172'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-25-5325'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4801'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4182'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-62-4062'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-89-2214'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-28-6880'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4734'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4847'),
('V3','Demand surprise / consumption','Act 2','R14,R15,R16,D','10_demand_daily','SUM ship>1.5×SUM fcst Jan–Sep26','48-32-4155'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-56-9639'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-47-5711'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-90-0910'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-68-8112'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','M300N-L9-J'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-17-0025'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-22-2731'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-57-5166'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-22-0312'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-3880'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-4726'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','14-46-0507'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-16-2764'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-10-1307'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-3330'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-38-0222'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-42-2008'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-68-0124'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','52-76-6672'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','77-1002T'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-4769'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-66-4502'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-68-4592'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-1707'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-14-0525'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-22-1080'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-20-5005'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-10-1504'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-85-1101'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-1346'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-3138'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-3125'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-20-3986'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','10-97-1082'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-32-4678'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-32-4660'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','10-05-5077'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','52-76-0169'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-10-0411'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-73-2241'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-08-4814'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','2132-ST'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-42-0111'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','34-40-0045'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','48-73-1331C'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','2738-ST'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-22-1113R'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-56-9100E'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','49-93-9104'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-09-1515'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-4124'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','51-16-2451C'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-4831'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','10-20-6570'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','2572B-21'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-31-0682'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-50-0090'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','52-80-0147'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-38-0224'),
('V4','Supply / PO slip','Act 5','C.5.5,R27','purchase_orders','promised>original promised','58-46-1865'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','3651-21XCW'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','MR023339'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','06-82-8995'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-66-6227T'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','31-107T'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','40-50-8937'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','31-44-0408'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','PN0010630'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','14-32-0012'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','0852-20'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-89-2207'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','43-35-0925'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','634A00274'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-94-0013'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-56-9639'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','31-15-0066'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','2882-22'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','28-28-1700'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-73-2052'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','30-75-0150'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','77-0204'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','STLHDL-S'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','28-50-4139'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','50-59-1812W3'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','14-20-1204'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','2533-21'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','18-07-0176'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','58-15-0426-02'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','14-46-0709'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','MR104374'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','32-30-8001'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','14-46-0290'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-40-0720'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','58-95-0075-02'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-22-6105D'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-73-8922V'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-32-4788'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','58-12-0763'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','2677-04'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','28-06-0012'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-32-5033'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','05-81-5465'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','58-10-1310'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-20-9006Y'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','964M00012'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','42-06-0013'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-68-9842'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-41-0720'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-22-8901F'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','28-50-0027'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-11-2422'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-20-7411'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','2160-21J'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-22-8436'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','PN0003608'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-16-KITC'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','14-38-0095'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','3404-W3497'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','49-56-7010'),
('V4b','Who-moved-it (supplier-initiated)','Act 5','C.5.5','purchase_order_change_orders','change_order_originator_type=SUPPLIER','48-73-8512X'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-90-0910'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-47-5711'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-56-9639'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','415B-LD'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','44-10-0062'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','34-60-0051'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-00-5227'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-66-6713T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-1362'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-56-9649CA'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-20-6713T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','2672-20Z'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-2241'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-93-9104'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','RK58-28-0052U'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-56-9100E'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-16-B500'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-8902WM'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-89-2218T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','2585-ST'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','0910-20Y'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-57-5115'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-56-9605CA'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','2845-20'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-66-6512T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-62-4000'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-8439'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-1206C'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','F200U-21XL'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-25-2202'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-08-5265'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-00-5262PC'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','42-86-0010'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-94-0533'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','23-66-1100'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-9052'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-66-6515'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-00-5563'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','2557-20'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-1302'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','6232-21'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-8690'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-62-4005'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','M300B-212X'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-8392R'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-59-1881'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','43-24-9116T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','49-22-1110W'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-1351'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','45-88-1515'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','43-24-9304'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-1096'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','2954-20'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-22-9487T'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','0818-20'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-6966'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','605GN-LD'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','44-60-0850'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','48-73-2501'),
('V5','Holds / fulfillment blocks','Act 6','C.2.3','sales_fulfillment_hold_transactions','hold_apply_date_key>=Aug26','E105.48'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-32-4662CA'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-29-3874'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','18-01-2120'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','42-14-0017'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','05-74-0028'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-66-6144'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','02-04-0019'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','M200B-XLREC'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','45-88-1140'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-94-0501'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-50-0060'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-66-3280'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-05-0015'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-94-0647'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','23-81-0510'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','2633-20'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-25-2060'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-2604P'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-30-0123'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','43-44-4001'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-6826'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-6537'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','44-20-0200'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','MXF302-2HDZ'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','F251G-MD'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','31-44-0149'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','M552G-L'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','22-64-1422'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','42-66-0100'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-12-KITA'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-8924'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-9065'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','M200B-M9'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','38-50-6020'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-89-9224'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','31-12-0041'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','43-82-0205'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','45-96-9514'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-46-3413'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-73-7024M'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-20-0328'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','43-44-1200'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-46-9498'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','44-52-0605'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','44-66-0011'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','05-81-9045'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-22-8823'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','31-01-1910'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','M200R-XL9'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-30-2890'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','48-20-5428'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','28-14-1030'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','31-05-0140'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','34-40-8005'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','28-14-0085'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','44-60-0855'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','28-35-0110'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','14-20-2020'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','23-26-0031'),
('V6','Cross-org rebalance','Act 7','R5,C.4','transfer_orders','open transfer, src<>dest','49-90-2400'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-22-8929'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-27-1520'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-32-4171'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-32-4289'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-32-4579'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-32-4680'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-32-4815'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-36-1308'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-37-5025R'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-40-1026'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-44-0171'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-53-4832'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-53-4835'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-55-1026'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-62-4082'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-73-1434'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-73-1455'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-73-5136'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-73-7124E'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-73-8435C'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-80-6401'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-89-2326'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','48-95-6070'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-15-P750'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-1609'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-1663'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-2634C'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-2650'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-2875'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-5102'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-16-U01AC'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-56-0024'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-56-9825'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-57-0626'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-57-5371'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-66-0502'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-66-4516'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-66-5144'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-66-6404'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-66-6734'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-90-1979'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','51-57-8580'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','51-57-8701'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','51-57-8725'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','52-76-2782'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','52-76-4972'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-08-2055'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-08-5908'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-10-0338'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-42-9850'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-68-8112'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','603GN-MD'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','STLHDL-S'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','TI14SC'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','43-76-0900'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','49-90-0910'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-10-9170'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','58-10-9171'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','14-46-0709'),
('V7','Excess / overstock (E&O)','Scenario 1','DK-17,S1','20_supply_daily','PAB>3×SS','43-34-2735'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223100'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228901W'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228902W'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49940003'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228903W'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223104'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','50021025'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221505'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49940005'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48732010'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221725'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111850'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223170'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48112450'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223180'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','312867009'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221503'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48017026'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221825'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','LRHANDLE'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49940103'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223106'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','LRBDYSM'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223105'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48017787'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223209'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111865'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221950'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228902'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48551034'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','312867024'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221500'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48017788'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111852'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111881'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48112442'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111862'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48223115'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','369722'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49940503'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48324023'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228902E'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48111813'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221706'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49940107'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48894670'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221501'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48894631'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221025M'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48324537'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228901'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48221905'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','295320'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','MLSQ070'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','49221110'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','349722'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48732015'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','301720'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48325031'),
('V8','Forecast bias (governed)','Scenario 5 / DK-7','D,R15,C.6','fact_forecast_accuracy','governed fact_forecast_accuracy Jan–Aug26','48228903'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-32-4171'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-32-4579'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-32-4815'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-1410'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-1501'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6624'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','50-42-0120'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','50-44-0260'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','3401-20'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','43-34-2735'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','M701B-21L'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6157T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6204T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6262T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-47-5711'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','CPPLH2001'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','CPPL2201'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','BLO1436'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','2821-21J'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-7920V'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','2123-21HDJ'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6654'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6672'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-89-4870K'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-22-3260X'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-81-4780'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-81-7760'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-22-3079T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','43-40-8113'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','14-73-0515'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','23-66-5027'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','2533-21'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','28-25-0010'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','32-30-8001'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','415G-S'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','44-40-0035'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','45-06-0020'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','45-96-9315'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-13-5540'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-20-9046'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-89-2325CAN'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-22-9508'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-27-0007'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-41-0720'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6538'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','52-76-0093'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','52-80-0606'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','603BL-3X'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-40-1048'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-90-2023Y'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','PN0005818'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-7153EM'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6511T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-7942V'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-73-8912V'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-56-9210T'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-16-2820V'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','49-66-6674'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','351E-2X'),
('V9','Forward risk (coming-risk)','Gap 1','G1,DK-9','20_supply_daily','healthy now, crosses SS later','48-81-5080'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-27-0180'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-32-4815'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-40-0720'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-73-1321'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-73-1410'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','49-16-W247'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','49-57-5166'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','49-66-6624'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','49-90-1979'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','604BL-XL'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','606B-XL'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','77-0204'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','3401-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','31-44-0408'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','M701B-21L'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','42-70-8100'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','CPPLH2001'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','F452G-XLD'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2772A-21J'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2161-21J'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-22-7718V'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-1047T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-9086T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2779-750CUZ'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-2122T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-2124T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-4000T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-9052T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-9053T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','45-34-9101T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2941-21Z'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','5268-21J'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2123-21HDJ'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','49-66-6654'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2971-20M'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-89-4870K'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','28-28-1200'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-22-3260X'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','51-16-2651ZX'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-81-4780'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-81-7760'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','48-22-3079T'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','43-40-8113'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','0820-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','0852-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','0960-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','14-20-9225'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','14-32-0012'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','14-46-0290'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','14-73-0515'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','18-07-0176'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','22-130'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','22-68-0019'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','23-66-5027'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2446-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2476-20'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','2533-21'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','28-20-0023'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','28-28-1700'),
('V10','Chronic (repeat offender)','V10 / Gap 5','G5,temporal','20_supply_daily','≥6 forward weeks below SS','28-35-0085'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9508'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9408'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9529'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9125'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8949B'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9038'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9314'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9504'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9429'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9004'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9013'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9315'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8922'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9519'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9051'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9031'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9019'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8927'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9130'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9311'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9012'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9020'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9032'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9016'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9044'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9481'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9150'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9214'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9482'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9030'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9212'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9023'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9411'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9484'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9000'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9037'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9080'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8904'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9018'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9215'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9513'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9029'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9320'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9036'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8928'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9485'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9511'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8902H'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9214T'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9407'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9088'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8904X'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9151'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9034'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9486'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9215T'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8910'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-8920'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9017'),
('V11','Convergence (multi-cause)','DK-13','DK-13','20_supply_daily+purchase_orders','below SS ∩ PO slip','48-22-9404'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-25-1252'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-27-0180'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-32-4171'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-32-4579'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-32-4680'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-32-4815'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-40-0720'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-73-1410'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-89-2207'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-16-W247'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6122'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6624'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','50-42-0120'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','50-44-0260'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','604BL-XL'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','77-0204'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','43-34-2735'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','M701B-21L'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6157T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6204T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6262T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','CPPLH2001'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','CPPL2201'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-89-2217T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','2821-21J'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','PN0006103'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','PN0006130'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','PN0006141'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-1047T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-9086T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-94-0613'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','2779-750CUZ'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-2122T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-2124T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-4000T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-9052T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-9053T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','45-34-9101T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-73-7920V'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','2123-21HDJ'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6654'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','49-66-6672'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-89-4870K'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-22-3260X'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','48-22-3079T'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','02-40-0518'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','43-40-8113'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','06-82-8995'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','0852-20'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','0960-20'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','14-02-0115'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','14-02-0140'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','14-46-0290'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','14-46-6050'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','14-73-0515'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','18-07-0176'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','22-130'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','2476-20'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','2533-21'),
('V12','Do-nothing / false-alarm','DK-14','DK-14','20_supply_daily','below SS but min PAB>=0 (cushion dip)','28-25-0010'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-22-8903P'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-25-5120'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-32-4196'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-32-4396'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-32-4408'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-39-0506'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-73-1107'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-73-7151H'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-89-2313'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-12-U600C'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-16-2689'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-16-2738'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-36-2789'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-59-2089'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-59-4138'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-66-6119'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','50-39-1500'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','52-80-0151'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','52-80-2825B'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','6370-21'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','70-01-1161'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','3033-20'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-73-8511'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','312B-LY'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','605B-MDY'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','M551R-XLD'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-59-1881SC'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','45-34-1123'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-20-8899Y'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','M100R-3X-W'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-10-9001N'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-90-6024T'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-22-2464T'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-11-2450C'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','45-34-9083T'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-20-0390'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-46-0369'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-73-2516'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-73-5021BY'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-46-3029'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','M100B-212X-J'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','49-56-9607CA'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-39-0511B'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-39-0521BA'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','PN0016235'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-46-2042'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-46-0930'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-81-6780'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','48-81-7040'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','06-82-7784'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-29-0135'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','14-48-0085'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','18-50-0120'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','23-45-2674'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','23-66-0011'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','2520-ST'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','2666-20'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','2758-20'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','28-50-0113'),
('V13','Recoverability (committed loss)','DK-15','DK-15','20_supply_daily+dim_series_ext_vw','complete_lead_time>days-to-first-stockout','2912-ST'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-25-1252'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-32-4171'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-32-4579'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-32-4815'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-40-0720'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-73-1410'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6122'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6624'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-90-1979'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','606B-XL'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','77-0204'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','M650K-3632'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6157T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6204T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6262T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','F452G-XLD'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-89-2217T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2772A-21J'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2821-21J'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2161-21J'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-22-7718V'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-1047T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-9086T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-94-0613'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2779-750CUZ'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-2122T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-2124T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-4000T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-9052T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-9053T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-9101T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-73-7920V'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2941-21Z'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2123-21HDJ'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6654'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6672'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','2971-20M'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-89-4870K'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-90-1976'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-22-3260X'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-81-4780'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-81-7760'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-22-3079T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-00-5561'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-20-8882'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-32-4788'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-32-5033'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-73-5072'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-89-2338'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-16-KITC'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-16-U001C'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6376'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6538'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6642'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','504B-LXL'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','603B-S'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','MLBX24'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','45-34-1077'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','49-66-6212T'),
('V15','Lifecycle transition/NPD','N1 / DK','N1,lifecycle','items_scd1','transition_sku_flag/is_npd_item boolean true + below SS','48-20-9006Y'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','603G-S'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','606B-XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M300N-21S'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M701B-21L'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F452G-XLD'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M200N-203X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3632-21PO'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F550N-XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-16-3055'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M600B-21L'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2118-20'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','504B-LXL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','606BL-XLD'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M102G-21XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M300N-21XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M850G-4032'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M250B-M'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M101C-3X-W'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2736-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','351E-2X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3450-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','P326-2967'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F102B-21XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M102G-212X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M102G-213X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3841-20'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M100G-20M'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M101C-M-W'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M200G-212X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M200U-202X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-90-2035Y'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M552G-XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3060-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-90-1955'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M300G-21S'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M753BD'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2835-21HD'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','U2000RB-1'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M200B-202X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','604E-3X'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F102B-LREC'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M754E-SM'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2940-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2667-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F300B-20L'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F300B-20XL'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2525-ST'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M700B-21S'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3693-ST'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M100G-S-W'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M102G-L-W'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F552G-XS'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','F251B-MD'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-90-2929'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3044-20'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','2865-STR'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-90-1992'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','49-90-2325'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','3006-ST'),
('V16','Over-forecast excess driver','N2','N2','10_demand_daily','SUM fcst>1.5×SUM actual','M651B-3430'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2446-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','0721-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6536-21'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2982-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2657-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2845-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2967-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2602-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2519-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2105'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2787-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2127-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2780-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','49-16-2721'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2954-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2559-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2828-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','48-11-2131'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3974-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','48-11-2460'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','5374-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3107-6'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2775B-211'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3674-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2505-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','MXF220-2HD'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2726-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2887-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2906-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6177-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2114-21'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2820-20PS'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2560-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3601-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2762-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2563-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3020-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2115-21'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2764-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','MXF302-2HD'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2881-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2011R'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6161-33'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','48-11-2425'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2930-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','49-24-2310'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6146-33'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2836-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6470-21'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2758-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2113-21'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6143-31'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2903-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6086-30'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','3049-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6124-31'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2488-20'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6161-31'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','6141-59'),
('V17','Returns / warranty','N3','N3','fact.warranty_transaction','warranty transactions since Jan 2026, item-keyed via conformed fact','2974-20'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-20-8036'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2865-20'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','53-01-5293'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-73-1079'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-8436'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','31-052'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','14-34-0960'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-4206'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','14-30-3405'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-89-2747'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','45-66-0018'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-9340'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-96-0600'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','58-31-0628'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-16-2669'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','PN0002695'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2267-20H'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','22-16-0430'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','10-05-6601'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-32-4118'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','MR103749'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','14-29-0023'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2205-20'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-66-6272T'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','34-40-1561'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-73-2012V'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-66-6348'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','52-80-2829'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-57-8643'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-9504'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-1960'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-32-5162CA'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','06-82-0041'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','45-88-7001'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','58-09-4324'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-22-9314'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-73-2015V'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-73-7151HM'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','MR104024'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','58-68-1169'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2657-99'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-57-8323'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','45-34-9063T'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-66-6245T'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','16-01-2503'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-66-4703'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','14-50-2430'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','44-90-0108'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','45-34-1062'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-57-5141'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-89-2727T'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2354-STR'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2432-22YY'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','53-01-6162'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-32-4706'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-57-5536'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','2843-20'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','49-66-6211'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','MR104546'),
('V18','Found-inventory / phantom heal','N4','N4,S10','inventory_material_transaction','positive adjustment txn since Jun26','48-36-1109'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-25-1252'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-27-0180'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-27-1520'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4289'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4579'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4680'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4763'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4815'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-36-1308'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-39-0601'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-39-0616'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-40-0720'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-40-1026'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-62-4082'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-80-6401'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-89-2207'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-25-4125'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-27-0007'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4191'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4715'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4788'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4846'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4914'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-5033'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-36-1108'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-41-0720'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-52-1300'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-62-4187'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-20-9101'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-20-9116'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-27-0190'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-28-4006'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4020'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4090'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4142'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4485'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4502'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4682'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4760'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4810'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-5003'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-9930'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-40-0626'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-80-5180'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-89-2217'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-20-9097'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-25-4621'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-25-5143'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-25-5225'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-27-0005'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4515'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4571'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4573'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4578'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4660'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4678'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-4771'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-32-5700'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-39-0561'),
('V19','Non-standard demand channels','N5','N5','10_demand_daily+dg5_customer_scd1','shipments via non-standard mkedg5 channels','48-39-0635'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','49-16-2650'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','22-06-0605'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-30-0161'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-13-1503'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-73-1321'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','45-88-0128'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-22-8428'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-73-2052'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-46-9960'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','28-50-4139'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','06-82-8995'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','2533-21'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','2882-22'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','32-30-8001'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','42-42-0051'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','44-90-0014'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','45-76-0027'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-00-5232'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-22-8339'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-32-4815'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-44-0171'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','49-22-2731'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','42-25-2595'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','43-34-2735'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-22-3079T'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','06-82-0027'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-48-0095'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','22-32-0420'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-20-5235'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-73-1221'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-22-8393R'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-32-4680'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','MT205'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','3401-20'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','2160-0'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','0852-20'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','22-130'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','43-56-2550'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-73-1410'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-73-8435C'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','06-10-0025'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-30-2008'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-34-0034'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','14-46-0259'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','28-28-1700'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','28-35-0127'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','31-12-0098'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','31-53-0011'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-00-5561'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','2579-20Y'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','06-65-0096'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','23-66-2840'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','2865-20'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','42-25-0002'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','44-40-0035'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','44-76-0050'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-20-9046'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-13-5540'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','48-32-4579'),
('V20','Component / multi-org items','N6','N6','20_supply_daily','supply footprint on >=5 orgs','507BL-SM'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-90-2023Y'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-5001E'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-22-1110'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-2923'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','2791'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-89-9244'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-73-8523HX'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','1140'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-20-3916'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','2909-20'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','650.24V'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-5603'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','500M.24'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-08-1095'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-73-8521HX'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','44-10-5264'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','2807-20J'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-56-5140'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-20-7311'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','2788-22HDZ'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','31-44-2854'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','MT555X'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-3510D'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-32-4408'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','650.72V'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-90-2014J'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-4540'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-1525V'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','296'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','0880-20'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','105'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','77-063T'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','44-06-0201'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','MT216X'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','27030'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-73-8522HX'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','50-02-1015'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','14-20-6550'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','18-07-5316'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','EM70.10'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','2828-21E'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-2917'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','4274-21Z'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','14-29-0115'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-1502'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-3910'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-1521V'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-3209'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','MLIBM48'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','352R-S'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','FG58-28-3237'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-90-1900'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-6100V'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-1500'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','100'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-6240'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','FG58-28-2923'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','49-90-2026'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-1905'),
('V21','Recovery velocity (slow release)','N7','N7','sales_fulfillment_hold_transactions','hold_lag_hours>168h','48-22-6910'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','50-44-0260'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BLO1436'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2651ZX'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0005818'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-11-1822'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','6PCTSPH120B'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','14-46-0533T'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BCO2238'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BCO2223'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','3974WM'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2659X5'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-33-1000'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','14-46-0531T'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0005654'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BCO2296'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','8PCTSPH'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','3973WM'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-15-0542'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-33-0987'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0005819'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','3975WM'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','2580WM'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BCO2351'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2455C'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-09-1057'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','45-52-1091C'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','52-76-2446'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2456M'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-10-2003'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','50-56-9103'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0005661'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BCO2222'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2455M'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2652ZX'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-33-0480'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-68-1767'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2659X4'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','BLO2019'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','DIVIDER12'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0005830'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','9PCTSPH'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-39-2900'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2658R'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2670'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2452M'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2655BX'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2659X6'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','PN0014724'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','50-32-5156CA'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-22-2462'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2656X'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2657X'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2654'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','6PCTSPH60B'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-10-0263'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','58-10-1014'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2656RX'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2650X'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51162651RX'),
('V22','Criticality A-class ABC','DK-16','DK-16','dim_series_ext_vw','inventory_abc_class=A + below SS','51-16-2456Z'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4020'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4029'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4073'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-1915'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4168'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-52-1600'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4280'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-3025'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4019'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4116'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-3020'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-5220'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-5421'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4282'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5721'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-89-1561'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-3065'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5158'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-3090'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-36-1061'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5722'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-2065'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5022'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4204'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4196'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4490'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4222'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5720'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-0200'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-6024'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5023'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4108'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4489'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-5101'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-5200'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4150'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4028'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-30-1520'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5032'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-42-5640'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-5021'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-52-1700'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4281'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4203'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-52-1400'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4026'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4731'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-52-1650'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4015'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4005'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-32-4263'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-41-0713'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-89-0026'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4105'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-3065'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-40-4140'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-62-6048'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-25-1371'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','48-89-2521'),
('V23','Dormant / obsolescence (E&O)','DK-17','DK-17','10_demand_daily','0 ship Mar–Sep26, >0 before','49-10-9122'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-62-2057'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-32-4490C'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-62-4074'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','49-22-1110V'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-20-4075'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','49-10-9208Q'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-22-2434'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-73-5332C'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','58-28-7098'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','MLIB48'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-3187'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-7776'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-1428'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-73-1501'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','MLBX78'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-7812'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-2897'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-0664'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-73-7124E'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','FG58-28-3291'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','48-20-8823'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','05-55-3120'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','05-81-0076'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','05-86-0016'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-54-0120'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-65-0096'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-65-1280'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-75-5825'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-82-0091'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-82-1085'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-97-0455'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','12-20-2447'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','12-20-5379'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-04-0005'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-09-0100'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-12-0115'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-29-0101'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-30-2409'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-34-6255'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-38-0061'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-46-1017'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-46-8605'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-04-2120'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-60-0041'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-60-5379'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-60-5420'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-66-0141'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-68-0015'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','45-08-0013'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','05-74-0625'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','05-81-0530'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-65-0006'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-75-0006'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','06-81-0028'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','12-99-1300'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-34-0270'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-46-0401'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-20-0026'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','44-60-0142'),
('V24','Intermittent demand','DK-18','DK-18','10_demand_daily','active<30% of >=12 months','14-02-0115'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-6262T'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4680'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-27-0180'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','50-44-0260'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4579'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-25-1252'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4171'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','M650K-3632'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-94-0613'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','3401-20'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4815'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','603B-S'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-6212T'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','58-22-6108'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','52-76-0093'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-4703FL'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','507B-LXLQ'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','2438-22XYY'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-81-5080'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-5072'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-11-2450C'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','603BL-3X'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-22-8901F'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4832ZZ'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-5033'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-94-0107'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4788'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-2014TW'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','45-88-0015'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','52-80-0606'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-81-7060'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','51-11-1822'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-2101'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-20-9057Y'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-22-9008'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','45-96-0024'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-2502'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-1108'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-5003'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-22-8371R'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','3494-22'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4810'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-6370T'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','415R-LP'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-5165'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-32-4502'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-5161'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','605G-MDQ'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','M650G-3230D'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-27-0190'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','14-46-0533T'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-6607T'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-73-5123'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-16-1212'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-22-0160'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','49-66-4502'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','603E-2X'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','51-36-7100'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','58-08-3120'),
('V25','Parameter / SS review','DK-19','DK-19','dim_series_ext_vw','safety_stock_managed_flag=Yes + below SS','48-81-7740'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-22-8929'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-25-1252'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-27-0180'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-27-1520'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4171'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4289'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4437J'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4579'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4680'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4763'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4815'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-36-1308'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-39-0601'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-39-0616'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-40-0720'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-44-0171'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-1026'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-1212'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-62-4082'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-25-4125'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4191'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4413J'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4461J'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4788'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4846'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4914'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-5033'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-41-0720'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-44-0151'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-0123'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-62-4187'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-66-1270'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-66-3160'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-73-1097'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-22-9008'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-22-9408'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-27-0190'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-28-4006'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4020'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4090'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4485'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4502'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4682'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4685J'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4760'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4810'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-5003'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-40-0620P'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-40-0626'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-53-2410'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-53-2833'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-2730'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-2765'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-55-3566'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-59-0090'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-73-1108'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-73-1131'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-22-9225'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-25-4621'),
('V26','Intentional-hold (managed SS)','DK-20','DK-20','dim_series_ext_vw','safety_stock_managed_flag=Yes','48-32-4073')
)
SELECT
  s.scenario_code, s.scenario_title, s.activity, s.requirement_map,
  s.source_table, s.predicate_note, s.item_id,
  true                                   AS in_seed_catalog,
  (sp.item_id IS NOT NULL)               AS joins_to_spine,
  current_timestamp()                    AS extracted_ts
FROM seed s
LEFT JOIN (SELECT DISTINCT item_id FROM sandbox_operations.po_management.rc_serving_sku_week) sp
  ON s.item_id = sp.item_id;
""")
print("03_rc_scenario_membership: done")

# COMMAND ----------
# MAGIC %md ### 04_rc_forward_risk
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 04 · rc_forward_risk (ADR §7.2)
-- First future SS-crossing per SKU×org — reads the spine (define-once).
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_forward_risk AS
SELECT
  item_id, inventory_organization_bigint_key, designated_organization_bigint_key,
  MAX(criticality_class)      AS criticality_class,
  MAX(likely_cause)           AS likely_cause,
  MAX(recoverability_class)   AS recoverability_class,
  MAX(committed_value)        AS committed_value,
  MIN(CASE WHEN projected_available_balance < safety_stock THEN date_key END) AS crosses_week,
  MIN(projected_available_balance) AS depth_at_low_point,
  DATEDIFF(
    to_date(CAST(MIN(CASE WHEN projected_available_balance < safety_stock THEN date_key END) AS STRING),'yyyyMMdd'),
    to_date(CAST(MIN(process_date) AS STRING),'yyyyMMdd'))                     AS days_to_crossing,
  MAX(recoverability_class = 'UNRECOVERABLE') AS within_lead_time,
  MIN(process_date)           AS snapshot_date
FROM sandbox_operations.po_management.rc_serving_sku_week
GROUP BY item_id, inventory_organization_bigint_key, designated_organization_bigint_key
HAVING MIN(CASE WHEN projected_available_balance < safety_stock THEN date_key END) IS NOT NULL;
""")
print("04_rc_forward_risk: done")

# COMMAND ----------
# MAGIC %md ### 05_rc_pattern_rollup
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 05 · rc_pattern_rollup (ADR §7.4)
-- Driver contribution ranked by $-at-risk, by supplier(normalized, hazard #14) / org / criticality.
-- Reads the spine + dim_series_ext_vw for the supplier attribute.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_pattern_rollup AS
WITH flagged AS (
  SELECT r.item_id, r.inventory_organization_bigint_key, r.designated_organization_bigint_key,
         r.series_bigint_key, r.criticality_class, r.likely_cause,
         MAX(r.committed_value) AS committed_value
  FROM sandbox_operations.po_management.rc_serving_sku_week r
  WHERE r.severity_class <> 'healthy'
  GROUP BY r.item_id, r.inventory_organization_bigint_key, r.designated_organization_bigint_key,
           r.series_bigint_key, r.criticality_class, r.likely_cause
),
sup AS (
  SELECT series_bigint_key,
         -- normalize supplier name (hazard #14): trim, upper, collapse TTI variants
         upper(trim(regexp_replace(origin_supplier_name, '(LIMITED|LTD|LMTD)', 'LTD'))) AS supplier_norm,
         origin_supplier_number
  FROM prod_operations.edw_extension.dim_series_ext_vw
)
SELECT
  'supplier'                              AS dimension,
  COALESCE(sup.supplier_norm,'(unknown)') AS group_key,
  f.likely_cause,
  COUNT(DISTINCT f.item_id)               AS sku_count,
  ROUND(SUM(f.committed_value),0)         AS dollars_at_risk
FROM flagged f
LEFT JOIN sup ON f.series_bigint_key = sup.series_bigint_key
GROUP BY 1,2,3
UNION ALL
SELECT 'org', CAST(f.inventory_organization_bigint_key AS STRING), f.likely_cause,
       COUNT(DISTINCT f.item_id), ROUND(SUM(f.committed_value),0)
FROM flagged f GROUP BY 1,2,3
UNION ALL
SELECT 'criticality', f.criticality_class, f.likely_cause,
       COUNT(DISTINCT f.item_id), ROUND(SUM(f.committed_value),0)
FROM flagged f GROUP BY 1,2,3;
""")
print("05_rc_pattern_rollup: done")

# COMMAND ----------
# MAGIC %md ### 06_rc_snapshot_history
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 06 · rc_snapshot_history (ADR §7.3)
-- Chronic recurrence + gap decomposition (consumption move vs SS-target move) across snapshot vintages.
-- Hazard #3: pin vintages explicitly. Gap-decomp compares the SAME target week across two process_dates.
-- Bounded to the flagged book (severity<>healthy on the current spine) to keep the multi-snapshot scan cheap.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_snapshot_history AS
WITH scope AS (   -- only items currently flagged (from the spine) — keeps the scan bounded
  SELECT DISTINCT item_id, product_bigint_key, inventory_organization_bigint_key
  FROM sandbox_operations.po_management.rc_serving_sku_week
  WHERE severity_class <> 'healthy'
),
cur AS (   -- latest vintage 20260903, per SKU×org×target-week
  SELECT s.product_bigint_key, s.inventory_organization_bigint_key, s.date_key,
         s.projected_available_balance AS pab_cur, s.safety_stock AS ss_cur, s.total_demand AS dmd_cur
  FROM prod_edw.fact.`20_supply_daily` s
  JOIN scope sc ON s.product_bigint_key = sc.product_bigint_key
              AND s.inventory_organization_bigint_key = sc.inventory_organization_bigint_key
  WHERE s.process_date = 20260903 AND s.plan_name = '20 Global Supply Plan'
    AND s.date_key BETWEEN 20260903 AND 20261130
),
prior AS (   -- prior vintage 20260804, same grain
  SELECT s.product_bigint_key, s.inventory_organization_bigint_key, s.date_key,
         s.projected_available_balance AS pab_pri, s.safety_stock AS ss_pri, s.total_demand AS dmd_pri
  FROM prod_edw.fact.`20_supply_daily` s
  JOIN scope sc ON s.product_bigint_key = sc.product_bigint_key
              AND s.inventory_organization_bigint_key = sc.inventory_organization_bigint_key
  WHERE s.process_date = 20260804 AND s.plan_name = '20 Global Supply Plan'
    AND s.date_key BETWEEN 20260903 AND 20261130
),
chronic AS (   -- weeks-below-SS in the current window (chronicity proxy without daily-snapshot fan-out)
  SELECT product_bigint_key, inventory_organization_bigint_key,
         SUM(CASE WHEN pab_cur < ss_cur THEN 1 ELSE 0 END) AS weeks_below_ss_window,
         COUNT(*) AS weeks_in_window
  FROM cur GROUP BY 1,2
)
SELECT
  sc.item_id,
  c.product_bigint_key, c.inventory_organization_bigint_key, c.date_key AS target_week,
  c.pab_cur, p.pab_pri,
  c.ss_cur, p.ss_pri,
  c.dmd_cur, p.dmd_pri,
  -- gap decomposition (measures §; ADR §7.3): split the week-over-vintage gap move into demand vs target
  (c.dmd_cur - p.dmd_pri)                       AS delta_from_consumption,   -- demand moved
  (c.ss_cur  - p.ss_pri)                        AS delta_from_target_refresh, -- SS target moved
  ((c.pab_cur - c.ss_cur) - (p.pab_pri - p.ss_pri)) AS delta_ss_gap,
  ch.weeks_below_ss_window,
  ch.weeks_in_window,
  (ch.weeks_below_ss_window >= 6)               AS is_chronic,
  20260903 AS cur_vintage, 20260804 AS prior_vintage
FROM cur c
JOIN scope sc ON c.product_bigint_key = sc.product_bigint_key
             AND c.inventory_organization_bigint_key = sc.inventory_organization_bigint_key
LEFT JOIN prior p ON c.product_bigint_key = p.product_bigint_key
                 AND c.inventory_organization_bigint_key = p.inventory_organization_bigint_key
                 AND c.date_key = p.date_key
JOIN chronic ch ON c.product_bigint_key = ch.product_bigint_key
               AND c.inventory_organization_bigint_key = ch.inventory_organization_bigint_key;
""")
print("06_rc_snapshot_history: done")

# COMMAND ----------
# MAGIC %md ### 07_rc_cause_week_heat
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 07 · rc_cause_week_heat (ADR §7.4a / DK-22)
-- Level-stacked cause × week, signed $-weighted variance, for the recursive heatmap drill.
-- Signed: shortfall (short) is +$ pressure; excess is -$. $ = committed_value. One fixed vintage.
-- child_row_count drives the stop-rule (recurse only while >= ~4 banding child rows).
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_cause_week_heat AS
WITH r AS (
  SELECT likely_cause, designated_organization_bigint_key, inventory_organization_bigint_key,
         criticality_class, date_key, item_id,
         ss_gap, shortfall_units, committed_value, severity_class
  FROM sandbox_operations.po_management.rc_serving_sku_week
  WHERE severity_class <> 'healthy'
),
-- LEVEL 1: cause × week (portfolio)
lvl_cause AS (
  SELECT 'cause' AS level, likely_cause AS row_key, likely_cause AS row_label,
         'ALL' AS parent_filter, date_key AS week,
         ROUND(SUM(CASE WHEN ss_gap < 0 THEN committed_value ELSE -committed_value END),0) AS cell_value_signed,
         COUNT(DISTINCT item_id) AS at_risk_skus
  FROM r GROUP BY likely_cause, date_key
),
-- LEVEL 2: org × week within cause (pool/org drill)
lvl_org AS (
  SELECT 'org' AS level, CAST(inventory_organization_bigint_key AS STRING) AS row_key,
         CAST(inventory_organization_bigint_key AS STRING) AS row_label,
         likely_cause AS parent_filter, date_key AS week,
         ROUND(SUM(CASE WHEN ss_gap < 0 THEN committed_value ELSE -committed_value END),0) AS cell_value_signed,
         COUNT(DISTINCT item_id) AS at_risk_skus
  FROM r GROUP BY inventory_organization_bigint_key, likely_cause, date_key
),
-- LEVEL 3: criticality × week within org (leaf-ward)
lvl_crit AS (
  SELECT 'criticality' AS level, criticality_class AS row_key, criticality_class AS row_label,
         CAST(inventory_organization_bigint_key AS STRING) AS parent_filter, date_key AS week,
         ROUND(SUM(CASE WHEN ss_gap < 0 THEN committed_value ELSE -committed_value END),0) AS cell_value_signed,
         COUNT(DISTINCT item_id) AS at_risk_skus
  FROM r GROUP BY criticality_class, inventory_organization_bigint_key, date_key
),
u AS (SELECT * FROM lvl_cause UNION ALL SELECT * FROM lvl_org UNION ALL SELECT * FROM lvl_crit)
SELECT u.*,
       COUNT(*) OVER (PARTITION BY level, parent_filter, week) AS child_row_count,   -- stop-rule input
       20260903 AS process_date
FROM u;
""")
print("07_rc_cause_week_heat: done")

# COMMAND ----------
# MAGIC %md ### 08_rc_value_baseline_daily
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 08 · rc_value_baseline_daily (ADR §7.7 / DK-21)
-- Frozen daily at-risk exposure — the Value-Ledger 08:00 anchor. Commitment-$ weighted.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_value_baseline_daily AS
SELECT
  concat('base_', CAST(MIN(process_date) AS STRING))       AS baseline_snapshot_id,
  MIN(process_date)                                        AS as_of_date,
  -- at-risk $: sum committed_value over ACT-worthy flags (per SKU×org, dedup to worst week)
  ROUND(SUM(peak_committed),0)                             AS at_risk_dollars,
  COUNT(*)                                                 AS at_risk_sku_count,
  ROUND(SUM(CASE WHEN recoverability_class='UNRECOVERABLE' THEN peak_committed ELSE 0 END),0) AS unrecoverable_dollars,
  MIN(process_date)                                        AS process_date,
  current_timestamp()                                      AS build_ts
FROM (
  SELECT item_id, inventory_organization_bigint_key,
         MAX(committed_value)      AS peak_committed,
         MAX(recoverability_class) AS recoverability_class,
         MIN(process_date)         AS process_date
  FROM sandbox_operations.po_management.rc_serving_sku_week
  WHERE action_verdict = 'ACT'
  GROUP BY item_id, inventory_organization_bigint_key
) act;
""")
print("08_rc_value_baseline_daily: done")

# COMMAND ----------
# MAGIC %md ### 09_rc_qa_reconciliation
# COMMAND ----------
spark.sql("""
-- Wave-0+ serving layer · 09 · rc_qa_reconciliation (ADR §10 risk row)
-- Reconciles the spine against a direct prod_edw re-query at the SAME pinned snapshot.
-- Grain of truth: distinct item×org on 20 Global at 20260903 forward window. Drift should be ~0.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_qa_reconciliation AS
WITH source_truth AS (
  SELECT
    COUNT(DISTINCT s.product_bigint_key || '-' || s.inventory_organization_bigint_key) AS src_sku_org,
    COUNT(DISTINCT s.product_bigint_key)                                                AS src_skus
  FROM prod_edw.fact.`20_supply_daily` s
  JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key = i.item_bigint_key
  WHERE s.process_date = 20260903 AND s.plan_name = '20 Global Supply Plan'
    AND s.date_key BETWEEN 20260903 AND 20261130 AND i.item IS NOT NULL
),
serving AS (
  SELECT
    COUNT(DISTINCT item_id || '-' || inventory_organization_bigint_key) AS srv_sku_org,
    COUNT(DISTINCT item_id)                                             AS srv_skus,
    COUNT(DISTINCT CASE WHEN severity_class<>'healthy' THEN item_id||'-'||inventory_organization_bigint_key END) AS srv_flagged,
    COUNT(DISTINCT CASE WHEN action_verdict='ACT' THEN item_id||'-'||inventory_organization_bigint_key END)      AS srv_act
  FROM sandbox_operations.po_management.rc_serving_sku_week
)
SELECT 'sku_org_grain'  AS check_name, t.src_sku_org AS source_value, s.srv_sku_org AS serving_value,
       (t.src_sku_org - s.srv_sku_org) AS drift FROM source_truth t CROSS JOIN serving s
UNION ALL
SELECT 'distinct_skus', t.src_skus, s.srv_skus, (t.src_skus - s.srv_skus) FROM source_truth t CROSS JOIN serving s
UNION ALL
SELECT 'flagged_sku_org', NULL, s.srv_flagged, NULL FROM serving s
UNION ALL
SELECT 'act_sku_org', NULL, s.srv_act, NULL FROM serving s;
""")
print("09_rc_qa_reconciliation: done")

# COMMAND ----------
# MAGIC %md ### 10_rc_excess
# COMMAND ----------
spark.sql("""
-- Wave-1 · 10 · rc_excess — every SKU whose PROJECTED position sits well above target (E&O candidate).
-- on_hand is ~sparse on the plan fact; excess is correctly defined on the projected available balance
-- staying above the safety-stock target across the forward window. $ = surplus units × std_cost.
-- Full 20 Global book. WRITE: sandbox_operations.po_management. READ-ONLY sources.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_excess AS
WITH per_sku AS (
  SELECT
    item_id,
    MIN(projected_available_balance)               AS min_pab,
    MAX(safety_stock)                              AS safety_stock,
    MAX(std_cost)                                  AS std_cost,
    MAX(criticality_class)                         AS criticality_class,
    AVG(NULLIF(total_demand, 0))                   AS avg_wk_demand
  FROM sandbox_operations.po_management.rc_serving_sku_week
  GROUP BY item_id
)
SELECT
  item_id,
  min_pab,
  safety_stock,
  criticality_class,
  GREATEST(0, min_pab - safety_stock)                                          AS surplus_units,
  ROUND(GREATEST(0, min_pab - safety_stock) * COALESCE(std_cost, 0), 0)         AS dollars,
  CASE WHEN avg_wk_demand > 0 THEN ROUND(min_pab / avg_wk_demand, 0) ELSE NULL END AS weeks_cover,
  CASE WHEN avg_wk_demand IS NULL OR avg_wk_demand = 0 THEN 'no-forward-demand'
       WHEN min_pab / NULLIF(avg_wk_demand,0) > 52 THEN 'high-cover'
       ELSE 'over-3x-SS' END                                                   AS driver
FROM per_sku
WHERE safety_stock > 0 AND min_pab > 3 * safety_stock
ORDER BY dollars DESC;
""")
print("10_rc_excess: done")

# COMMAND ----------
# MAGIC %md ### 11_rc_rebalance
# COMMAND ----------
spark.sql("""
-- Wave-1 · 11 · rc_rebalance — SKUs short in one org with in-network excess in another (transfer-before-buy).
-- Spine self-join within the designated pool. Uses worst forward position per SKU×org.
-- Full book. WRITE: sandbox_operations.po_management. READ-ONLY sources.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_rebalance AS
WITH sku_org AS (
  SELECT
    item_id,
    designated_organization_bigint_key AS pool,
    inventory_organization_bigint_key  AS org,
    MIN(projected_available_balance)    AS low_pab,
    MAX(safety_stock)                   AS ss
  FROM sandbox_operations.po_management.rc_serving_sku_week
  GROUP BY item_id, designated_organization_bigint_key, inventory_organization_bigint_key
),
pos AS (  -- net position vs SS per org
  SELECT item_id, pool, org, (low_pab - ss) AS net FROM sku_org
),
shorts AS (SELECT item_id, pool, org AS short_org, net AS short_net FROM pos WHERE net < 0),
excess AS (SELECT item_id, pool, org AS excess_org, net AS excess_net FROM pos WHERE net > 0)
SELECT
  s.item_id,
  s.short_org,
  ROUND(s.short_net, 0)                                   AS short_units,
  e.excess_org,
  ROUND(e.excess_net, 0)                                  AS excess_units,
  ROUND(LEAST(ABS(s.short_net), e.excess_net), 0)         AS coverable,
  ROUND(100.0 * LEAST(ABS(s.short_net), e.excess_net) / NULLIF(ABS(s.short_net), 0), 0) AS pct_covered
FROM shorts s
JOIN excess e ON s.item_id = e.item_id AND s.pool = e.pool AND s.short_org <> e.excess_org
QUALIFY ROW_NUMBER() OVER (PARTITION BY s.item_id, s.short_org ORDER BY e.excess_net DESC) = 1
ORDER BY coverable DESC;
""")
print("11_rc_rebalance: done")

# COMMAND ----------
# MAGIC %md ### 12_rc_bias
# COMMAND ----------
spark.sql("""
-- Wave-1 · 12 · rc_bias — governed forecast bias / FVA by DG5 channel.
-- Source: prod_operations.demand.fact_forecast_accuracy (governed, DK-7). Past window with real actuals.
-- planner_bias vs system_bias: where |planner| > |system|, the human override ADDS error (flag it).
-- WRITE: sandbox_operations.po_management. READ-ONLY source.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_bias AS
WITH agg AS (
  SELECT
    g.mkedg5                                        AS dg5,
    SUM(fa.planner_bias)                            AS planner_bias,
    SUM(fa.system_bias)                             AS system_bias,
    SUM(fa.positive_error + fa.negative_error)      AS abs_error,
    SUM(fa.positive_error_cost + fa.negative_error_cost) AS error_cost
  FROM prod_operations.demand.fact_forecast_accuracy fa
  JOIN prod_edw.dimension.dg5_customer_scd1 g ON fa.dg5_customer_bigint_key = g.dg5_customer_bigint_key
  WHERE fa.date_key BETWEEN 20260101 AND 20260831
  GROUP BY g.mkedg5
)
SELECT
  dg5,
  ROUND(planner_bias, 0)  AS planner_bias,
  ROUND(system_bias, 0)   AS system_bias,
  ROUND(abs_error, 0)     AS abs_error,
  ROUND(error_cost, 0)    AS error_cost,
  CASE
    WHEN ABS(planner_bias) > ABS(system_bias) THEN 'OVERRIDE adds error'
    WHEN planner_bias < 0 AND system_bias < 0 THEN 'chronic UNDER-forecast'
    WHEN planner_bias > 0 AND system_bias > 0 THEN 'chronic OVER-forecast'
    ELSE 'mixed'
  END                     AS flag
FROM agg
WHERE (planner_bias <> 0 OR system_bias <> 0) AND abs_error > 0
ORDER BY abs_error DESC;
""")
print("12_rc_bias: done")

# COMMAND ----------
# MAGIC %md ### 13_rc_dormant
# COMMAND ----------
spark.sql("""
-- Wave-1 · 13 · rc_dormant — dormant / E&O: items with no recent shipments but prior history (or never shipped).
-- Source: shipment recency over 10_demand_daily + criticality/managed-hold from dim_series_ext_vw.
-- Managed safety stock (safety_stock_managed_flag='Yes') → intentional reserve, not E&O. DK-17 / V23.
-- WRITE: sandbox_operations.po_management. READ-ONLY sources.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_dormant AS
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`),
recency AS (
  SELECT
    i.item AS item_id,
    MAX(d.series_bigint_key) AS series_bigint_key,
    SUM(CASE WHEN d.date_key BETWEEN 20260301 AND 20260901 THEN d.shipments_history ELSE 0 END) AS recent_ship,
    SUM(CASE WHEN d.date_key BETWEEN 20250101 AND 20260228 THEN d.shipments_history ELSE 0 END) AS prior_ship,
    MAX(CASE WHEN d.shipments_history > 0 THEN d.date_key END)                                   AS last_ship_week
  FROM prod_edw.fact.`10_demand_daily` d
  JOIN latest L ON d.process_date = L.pd
  JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key = i.item_bigint_key
  WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan')
    AND i.item IS NOT NULL
  GROUP BY i.item
),
ser AS (
  SELECT series_bigint_key, inventory_abc_class, standard_cost, safety_stock_managed_flag
  FROM prod_operations.edw_extension.dim_series_ext_vw
)
SELECT
  r.item_id,
  COALESCE(UPPER(s.inventory_abc_class),'UNCLASSIFIED')  AS abc,
  r.last_ship_week,
  CASE WHEN r.prior_ship = 0 THEN 'never' ELSE 'dormant' END AS status,
  (s.safety_stock_managed_flag = 'Yes')                  AS managed_hold,
  CASE WHEN s.safety_stock_managed_flag = 'Yes' THEN 'intentional' ELSE 'review E&O' END AS verdict
FROM recency r
LEFT JOIN ser s ON r.series_bigint_key = s.series_bigint_key
WHERE r.recent_ship = 0            -- nothing shipped in the last 6 months
ORDER BY r.prior_ship DESC;
""")
print("13_rc_dormant: done")

# COMMAND ----------
# MAGIC %md ### 14_rc_case_evidence
# COMMAND ----------
spark.sql("""
-- Wave-1 · 14 · rc_case_evidence — per flagged SKU: real root-cause signals for the investigation page.
-- Bounded to the flagged book. READ-ONLY sources.
-- HONEST NOTE: PO "who-moved-it" slips are NOT included — in this book every slipped PO carries a sentinel
-- original-promise date (2000-01-01), so no genuine reschedule attribution exists. The credible supply-side
-- signal is holds (recency + lag). The demand/supply cause split is DERIVED from the plan's own components.
CREATE OR REPLACE TABLE sandbox_operations.po_management.rc_case_evidence AS
WITH flagged AS (
  SELECT item_id,
    MAX(likely_cause)     AS likely_cause,
    MAX(shortfall_units)  AS shortfall_units,
    MAX(criticality_class) AS criticality_class,
    -- DERIVED cause split from the plan's demand-vs-supply pressure (chipped DERIVED in the UI)
    ROUND(AVG(CASE WHEN total_demand > total_supply THEN total_demand - total_supply ELSE 0 END),0) AS demand_pressure_units
  FROM sandbox_operations.po_management.rc_serving_sku_week
  WHERE severity_class <> 'healthy'
  GROUP BY item_id
),
holds AS (
  SELECT i.item AS item_id,
         COUNT(*)                    AS recent_holds,
         MAX(h.hold_lag_hours)       AS max_hold_lag_hrs
  FROM prod_edw.fact.sales_fulfillment_hold_transactions h
  JOIN prod_edw.dimension.items_scd1 i ON h.item_bigint_key = i.item_bigint_key
  WHERE h.hold_apply_date_key >= 20260601
  GROUP BY i.item
)
SELECT
  f.item_id,
  f.likely_cause,
  f.shortfall_units,
  f.criticality_class,
  f.demand_pressure_units,
  COALESCE(h.recent_holds, 0)  AS recent_holds,
  h.max_hold_lag_hrs
FROM flagged f
LEFT JOIN holds h ON f.item_id = h.item_id;
""")
print("14_rc_case_evidence: done")

# COMMAND ----------
# MAGIC %md ### Gate — reconciliation drift + new lenses populated
# COMMAND ----------
bad = [r for r in spark.sql("SELECT check_name, drift FROM sandbox_operations.po_management.rc_qa_reconciliation WHERE drift IS NOT NULL").collect() if r["drift"] is not None and int(r["drift"]) != 0]
if bad:
    raise Exception(f"Reconciliation drift detected: {bad}")
# new lenses must be non-empty
for t in ["rc_excess","rc_rebalance","rc_bias","rc_dormant","rc_case_evidence"]:
    n = spark.sql(f"SELECT COUNT(*) c FROM sandbox_operations.po_management.{t}").collect()[0]["c"]
    if n == 0:
        raise Exception(f"{t} is empty after refresh")
    print(f"{t}: {n} rows")
print("Gate passed — drift=0, all lenses populated.")