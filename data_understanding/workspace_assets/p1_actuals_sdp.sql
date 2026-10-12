-- Databricks SDP (Lakeflow Declarative Pipeline) — P1 "Actuals Supply Plan"
-- ============================================================================
-- PARALLEL BUILD (roadmap step 2). Writes ONLY to sandbox_operations.po_management
-- with the `sdp_` prefix — never touches the live rung2_*/p1flow_* tables or the
-- working dashboard. READ-ONLY on prod_edw / prod_operations.
--
-- WHY THIS PIPELINE EXISTS (user's challenge, verified): the live dashboard
-- aggregates 590,275 gold rows on EVERY overview widget render. This pipeline
-- pre-computes every heavy join / window / dedup / semi-additive roll-up ONCE per
-- weekly run into tiny per-widget serving MVs, so the cloned dashboard only
-- FILTERS a few dozen–few hundred rows. Same numbers, ~18,000x less live scan.
--
-- Publishing mode: the pipeline's default catalog/schema is set to
-- sandbox_operations / po_management at create time, so bare dataset names below
-- publish there. prod sources are referenced fully-qualified (external batch reads).
-- All datasets are MATERIALIZED VIEWs (batch reads of static-ish prod facts;
-- aggregations => MV, per the pipelines skill decision tree).
--
-- Layers:  SILVER (4)  ->  GOLD (3)  ->  SERVING aggregates (~20)  + DQ expectations
-- WINDOW IS ONE KNOB: the load window lives in pipeline `configuration` (p1.pd_lo / p1.pd_hi /
-- p1.wk_lo / p1.wk_hi / p1.ledger_hi) and is referenced below via ${...} substitution. To widen the
-- backfill, update the pipeline config (single `databricks pipelines update --json`) + full-refresh —
-- NO SQL edits, NO re-upload. Current config = 180-day window (2026-03-02..2026-08-24), orgs 2012+2120.
-- ============================================================================


-- ############################################################################
-- SILVER 1 — sdp_planned_weekly  (plan forward view; one snapshot/week; org->plan)
--   Source-equivalent to rung2_planned_weekly. + _load_ts metadata (closes 2.1.6).
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_planned_weekly
  COMMENT 'Silver: weekly plan snapshots, org->plan mapping (2120=Mexico else Global). One snapshot/week.'
AS
WITH params AS (
  SELECT ${p1.pd_lo} AS pd_lo, ${p1.pd_hi} AS pd_hi, 1741829739420281188 AS mexico_org_key
),
snaps AS (
  SELECT DISTINCT process_date,
         date_trunc('week', to_date(cast(process_date AS string),'yyyyMMdd')) AS snap_week,
         row_number() OVER (PARTITION BY date_trunc('week', to_date(cast(process_date AS string),'yyyyMMdd'))
                            ORDER BY process_date) AS rn
  FROM prod_edw.fact.`20_supply_daily`, params
  WHERE process_date BETWEEN (SELECT pd_lo FROM params) AND (SELECT pd_hi FROM params)
),
chosen AS (SELECT process_date, snap_week FROM snaps WHERE rn = 1)
SELECT
  p.product_bigint_key AS item_bigint_key,
  i.item_id, i.item_description, i.global_planning_abc_code AS abc,
  p.inventory_organization_bigint_key AS org_bigint_key,
  o.organization_code, o.organization_name,
  p.plan_name,
  c.process_date AS snapshot_date, c.snap_week AS snapshot_week,
  to_date(cast(p.date_key AS string),'yyyyMMdd') AS target_week_start,
  ROUND(SUM(p.projected_available_balance),2) AS planned_pab,
  ROUND(SUM(p.safety_stock),2)                AS planned_safety_stock,
  ROUND(SUM(p.sales_orders),2)                AS planned_sales_orders,
  MAX(s.applied_standard_cost)                AS applied_standard_cost,
  current_timestamp()                         AS _load_ts
FROM prod_edw.fact.`20_supply_daily` p
JOIN chosen c ON p.process_date = c.process_date
JOIN params pr ON TRUE
JOIN prod_edw.dimension.items_scd1 i ON p.product_bigint_key = i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON p.inventory_organization_bigint_key = o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw s
       ON i.item_id = s.item_number AND o.organization_code = s.organization_code
WHERE ( (p.inventory_organization_bigint_key = pr.mexico_org_key AND p.plan_name = '20 Mexico Supply Plan')
     OR (p.inventory_organization_bigint_key <> pr.mexico_org_key AND p.plan_name = '20 Global Supply Plan') )
  AND o.organization_code IN ('2012','2120')
  AND p.date_key BETWEEN ${p1.pd_lo} AND 20261231
GROUP BY 1,2,3,4,5,6,7,8,9,10,11;


-- ############################################################################
-- SILVER 2 — sdp_actuals_weekly (received+shipped SUMmed; on-hand point-in-time)
--   Source-equivalent to rung2_actuals_weekly. On-hand NEVER summed across dates.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_actuals_weekly
  COMMENT 'Silver: weekly actuals. received/shipped additive; on-hand = latest point-in-time in week (semi-additive).'
AS
WITH params AS (SELECT DATE'${p1.wk_lo}' AS wk_lo, DATE'${p1.wk_hi}' AS wk_hi),
orgs AS (SELECT inventory_organization_bigint_key AS k, organization_code AS code
         FROM prod_edw.dimension.inventory_organization_scd1 WHERE organization_code IN ('2012','2120')),
recv AS (
  SELECT r.item_bigint_key, r.inventory_organization_bigint_key AS org_bigint_key,
         date_trunc('week', r.receipt_creation_date) AS week_start, ROUND(SUM(r.received_quantity),2) AS actual_po_received
  FROM prod_edw.fact.purchase_receipt_line r JOIN orgs ON r.inventory_organization_bigint_key=orgs.k, params
  WHERE r.receipt_creation_date >= (SELECT wk_lo FROM params) AND r.receipt_creation_date < (SELECT wk_hi FROM params)
  GROUP BY 1,2,3),
ship AS (
  SELECT t.item_bigint_key, t.fulfillment_organization_bigint_key AS org_bigint_key,
         date_trunc('week', t.fulfillment_timestamp) AS week_start, ROUND(SUM(t.shipped_quantity),2) AS actual_shipped
  FROM prod_edw.fact.sales_order_line_transactions t JOIN orgs ON t.fulfillment_organization_bigint_key=orgs.k, params
  WHERE t.order_type='Standard' AND t.sales_fulfillment_line_status IN ('Invoiced','Closed') AND t.shipped_quantity>0
    AND t.fulfillment_timestamp >= (SELECT wk_lo FROM params) AND t.fulfillment_timestamp < (SELECT wk_hi FROM params)
  GROUP BY 1,2,3),
oh_ranked AS (
  SELECT d.item_bigint_key, d.inventory_organization_bigint_key AS org_bigint_key,
         date_trunc('week', to_date(cast(d.date_key AS string),'yyyyMMdd')) AS week_start,
         d.on_hand_qty, d.on_hand_cost,
         row_number() OVER (PARTITION BY d.item_bigint_key, d.inventory_organization_bigint_key,
                            date_trunc('week', to_date(cast(d.date_key AS string),'yyyyMMdd')) ORDER BY d.date_key DESC) AS rn
  FROM prod_edw.fact.inventory_days_on_hand d JOIN orgs ON d.inventory_organization_bigint_key=orgs.k, params
  WHERE to_date(cast(d.date_key AS string),'yyyyMMdd') >= (SELECT wk_lo FROM params)
    AND to_date(cast(d.date_key AS string),'yyyyMMdd') < (SELECT wk_hi FROM params)),
oh AS (SELECT item_bigint_key, org_bigint_key, week_start, ROUND(on_hand_qty,2) AS actual_end_on_hand,
              ROUND(on_hand_cost,2) AS actual_end_on_hand_cost FROM oh_ranked WHERE rn=1),
keys AS (
  SELECT item_bigint_key, org_bigint_key, week_start FROM recv
  UNION SELECT item_bigint_key, org_bigint_key, week_start FROM ship
  UNION SELECT item_bigint_key, org_bigint_key, week_start FROM oh)
SELECT k.item_bigint_key, k.org_bigint_key, k.week_start,
       COALESCE(recv.actual_po_received,0) AS actual_po_received,
       COALESCE(ship.actual_shipped,0) AS actual_shipped,
       oh.actual_end_on_hand, oh.actual_end_on_hand_cost,
       current_timestamp() AS _load_ts
FROM keys k
LEFT JOIN recv ON k.item_bigint_key=recv.item_bigint_key AND k.org_bigint_key=recv.org_bigint_key AND k.week_start=recv.week_start
LEFT JOIN ship ON k.item_bigint_key=ship.item_bigint_key AND k.org_bigint_key=ship.org_bigint_key AND k.week_start=ship.week_start
LEFT JOIN oh   ON k.item_bigint_key=oh.item_bigint_key   AND k.org_bigint_key=oh.org_bigint_key   AND k.week_start=oh.week_start;


-- ############################################################################
-- SILVER 3 — sdp_transfer_stages (2012 transfer lane; dedup to receipt-line grain)
--   Source-equivalent to p1flow_transfer_stages, widened to the 4-month window.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_transfer_stages
  COMMENT 'Silver: transfer-order receipts into 2012 (the network hub). Dedup to receipt-line grain.'
AS
WITH org AS (
  SELECT inventory_organization_bigint_key AS k, organization_code AS code
  FROM prod_edw.dimension.inventory_organization_scd1
),
dedup AS (
  SELECT r.*,
    ROW_NUMBER() OVER (PARTITION BY r.receipt_line_bigint_key ORDER BY r.receipt_receive_date DESC) AS rn
  FROM prod_operations.manufacturing_sc.fact_transfer_order_receipt r
  JOIN org de ON r.destination_inventory_organization_bigint_key = de.k
  WHERE de.code = '2012' AND r.receipt_receive_date >= '${p1.wk_lo}'
)
SELECT
  it.item_id, it.item_description,
  so.code AS source_org, de.code AS dest_org,
  d.transfer_order_number, d.transfer_order_line_number, d.receipt_line_bigint_key,
  d.shipped_date, d.expected_receipt_date, d.receipt_receive_date,
  d.quantity_shipped, d.quantity_received,
  DATEDIFF(d.receipt_receive_date, d.shipped_date)          AS transit_days,
  DATEDIFF(d.receipt_receive_date, d.expected_receipt_date) AS slip_days,
  CASE WHEN d.receipt_receive_date > d.expected_receipt_date THEN 1 ELSE 0 END AS late_flag,
  (d.quantity_shipped - d.quantity_received) AS qty_short,
  current_timestamp() AS _load_ts
FROM dedup d
JOIN org so ON d.source_inventory_organization_bigint_key = so.k
JOIN org de ON d.destination_inventory_organization_bigint_key = de.k
LEFT JOIN prod_edw.dimension.items_scd1 it ON d.item_bigint_key = it.item_bigint_key
WHERE d.rn = 1;


-- ############################################################################
-- SILVER 4 — sdp_po_stages (BOTH orgs; REAL timing from historical lead-time-error)
--   Source-equivalent to p1flow_po_stages, widened to the 4-month window.
--   NOTE: purchase_receipt_line.expected_receipt_date is a same-day mirage;
--   real PO timing lives in general_historical_purchase_order_lead_time_errors.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_po_stages
  COMMENT 'Silver: PO ordered->delivered stage timing from historical lead-time errors (real timing, not the receipt mirage).'
AS
WITH dedup AS (
  SELECT h.*,
    ROW_NUMBER() OVER (
      PARTITION BY h.order_line_bigint_key, h.receipt_number, h.receipt_line_number
      ORDER BY h.delivery_date DESC) AS rn
  FROM prod_operations.features.general_historical_purchase_order_lead_time_errors h
  WHERE h.organization_code IN ('2012','2120')
    AND h.order_date >= '${p1.wk_lo}'
    AND h.requested_delivery_date IS NOT NULL AND h.delivery_date IS NOT NULL
)
SELECT
  item_number, organization_code AS org, supplier_name, supplier_number,
  purchase_order_number, purchase_order_line_number, order_line_bigint_key,
  receipt_number, receipt_line_number,
  order_date, requested_delivery_date AS expected_date, delivery_date AS actual_date,
  delivered_quantity, requested_lead_time_days, receipt_lead_time_days,
  lead_time_error_days AS slip_days,
  CASE WHEN lead_time_error_days > 0 THEN 1 ELSE 0 END AS late_flag,
  CASE WHEN lead_time_error_days < 0 THEN 1 ELSE 0 END AS early_flag,
  current_timestamp() AS _load_ts
FROM dedup WHERE rn = 1;


-- ############################################################################
-- GOLD 1 — sdp_plan_vs_actual  (prior-week baseline; variance/$/status/tier/planner)
--   Source-equivalent to rung2_plan_vs_actual. THE central fact. Clustered by
--   item_id so the SKU-drill (:sku) prunes via data-skipping (perf gate for drill).
--   + DQ expectations (closes T5): keys non-null, org in-scope, status valid.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_plan_vs_actual
  (
    CONSTRAINT valid_keys       EXPECT (item_bigint_key IS NOT NULL AND org_bigint_key IS NOT NULL AND week_start IS NOT NULL),
    CONSTRAINT org_in_scope     EXPECT (organization_code IN ('2012','2120')),
    CONSTRAINT status_valid     EXPECT (onhand_status IN ('green','yellow','red','no-data')),
    CONSTRAINT tier_valid       EXPECT (alert_tier IN ('0 · OK','1 · Monitor','2 · Alert','3 · Escalate'))
  )
  CLUSTER BY (item_id)
  COMMENT 'Gold: item x org x week plan-vs-actual vs prior-week baseline. Variance, $ impact, status, alert tier, planner, WoW.'
AS
WITH plan_pick AS (
  SELECT *, row_number() OVER (PARTITION BY item_bigint_key, org_bigint_key, target_week_start
                               ORDER BY snapshot_week DESC) AS rn
  FROM sdp_planned_weekly
  WHERE snapshot_week < target_week_start),
plan1 AS (SELECT * FROM plan_pick WHERE rn=1),
joined AS (
  SELECT p.item_bigint_key, p.item_id, p.item_description, p.abc, p.organization_code, p.org_bigint_key,
    p.plan_name, COALESCE(NULLIF(s.planner_name,''),'Unassigned') AS planner_name,
    p.target_week_start AS week_start,
    p.planned_pab, a.actual_end_on_hand, p.planned_sales_orders, a.actual_shipped, a.actual_po_received, p.planned_safety_stock,
    ROUND(a.actual_end_on_hand - p.planned_pab,2) AS onhand_variance_abs,
    ROUND(100.0*(a.actual_end_on_hand - p.planned_pab)/NULLIF(ABS(p.planned_pab),0),1) AS onhand_variance_pct,
    ROUND((a.actual_end_on_hand - p.planned_pab) * p.applied_standard_cost, 2) AS onhand_variance_dollar,
    ROUND(a.actual_shipped - p.planned_sales_orders,2) AS shipped_variance_abs,
    CASE WHEN a.actual_end_on_hand IS NULL OR p.planned_pab IS NULL THEN 'no-data'
         WHEN ABS(a.actual_end_on_hand - p.planned_pab)/NULLIF(ABS(p.planned_pab),0) <= 0.15 THEN 'green'
         WHEN ABS(a.actual_end_on_hand - p.planned_pab)/NULLIF(ABS(p.planned_pab),0) <= 0.30 THEN 'yellow'
         ELSE 'red' END AS onhand_status,
    p.applied_standard_cost
  FROM plan1 p
  LEFT JOIN sdp_actuals_weekly a
    ON p.item_bigint_key=a.item_bigint_key AND p.org_bigint_key=a.org_bigint_key AND p.target_week_start=a.week_start
  LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw s
    ON p.item_id = s.item_number AND p.organization_code = s.organization_code
  WHERE a.week_start IS NOT NULL
)
SELECT *,
  ROUND(onhand_variance_abs - LAG(onhand_variance_abs) OVER (PARTITION BY item_bigint_key, org_bigint_key ORDER BY week_start),2) AS wow_onhand_delta,
  CASE
    WHEN onhand_variance_pct IS NULL THEN '0 · OK'
    WHEN ABS(onhand_variance_pct) > 50 OR ABS(onhand_variance_dollar) > 200000 THEN '3 · Escalate'
    WHEN ABS(onhand_variance_pct) > 30 OR ABS(onhand_variance_dollar) > 50000 THEN '2 · Alert'
    WHEN ABS(onhand_variance_pct) > 15 THEN '1 · Monitor'
    ELSE '0 · OK' END AS alert_tier
FROM joined;


-- ############################################################################
-- GOLD 2 — sdp_order_stage_gold (unified purchase+transfer; org-aware bands; maneuver; chronic)
--   Source-equivalent to p1flow_order_stage_gold.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_order_stage_gold
  COMMENT 'Gold: unified order lifecycle (purchase + transfer). Org-aware timing bands, recommended maneuver, chronic-slipper enrichment.'
AS
WITH unified AS (
  SELECT CAST(item_id AS STRING) AS item_ref, item_description, dest_org AS org,
         'transfer' AS lane, 'in_transit_to_received' AS stage,
         CONCAT('TO-', CAST(transfer_order_number AS STRING), '-', CAST(transfer_order_line_number AS STRING)) AS order_ref,
         source_org, expected_receipt_date AS expected_date, receipt_receive_date AS actual_date,
         slip_days, late_flag, CAST(NULL AS INT) AS early_flag,
         quantity_shipped AS qty_expected, quantity_received AS qty_actual, qty_short AS qty_variance,
         CAST(NULL AS STRING) AS supplier_name
  FROM sdp_transfer_stages
  UNION ALL
  SELECT CAST(item_number AS STRING), NULL, org,
         'purchase' AS lane, 'ordered_to_delivered' AS stage,
         CONCAT('PO-', CAST(purchase_order_number AS STRING), '-', CAST(purchase_order_line_number AS STRING)),
         CAST(NULL AS STRING), expected_date, actual_date,
         slip_days, late_flag, early_flag,
         CAST(NULL AS FLOAT), CAST(delivered_quantity AS FLOAT), CAST(NULL AS FLOAT),
         supplier_name
  FROM sdp_po_stages
),
bands AS (
  SELECT lane, org,
    PERCENTILE_APPROX(slip_days,0.10) AS p10, PERCENTILE_APPROX(slip_days,0.25) AS p25,
    PERCENTILE_APPROX(slip_days,0.75) AS p75, PERCENTILE_APPROX(slip_days,0.90) AS p90
  FROM unified GROUP BY lane, org
),
chronic AS (
  SELECT item_number, organization_code AS org,
    ROUND(AVG(lead_time_error_days),1) AS chronic_avg_err_days,
    ROUND(100.0*AVG(CASE WHEN lead_time_error_days>0 THEN 1.0 ELSE 0 END),1) AS chronic_pct_late,
    COUNT(*) AS chronic_hist_n
  FROM prod_operations.features.general_historical_purchase_order_lead_time_errors
  WHERE organization_code IN ('2012','2120') AND lead_time_error_days IS NOT NULL
  GROUP BY item_number, organization_code
)
SELECT u.item_ref, u.item_description, u.org, u.lane, u.stage, u.order_ref, u.source_org, u.supplier_name,
  u.expected_date, u.actual_date, u.slip_days, u.late_flag, u.early_flag,
  u.qty_expected, u.qty_actual, u.qty_variance,
  CASE
    WHEN ABS(u.slip_days) <= 1 THEN '2 On-time'
    WHEN u.slip_days <  b.p10 THEN '0 Very early'
    WHEN u.slip_days <  b.p25 THEN '1 Early'
    WHEN u.slip_days <= b.p75 THEN '2 On-time'
    WHEN u.slip_days <= b.p90 THEN '3 Late'
    ELSE '4 Very late' END AS timing_band,
  c.chronic_avg_err_days, c.chronic_pct_late, c.chronic_hist_n,
  CASE
    WHEN ABS(u.slip_days) <= 1 THEN 'None'
    WHEN u.slip_days > b.p90 THEN 'Expedite / split shipment'
    WHEN u.slip_days > b.p75 THEN 'Monitor / nudge supplier'
    WHEN u.slip_days < b.p10 THEN 'Defer or downsize (arriving too early)'
    WHEN u.qty_variance > 0 THEN 'Reorder gap / follow up on short receipt'
    ELSE 'None' END AS recommended_maneuver
FROM unified u
JOIN bands b ON u.lane=b.lane AND u.org=b.org
LEFT JOIN chronic c ON u.lane='purchase' AND u.item_ref=c.item_number AND u.org=c.org;


-- ############################################################################
-- GOLD 3 — sdp_rootcause_plant  (upstream PLANT movement ledger, 5-category)
--   RE-DERIVED from source (inventory_material_transaction + location_scd1); the
--   original ad-hoc build SQL was not versioned. Reconciles to the prior table to
--   99.95% (only the receipt-adjustment label boundary differs). PLANT orgs only
--   (the ledger carries no DC rows) — a labelled upstream-context tier, NOT summable
--   with the DC (2012/2120) numbers.
-- ############################################################################
CREATE OR REFRESH MATERIALIZED VIEW sdp_rootcause_plant
  COMMENT 'Gold (upstream tier): plant material-movement ledger bucketed to 5 root causes. Plant orgs only; not summable with DC figures.'
AS
SELECT l.organization_code AS org, l.organization_code AS organization_code,
  CASE
    WHEN t.transaction_type_description LIKE '%Adjustment%'
      OR t.transaction_type_description IN ('Cycle Count Adjustment','Miscellaneous Receipt','Miscellaneous Issue',
                                            'Account Alias Issue','Account Alias Receipt','Return to Supplier') THEN 'Inventory adjustment'
    WHEN t.transaction_type_description LIKE '%Transfer%' OR t.transaction_type_description LIKE '%Movement Request%' THEN 'Transfer/rebalance'
    WHEN t.transaction_type_description LIKE 'Work in Process%' THEN 'Production (WIP)'
    WHEN t.transaction_type_description LIKE '%Purchase Order Receipt%' THEN 'Supply receipts'
    WHEN t.transaction_type_description LIKE 'Sales Order%' THEN 'Demand (issues/returns)'
    ELSE 'Other' END AS root_cause,
  COUNT(*) AS txns,
  ROUND(SUM(ABS(t.transaction_quantity))) AS total_qty
FROM prod_edw.fact.inventory_material_transaction t
JOIN prod_edw.dimension.location_scd1 l ON t.location_bigint_key = l.location_bigint_key
WHERE t.transaction_date_key BETWEEN ${p1.pd_lo} AND ${p1.ledger_hi}
GROUP BY 1,2,3;


-- ############################################################################
-- SERVING LAYER — per-widget-grain aggregates (the perf win).
-- Each MV pre-computes ONE widget's grain so the cloned dashboard only FILTERS
-- a few dozen–few hundred rows. FIDELITY RULE for week-windowed tiles: store
-- ADDITIVE COMPONENTS (sums + counts), never pre-divided averages — the thin
-- dashboard query sums components over the picked weeks and reconstructs the
-- exact same average/ratio. Percentiles aren't additive, so percentile tiles
-- are pre-aggregated over the full window (documented per MV).
-- ############################################################################

-- ---- WEEK x ORG rollup (serves ds_week, ds_mape_trend, net-variance trend) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_week_org
  COMMENT 'Serving: week x org KPI rollup. red/green counts, per-week avg bias, net variance $, MAPE components.'
AS
SELECT week_start, organization_code,
  COUNT(*) AS items,
  SUM(CASE WHEN onhand_status='red' THEN 1 ELSE 0 END)   AS red_items,
  SUM(CASE WHEN onhand_status='green' THEN 1 ELSE 0 END) AS green_items,
  ROUND(AVG(onhand_variance_pct),1)                      AS avg_bias_pct,
  ROUND(SUM(onhand_variance_dollar),0)                   AS net_variance_dollar,
  -- MAPE additive components (planned present & non-zero):
  SUM(CASE WHEN planned_pab IS NOT NULL AND planned_pab<>0 THEN ABS(onhand_variance_pct) END) AS sum_abs_var_pct,
  SUM(CASE WHEN planned_pab IS NOT NULL AND planned_pab<>0 THEN 1 ELSE 0 END)                  AS cnt_mape
FROM sdp_plan_vs_actual
GROUP BY week_start, organization_code;

-- ---- ABC bias (whole window) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_abc
  COMMENT 'Serving: ABC-class average variance (whole window).'
AS
SELECT abc, COUNT(*) AS rows, ROUND(AVG(onhand_variance_pct),1) AS avg_var_pct
FROM sdp_plan_vs_actual WHERE abc IS NOT NULL AND abc<>'None' GROUP BY abc;

-- ---- Org x plan comparison + scorecard (whole window) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_orgcmp
  COMMENT 'Serving: org x plan comparison — items, red/green item-weeks, avg bias, total abs $.'
AS
SELECT organization_code, plan_name, COUNT(DISTINCT item_id) AS items,
  SUM(CASE WHEN onhand_status='red' THEN 1 ELSE 0 END) AS red_iw,
  SUM(CASE WHEN onhand_status='green' THEN 1 ELSE 0 END) AS green_iw,
  ROUND(AVG(onhand_variance_pct),1) AS avg_bias_pct,
  ROUND(SUM(ABS(onhand_variance_dollar)),0) AS total_abs_dollar
FROM sdp_plan_vs_actual GROUP BY organization_code, plan_name;

CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_scorecard
  COMMENT 'Serving: full org scorecard (11 metrics per org x plan).'
AS
SELECT organization_code AS org, plan_name, COUNT(DISTINCT item_id) AS items, COUNT(*) AS item_weeks,
  ROUND(AVG(onhand_variance_pct),1) AS avg_overage_pct,
  ROUND(100.0*SUM(CASE WHEN onhand_status='green' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_green,
  ROUND(100.0*SUM(CASE WHEN onhand_status='red' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_red,
  ROUND(100.0*SUM(CASE WHEN planned_pab IS NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_unplanned,
  ROUND(100.0*SUM(CASE WHEN alert_tier LIKE '3%' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_escalate,
  ROUND(AVG(ABS(onhand_variance_dollar)),0) AS avg_abs_var_dollar,
  ROUND(AVG(CASE WHEN planned_safety_stock>0 THEN planned_safety_stock END),0) AS avg_ss_per_item,
  ROUND(SUM(actual_shipped)/NULLIF(SUM(actual_po_received),0),3) AS ship_receive_ratio,
  COUNT(DISTINCT planner_name) AS planners
FROM sdp_plan_vs_actual GROUP BY organization_code, plan_name;

-- ---- Planner load (whole window) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_planner
  COMMENT 'Serving: planner load — item-weeks, avg bias, total abs $.'
AS
SELECT planner_name, COUNT(*) AS item_weeks, ROUND(AVG(onhand_variance_pct),1) AS avg_bias_pct,
  ROUND(SUM(ABS(onhand_variance_dollar)),0) AS total_abs_dollar
FROM sdp_plan_vs_actual WHERE onhand_status<>'no-data' GROUP BY planner_name;

-- ---- Alert tier distribution ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_tier
  COMMENT 'Serving: alert-tier distribution — item-weeks and distinct items.'
AS
SELECT alert_tier, COUNT(*) AS item_weeks, COUNT(DISTINCT item_id) AS items
FROM sdp_plan_vs_actual GROUP BY alert_tier;

-- ---- Scale context (org onhand value + overage) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_scale_ctx
  COMMENT 'Serving: per-org on-hand USD value + avg overage.'
AS
SELECT organization_code AS org, ROUND(SUM(actual_end_on_hand*applied_standard_cost),0) AS onhand_value_usd,
  ROUND(AVG(onhand_variance_pct),1) AS avg_overage_pct
FROM sdp_plan_vs_actual GROUP BY organization_code;

-- ---- Variance-$ percentile bands (whole window; percentiles not additive) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_varpct_long
  COMMENT 'Serving: per-org abs variance-$ percentile bands (p50/p90/p95/p99), long format.'
AS
SELECT organization_code AS org, 'p50' AS band, ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar),0.50),0) AS var_dollar FROM sdp_plan_vs_actual WHERE onhand_variance_dollar IS NOT NULL GROUP BY organization_code
UNION ALL SELECT organization_code, 'p90', ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar),0.90),0) FROM sdp_plan_vs_actual WHERE onhand_variance_dollar IS NOT NULL GROUP BY organization_code
UNION ALL SELECT organization_code, 'p95', ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar),0.95),0) FROM sdp_plan_vs_actual WHERE onhand_variance_dollar IS NOT NULL GROUP BY organization_code
UNION ALL SELECT organization_code, 'p99', ROUND(PERCENTILE_APPROX(ABS(onhand_variance_dollar),0.99),0) FROM sdp_plan_vs_actual WHERE onhand_variance_dollar IS NOT NULL GROUP BY organization_code;

