-- Databricks notebook source
-- MAGIC %md
-- MAGIC # P1 Actuals Supply Plan — Vertical Slice (Rung 1)
-- MAGIC One item × one org × ~8 weeks, reconciled EDW → Silver → Gold.
-- MAGIC **READ-ONLY** on `prod_edw`/`prod_operations`; **writes only** to `sandbox_operations.po_management.p1slice_*`.
-- MAGIC Anchor: item 48111850 (M18 XC5.0 Battery) @ org 2012 Olive Branch, plan '20 Global Supply Plan'.
-- MAGIC Set-based + parameterized so Rung 2 (all items, 8 wks) and Rung 3 (full year, bounded backfill + weekly MERGE) are filter-widening, not rewrites.

-- COMMAND ----------

-- MAGIC %md ## Step 0 — write-privilege smoke test (drop after)

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS sandbox_operations.po_management.p1slice_smoke AS SELECT 1 AS ok;

-- COMMAND ----------

DROP TABLE sandbox_operations.po_management.p1slice_smoke;

-- COMMAND ----------

-- MAGIC %md ## Step 1 — Silver: planned_weekly (the plan's forward view, one snapshot per week)

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.p1slice_planned_weekly AS
WITH params AS (
  SELECT 3879620845706693458 AS anchor_item, 776578178872804310 AS anchor_org,
         20260706 AS pd_lo, 20260829 AS pd_hi, '20 Global Supply Plan' AS plan_nm
),
snaps AS (  -- one snapshot per week = earliest process_date in each Monday-week
  SELECT DISTINCT process_date,
         date_trunc('week', to_date(cast(process_date AS string),'yyyyMMdd')) AS snap_week,
         row_number() OVER (PARTITION BY date_trunc('week', to_date(cast(process_date AS string),'yyyyMMdd'))
                            ORDER BY process_date) AS rn
  FROM prod_edw.fact.`20_supply_daily`, params
  WHERE process_date BETWEEN (SELECT pd_lo FROM params) AND (SELECT pd_hi FROM params)
    AND product_bigint_key = (SELECT anchor_item FROM params)
    AND inventory_organization_bigint_key = (SELECT anchor_org FROM params)
    AND plan_name = (SELECT plan_nm FROM params)
),
chosen AS (SELECT process_date, snap_week FROM snaps WHERE rn = 1)
SELECT
  p.product_bigint_key AS item_bigint_key,
  i.item_id, i.item_description, i.global_planning_abc_code AS abc,
  p.inventory_organization_bigint_key AS org_bigint_key,
  o.organization_code, o.organization_name,
  c.process_date AS snapshot_date, c.snap_week AS snapshot_week,
  to_date(cast(p.date_key AS string),'yyyyMMdd') AS target_week_start,
  ROUND(SUM(p.projected_available_balance),2) AS planned_pab,
  ROUND(SUM(p.safety_stock),2)                AS planned_safety_stock,
  ROUND(SUM(p.sales_orders),2)                AS planned_sales_orders,
  MAX(s.applied_standard_cost)                AS applied_standard_cost
FROM prod_edw.fact.`20_supply_daily` p
JOIN chosen c ON p.process_date = c.process_date
JOIN params pr ON TRUE
JOIN prod_edw.dimension.items_scd1 i ON p.product_bigint_key = i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON p.inventory_organization_bigint_key = o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw s
       ON i.item_id = s.item_number AND o.organization_code = s.organization_code
WHERE p.product_bigint_key = pr.anchor_item
  AND p.inventory_organization_bigint_key = pr.anchor_org
  AND p.plan_name = pr.plan_nm
  AND p.date_key BETWEEN 20260706 AND 20261231
GROUP BY 1,2,3,4,5,6,7,8,9,10;

-- COMMAND ----------

-- MAGIC %md ## Step 2 — Silver: actuals_weekly (received + shipped summed; on-hand point-in-time, NEVER summed)

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.p1slice_actuals_weekly AS
WITH params AS (SELECT 3879620845706693458 AS anchor_item, 776578178872804310 AS anchor_org,
                       DATE'2026-07-06' AS wk_lo, DATE'2026-08-31' AS wk_hi),
recv AS (  -- FLOW: sum received (clean fact, EDW keys)
  SELECT date_trunc('week', receipt_creation_date) AS week_start, ROUND(SUM(received_quantity),2) AS actual_po_received
  FROM prod_edw.fact.purchase_receipt_line, params
  WHERE item_bigint_key=(SELECT anchor_item FROM params) AND inventory_organization_bigint_key=(SELECT anchor_org FROM params)
    AND receipt_creation_date >= (SELECT wk_lo FROM params) AND receipt_creation_date < (SELECT wk_hi FROM params)
  GROUP BY 1),