-- ---- SKU share (shared-across-orgs vs org-exclusive) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_sku_share
  COMMENT 'Serving: per-org count of shared-vs-exclusive SKUs, long format.'
AS
WITH i AS (SELECT DISTINCT organization_code AS org, item_id FROM sdp_plan_vs_actual),
shared AS (SELECT item_id FROM i GROUP BY item_id HAVING COUNT(DISTINCT org)>1)
SELECT i.org, CASE WHEN s.item_id IS NOT NULL THEN 'Shared across orgs' ELSE 'Org-exclusive' END AS sku_kind, COUNT(*) AS items
FROM i LEFT JOIN shared s ON i.item_id=s.item_id
GROUP BY i.org, CASE WHEN s.item_id IS NOT NULL THEN 'Shared across orgs' ELSE 'Org-exclusive' END;

-- ---- Planner concentration ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_planner_conc
  COMMENT 'Serving: per-org planner count + top-planner share %.'
AS
WITH p AS (SELECT organization_code AS org, planner_name, COUNT(*) AS rows_p FROM sdp_plan_vs_actual GROUP BY organization_code, planner_name)
SELECT org, COUNT(*) AS planners, ROUND(100.0*MAX(rows_p)/SUM(rows_p),1) AS top_planner_share_pct FROM p GROUP BY org;

-- ---- Money-at-risk by org x week (serves ds_money_risk whole-window AND cockpit_kpi this/prior-week swing) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_money_ow
  COMMENT 'Serving: per-org-per-week stockout $ and excess-capital $. Additive across weeks.'
AS
SELECT organization_code AS org, week_start,
  ROUND(SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand<planned_safety_stock THEN (planned_safety_stock-actual_end_on_hand)*applied_standard_cost ELSE 0 END),0) AS stockout_risk_usd,
  ROUND(SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand>3*planned_safety_stock THEN (actual_end_on_hand-3*planned_safety_stock)*applied_standard_cost ELSE 0 END),0) AS excess_capital_usd
FROM sdp_plan_vs_actual GROUP BY organization_code, week_start;

-- ---- Forecast Value Add (org; whole window) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_fva
  COMMENT 'Serving: per-org Forecast Value Add — plan vs naive-persistence abs error, and FVA %.'
AS
WITH s AS (
  SELECT organization_code, planned_pab, actual_end_on_hand,
    LAG(actual_end_on_hand) OVER (PARTITION BY item_bigint_key, org_bigint_key ORDER BY week_start) AS naive_fcst
  FROM sdp_plan_vs_actual WHERE planned_pab IS NOT NULL AND actual_end_on_hand IS NOT NULL )