ship AS (  -- FLOW: sum shipped, Standard + Invoiced/Closed + non-null (the 87%-null trap)
  SELECT date_trunc('week', fulfillment_timestamp) AS week_start, ROUND(SUM(shipped_quantity),2) AS actual_shipped
  FROM prod_edw.fact.sales_order_line_transactions, params
  WHERE item_bigint_key=(SELECT anchor_item FROM params) AND fulfillment_organization_bigint_key=(SELECT anchor_org FROM params)
    AND order_type='Standard' AND sales_fulfillment_line_status IN ('Invoiced','Closed') AND shipped_quantity>0
    AND fulfillment_timestamp >= (SELECT wk_lo FROM params) AND fulfillment_timestamp < (SELECT wk_hi FROM params)
  GROUP BY 1),
oh_ranked AS (  -- STOCK: point-in-time, take the week's latest date_key
  SELECT date_trunc('week', to_date(cast(date_key AS string),'yyyyMMdd')) AS week_start, on_hand_qty, on_hand_cost,
         row_number() OVER (PARTITION BY date_trunc('week', to_date(cast(date_key AS string),'yyyyMMdd')) ORDER BY date_key DESC) AS rn
  FROM prod_edw.fact.inventory_days_on_hand, params
  WHERE item_bigint_key=(SELECT anchor_item FROM params) AND inventory_organization_bigint_key=(SELECT anchor_org FROM params)
    AND to_date(cast(date_key AS string),'yyyyMMdd') >= (SELECT wk_lo FROM params)
    AND to_date(cast(date_key AS string),'yyyyMMdd') < (SELECT wk_hi FROM params)),
oh AS (SELECT week_start, ROUND(on_hand_qty,2) AS actual_end_on_hand, ROUND(on_hand_cost,2) AS actual_end_on_hand_cost FROM oh_ranked WHERE rn=1),
wks AS (SELECT week_start FROM recv UNION SELECT week_start FROM ship UNION SELECT week_start FROM oh)
SELECT (SELECT anchor_item FROM params) AS item_bigint_key, (SELECT anchor_org FROM params) AS org_bigint_key,
       w.week_start, COALESCE(recv.actual_po_received,0) AS actual_po_received,
       COALESCE(ship.actual_shipped,0) AS actual_shipped, oh.actual_end_on_hand, oh.actual_end_on_hand_cost
FROM wks w
LEFT JOIN recv ON w.week_start=recv.week_start
LEFT JOIN ship ON w.week_start=ship.week_start
LEFT JOIN oh   ON w.week_start=oh.week_start;

-- COMMAND ----------

-- MAGIC %md ## Step 3 — Gold: plan_vs_actual (prior-snapshot plan vs actual; variance + $ impact + status)

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.p1slice_plan_vs_actual AS
WITH plan_pick AS (
  SELECT *, row_number() OVER (PARTITION BY item_bigint_key, org_bigint_key, target_week_start ORDER BY snapshot_date) AS rn
  FROM sandbox_operations.po_management.p1slice_planned_weekly),
plan1 AS (SELECT * FROM plan_pick WHERE rn=1)
SELECT p.item_id, p.item_description, p.abc, p.organization_code, p.target_week_start AS week_start,
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
LEFT JOIN sandbox_operations.po_management.p1slice_actuals_weekly a
  ON p.item_bigint_key=a.item_bigint_key AND p.org_bigint_key=a.org_bigint_key AND p.target_week_start=a.week_start
WHERE a.week_start IS NOT NULL
ORDER BY p.target_week_start;

-- COMMAND ----------

-- MAGIC %md ## Step 4 — Reconciliation checks (evidence)

-- COMMAND ----------

-- Recon A: Gold actual_po_received ties to raw weekly receipt SUM (week 2026-08-10)
SELECT 'gold' AS src, actual_po_received AS v
FROM sandbox_operations.po_management.p1slice_plan_vs_actual WHERE week_start='2026-08-10'
UNION ALL
SELECT 'raw', ROUND(SUM(received_quantity),2)
FROM prod_edw.fact.purchase_receipt_line
WHERE item_bigint_key=3879620845706693458 AND inventory_organization_bigint_key=776578178872804310
  AND date_trunc('week', receipt_creation_date)=DATE'2026-08-10';

-- COMMAND ----------

-- Recon B: semi-additivity guard — WRONG summed vs RIGHT point-in-time (week of 08-24)
SELECT ROUND(SUM(on_hand_qty),0) AS wrong_summed,
       MAX_BY(on_hand_qty, date_key) AS right_pointintime
FROM prod_edw.fact.inventory_days_on_hand
WHERE item_bigint_key=3879620845706693458 AND inventory_organization_bigint_key=776578178872804310
  AND to_date(cast(date_key AS string),'yyyyMMdd') BETWEEN DATE'2026-08-24' AND DATE'2026-08-30';

-- COMMAND ----------

-- Final: the reconciled slice
SELECT week_start, planned_pab, actual_end_on_hand, onhand_variance_abs, onhand_variance_pct,
       onhand_variance_dollar, onhand_status, planned_sales_orders, actual_shipped, actual_po_received
FROM sandbox_operations.po_management.p1slice_plan_vs_actual ORDER BY week_start;