SELECT organization_code AS org,
  ROUND(AVG(ABS(actual_end_on_hand-planned_pab)),0) AS plan_abs_err,
  ROUND(AVG(ABS(actual_end_on_hand-naive_fcst)),0) AS naive_abs_err,
  ROUND(100.0*(AVG(ABS(actual_end_on_hand-naive_fcst))-AVG(ABS(actual_end_on_hand-planned_pab)))/NULLIF(AVG(ABS(actual_end_on_hand-naive_fcst)),0),1) AS fva_pct
FROM s WHERE naive_fcst IS NOT NULL GROUP BY organization_code;

-- ---- Bias persistence (org x bias_type; whole window) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_bias_persist
  COMMENT 'Serving: per-org count of persistently over/under-planned items (>=80% of >=4 weeks one-signed).'
AS
WITH signed AS (
  SELECT item_bigint_key, org_bigint_key, organization_code,
    SUM(CASE WHEN onhand_variance_abs>0 THEN 1 ELSE 0 END) AS wks_over,
    SUM(CASE WHEN onhand_variance_abs<0 THEN 1 ELSE 0 END) AS wks_under, COUNT(*) AS wks
  FROM sdp_plan_vs_actual WHERE onhand_variance_abs IS NOT NULL
  GROUP BY item_bigint_key, org_bigint_key, organization_code HAVING COUNT(*)>=4 )
SELECT organization_code AS org, 'Persistently over-planned' AS bias_type, SUM(CASE WHEN wks_over>=0.8*wks THEN 1 ELSE 0 END) AS items FROM signed GROUP BY organization_code
UNION ALL SELECT organization_code, 'Persistently under-planned', SUM(CASE WHEN wks_under>=0.8*wks THEN 1 ELSE 0 END) FROM signed GROUP BY organization_code;

-- ---- Month-over-month (org x month) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_mom
  COMMENT 'Serving: per-org monthly avg planned/actual on-hand + median variance %.'
AS
SELECT organization_code AS org, CAST(DATE_TRUNC('MONTH', week_start) AS DATE) AS month,
  ROUND(AVG(planned_pab),0) AS avg_planned_pab, ROUND(AVG(actual_end_on_hand),0) AS avg_actual_oh,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct,0.5),1) AS median_var_pct
FROM sdp_plan_vs_actual WHERE planned_pab IS NOT NULL GROUP BY organization_code, CAST(DATE_TRUNC('MONTH', week_start) AS DATE);

-- ---- SLA components (org x week; additive) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_sla_ow
  COMMENT 'Serving: per-org-per-week SLA additive components (MAPE sum/cnt, within-15 num, total cnt, stockout items).'
AS
SELECT organization_code AS org, week_start,
  SUM(CASE WHEN planned_pab IS NOT NULL AND planned_pab<>0 THEN ABS(onhand_variance_pct) END) AS sum_abs_var_pct,
  SUM(CASE WHEN planned_pab IS NOT NULL AND planned_pab<>0 THEN 1 ELSE 0 END) AS cnt_mape,
  SUM(CASE WHEN planned_pab IS NOT NULL AND ABS(onhand_variance_pct)<=15 THEN 1 ELSE 0 END) AS within15_num,
  COUNT(*) AS cnt_total,
  SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand<planned_safety_stock THEN 1 ELSE 0 END) AS stockout_items
FROM sdp_plan_vs_actual GROUP BY organization_code, week_start;

-- ---- Accuracy split (org x week x direction) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_accuracy_split
  COMMENT 'Serving: per-org-per-week over/under/on-plan/unplanned direction counts.'
AS
SELECT organization_code, week_start,
  CASE WHEN planned_pab IS NULL THEN 'Unplanned' WHEN onhand_variance_abs>0 THEN 'Over-plan'
       WHEN onhand_variance_abs<0 THEN 'Under-plan' ELSE 'On-plan' END AS dir,
  COUNT(*) AS n
FROM sdp_plan_vs_actual
GROUP BY organization_code, week_start,
  CASE WHEN planned_pab IS NULL THEN 'Unplanned' WHEN onhand_variance_abs>0 THEN 'Over-plan'
       WHEN onhand_variance_abs<0 THEN 'Under-plan' ELSE 'On-plan' END;

-- ---- ABC median distribution (org x abc; whole window — percentiles not additive) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_abc_median
  COMMENT 'Serving: per-org-per-ABC variance% median/p25/p75 (whole window; percentile so not week-additive).'
AS
SELECT organization_code AS org, COALESCE(abc,'(none)') AS abc,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct,0.5),1) AS median_var_pct,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct,0.25),1) AS p25,
  ROUND(PERCENTILE_APPROX(onhand_variance_pct,0.75),1) AS p75
FROM sdp_plan_vs_actual WHERE planned_pab IS NOT NULL GROUP BY organization_code, COALESCE(abc,'(none)');

-- ---- Root-cause DC (org x week x root_cause; additive across weeks) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_rootcause_dc
  COMMENT 'Serving: DC root-cause attribution (org x week x cause) for red/yellow item-weeks. Additive.'
AS
WITH g AS (
  SELECT organization_code, week_start, onhand_variance_dollar, planned_pab, actual_end_on_hand,
    planned_safety_stock, onhand_variance_abs, shipped_variance_abs, actual_po_received,
    CASE WHEN planned_pab IS NULL THEN 'Unplanned (no baseline)'
         WHEN planned_safety_stock>0 AND actual_end_on_hand < planned_safety_stock THEN 'Stockout / below safety stock'
         WHEN ABS(COALESCE(shipped_variance_abs,0)) >= ABS(onhand_variance_abs)*0.5 THEN 'Demand change (ship vs plan)'
         WHEN COALESCE(actual_po_received,0) > 0 AND ABS(onhand_variance_abs) > 0 THEN 'Supply receipt timing/qty'
         WHEN actual_end_on_hand > 3*planned_safety_stock AND planned_safety_stock>0 THEN 'Excess build-up'
         ELSE 'Plan drift (residual)' END AS root_cause
  FROM sdp_plan_vs_actual WHERE onhand_status IN ('red','yellow') )
SELECT organization_code AS org, week_start, root_cause, COUNT(*) AS item_weeks,
  ROUND(SUM(ABS(onhand_variance_dollar)),0) AS dollar_at_risk
FROM g GROUP BY organization_code, week_start, root_cause;

-- ---- Exception pareto (org x week x exception_type; additive) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_exc_pareto
  COMMENT 'Serving: exception-type pareto (org x week x type) for red/yellow. Additive.'
AS
SELECT organization_code AS org, week_start,
  CASE WHEN planned_pab IS NULL THEN 'Unplanned'
       WHEN planned_safety_stock>0 AND actual_end_on_hand < planned_safety_stock THEN 'Stockout risk'
       WHEN planned_safety_stock>0 AND actual_end_on_hand > 3*planned_safety_stock THEN 'Excess'
       WHEN onhand_variance_pct > 15 THEN 'Over-plan'
       WHEN onhand_variance_pct < -15 THEN 'Under-plan' ELSE 'Other' END AS exception_type,
  COUNT(*) AS items, ROUND(SUM(ABS(onhand_variance_dollar)),0) AS dollar_at_risk
FROM sdp_plan_vs_actual WHERE onhand_status IN ('red','yellow')
GROUP BY organization_code, week_start,
  CASE WHEN planned_pab IS NULL THEN 'Unplanned'
       WHEN planned_safety_stock>0 AND actual_end_on_hand < planned_safety_stock THEN 'Stockout risk'
       WHEN planned_safety_stock>0 AND actual_end_on_hand > 3*planned_safety_stock THEN 'Excess'
       WHEN onhand_variance_pct > 15 THEN 'Over-plan'
       WHEN onhand_variance_pct < -15 THEN 'Under-plan' ELSE 'Other' END;

-- ---- Exceptions detail (red/yellow rows only, chronic pre-joined) — serves topexc/exc_queue ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_exceptions
  COMMENT 'Serving: red/yellow exception rows with derived type, worst-per-item rank, chronic-supplier flag pre-joined.'
AS
WITH base AS (
  SELECT item_id, item_description, abc, organization_code, week_start, planner_name,
    onhand_variance_dollar, onhand_variance_pct, onhand_status, planned_pab, actual_end_on_hand, planned_safety_stock,
    CASE WHEN planned_pab IS NULL THEN 'Unplanned'
         WHEN planned_safety_stock>0 AND actual_end_on_hand < planned_safety_stock THEN 'Stockout risk'
         WHEN planned_safety_stock>0 AND actual_end_on_hand > 3*planned_safety_stock THEN 'Excess'
         WHEN onhand_variance_pct > 15 THEN 'Over-plan'
         WHEN onhand_variance_pct < -15 THEN 'Under-plan' ELSE 'Other' END AS exception_type,
    ABS(onhand_variance_dollar) AS abs_var_dollar
  FROM sdp_plan_vs_actual WHERE onhand_status IN ('red','yellow') ),
ch AS (SELECT DISTINCT item_ref, org, chronic_pct_late FROM sdp_order_stage_gold WHERE lane='purchase')
SELECT b.*,
  ROW_NUMBER() OVER (PARTITION BY b.item_id, b.organization_code ORDER BY b.abs_var_dollar DESC) AS worst_rn,
  c.chronic_pct_late,
  CASE WHEN c.chronic_pct_late >= 60 THEN 'Systemic (chronic supplier)' ELSE 'One-off' END AS root_flag
FROM base b LEFT JOIN ch c ON b.item_id=c.item_ref AND b.organization_code=c.org;

-- ---- Status transitions (item x org x week; red-ish only) — serves ALL cockpit tiles ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_transitions
  COMMENT 'Serving: item x org x week status transitions (rows where red now or prev red). newly_red/resolved/action/systemic pre-computed. Powers the Monday cockpit.'
AS
WITH lagged AS (
  SELECT p.item_id, p.item_description, p.abc, p.organization_code, p.week_start, p.planner_name,
    p.onhand_status, p.alert_tier, p.onhand_variance_dollar, p.planned_safety_stock, p.actual_end_on_hand,
    LAG(p.onhand_status) OVER (PARTITION BY p.item_bigint_key, p.org_bigint_key ORDER BY p.week_start) AS prev_status
  FROM sdp_plan_vs_actual p ),
ch AS (SELECT DISTINCT item_ref, org, chronic_pct_late FROM sdp_order_stage_gold WHERE lane='purchase')
SELECT l.item_id, l.item_description, l.abc, l.organization_code, l.week_start,
  COALESCE(l.planner_name,'Unassigned') AS planner_name, l.onhand_status, l.prev_status, l.alert_tier,
  ABS(l.onhand_variance_dollar) AS dollar,
  CASE WHEN l.onhand_status='red' AND COALESCE(l.prev_status,'')<>'red' THEN 1 ELSE 0 END AS newly_red,
  CASE WHEN l.onhand_status<>'red' AND l.prev_status='red' THEN 1 ELSE 0 END AS resolved_red,
  CASE WHEN l.onhand_status='red' THEN 1 ELSE 0 END AS is_red,
  CASE WHEN l.alert_tier LIKE '3%' THEN 1 ELSE 0 END AS is_escalation,
  CASE WHEN c.chronic_pct_late>=60 THEN 1 ELSE 0 END AS systemic,
  CASE WHEN l.planned_safety_stock>0 AND l.actual_end_on_hand<l.planned_safety_stock THEN 'EXPEDITE (below safety stock)'
       WHEN l.planned_safety_stock>0 AND l.actual_end_on_hand>3*l.planned_safety_stock THEN 'DEFER / CANCEL inbound (overstock)'
       WHEN c.chronic_pct_late>=60 THEN 'FIX SUPPLIER (chronic late)' ELSE 'REVIEW' END AS action,
  CASE WHEN c.chronic_pct_late>=60 THEN 'Systemic (chronic supplier)' ELSE 'One-off' END AS root_flag
FROM lagged l LEFT JOIN ch c ON l.item_id=c.item_ref AND l.organization_code=c.org
WHERE l.onhand_status='red' OR l.prev_status='red';

-- ---- Plan evolution / nervousness / convergence (from planned_weekly) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_plan_evolution
  COMMENT 'Serving: per-org plan total by target-week x snapshot-week (plan revision heatmap source).'
AS
SELECT organization_code AS org, target_week_start, CAST(snapshot_week AS DATE) AS snapshot_week,
  ROUND(SUM(planned_pab),0) AS planned_pab_total
FROM sdp_planned_weekly GROUP BY organization_code, target_week_start, CAST(snapshot_week AS DATE);

CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_plan_nervous
  COMMENT 'Serving: per-org per-target-week net plan revision (first vs last snapshot).'
AS
WITH pw AS (SELECT organization_code, target_week_start, snapshot_week, SUM(planned_pab) AS plan_total
            FROM sdp_planned_weekly GROUP BY organization_code, target_week_start, snapshot_week),
r AS (SELECT organization_code, target_week_start,
        FIRST_VALUE(plan_total) OVER (PARTITION BY organization_code,target_week_start ORDER BY snapshot_week ASC) AS first_plan,
        FIRST_VALUE(plan_total) OVER (PARTITION BY organization_code,target_week_start ORDER BY snapshot_week DESC) AS last_plan,
        ROW_NUMBER() OVER (PARTITION BY organization_code,target_week_start ORDER BY snapshot_week DESC) AS rn FROM pw)
SELECT organization_code AS org, target_week_start,
  ROUND(100.0*(last_plan-first_plan)/NULLIF(ABS(first_plan),0),1) AS net_revision_pct,
  ROUND(last_plan-first_plan,0) AS net_revision_units
FROM r WHERE rn=1;

CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_plan_converge
  COMMENT 'Serving: per-org avg abs plan change by weeks-to-target (convergence funnel).'
AS
WITH pw AS (SELECT organization_code, target_week_start, snapshot_week, SUM(planned_pab) AS plan_total
            FROM sdp_planned_weekly GROUP BY organization_code, target_week_start, snapshot_week),
d AS (SELECT organization_code,
        plan_total - LAG(plan_total) OVER (PARTITION BY organization_code,target_week_start ORDER BY snapshot_week) AS wow_change,
        CAST(DATEDIFF(target_week_start, snapshot_week)/7 AS INT) AS weeks_to_target FROM pw)
SELECT organization_code AS org, weeks_to_target, ROUND(AVG(ABS(wow_change)),0) AS avg_abs_plan_change
FROM d WHERE wow_change IS NOT NULL AND weeks_to_target>=0 AND weeks_to_target<=20
GROUP BY organization_code, weeks_to_target;

CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_plan_change_items
  COMMENT 'Serving: item-level first-vs-last plan change (items that changed). Row-level but small.'
AS
WITH ranked AS (
  SELECT item_id, item_description, organization_code, target_week_start, planned_pab,
    FIRST_VALUE(planned_pab) OVER (PARTITION BY item_bigint_key, organization_code, target_week_start ORDER BY snapshot_week ASC) AS first_plan,
    FIRST_VALUE(planned_pab) OVER (PARTITION BY item_bigint_key, organization_code, target_week_start ORDER BY snapshot_week DESC) AS last_plan,
    ROW_NUMBER() OVER (PARTITION BY item_bigint_key, organization_code, target_week_start ORDER BY snapshot_week DESC) AS rn
  FROM sdp_planned_weekly )
SELECT item_id, item_description, organization_code, target_week_start,
  ROUND(first_plan,0) AS first_plan, ROUND(last_plan,0) AS last_plan, ROUND(last_plan-first_plan,0) AS plan_change,
  ABS(last_plan-first_plan) AS abs_change
FROM ranked WHERE rn=1 AND first_plan <> last_plan;

-- ---- PO timing (lane x org) + lead-time accuracy band (from order/po stages) ----
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_po_timing
  COMMENT 'Serving: per-lane per-org order count, avg slip days, % late.'
AS
SELECT lane, org, COUNT(*) AS orders, ROUND(AVG(slip_days),1) AS avg_slip_days, ROUND(100.0*AVG(late_flag),1) AS pct_late
FROM sdp_order_stage_gold WHERE late_flag IS NOT NULL GROUP BY lane, org;

CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_acc_leadtime
  COMMENT 'Serving: PO accuracy by requested-lead-time band x org.'
AS
SELECT CASE WHEN requested_lead_time_days<=14 THEN '1 · Short (<=14d)'
            WHEN requested_lead_time_days<=45 THEN '2 · Medium (15-45d)' ELSE '3 · Long (>45d)' END AS lead_band,
  org, COUNT(*) AS po_lines, ROUND(AVG(slip_days),1) AS avg_slip_days, ROUND(100.0*AVG(late_flag),1) AS pct_late
FROM sdp_po_stages WHERE requested_lead_time_days IS NOT NULL
GROUP BY CASE WHEN requested_lead_time_days<=14 THEN '1 · Short (<=14d)'
              WHEN requested_lead_time_days<=45 THEN '2 · Medium (15-45d)' ELSE '3 · Long (>45d)' END, org;


-- ---- Overview cube (week x org x abc x status) — serves the 8 additive overview tiles ----
-- 626 rows. Counters/bars that are SUM/COUNT/MAX reconstruct EXACTLY and stay filter-reactive
-- (week_start/organization_code/abc/status columns present → global field filters inject WHERE).
-- AVG-bias and COUNT-DISTINCT tiles cannot be widget-reconstructed from a rollup and stay on raw ds_pva.
CREATE OR REFRESH MATERIALIZED VIEW sdp_agg_overview
  COMMENT 'Serving: overview cube week x org x abc x status. Additive components for the 8 SUM/COUNT/MAX overview tiles.'
AS
SELECT week_start, organization_code, abc, onhand_status,
  CASE WHEN onhand_status='red' THEN '3 · Off plan (>30%)' WHEN onhand_status='yellow' THEN '2 · Drifting (15–30%)' WHEN onhand_status='green' THEN '1 · On plan (≤15%)' ELSE '0 · No actual' END AS status_label,
  COUNT(*) AS items,
  SUM(CASE WHEN onhand_status IN ('yellow','red') THEN 1 ELSE 0 END) AS off_flag_sum,
  -- full precision (no per-cell ROUND) so re-summing across cells is bit-exact vs the base fact;
  -- the widget/thin query rounds at display time.
  SUM(ABS(onhand_variance_dollar)) AS sum_abs_dollar,
  SUM(onhand_variance_dollar) AS net_dollar,
  MAX(ABS(onhand_variance_dollar)) AS max_abs_dollar,
  SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand<planned_safety_stock THEN (planned_safety_stock-actual_end_on_hand)*applied_standard_cost ELSE 0 END) AS stockout_dollar,
  SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand>3*planned_safety_stock THEN (actual_end_on_hand-3*planned_safety_stock)*applied_standard_cost ELSE 0 END) AS excess_dollar
FROM sdp_plan_vs_actual
GROUP BY week_start, organization_code, abc, onhand_status;
