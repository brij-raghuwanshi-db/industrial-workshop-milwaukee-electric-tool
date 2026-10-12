-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Rung 2 — Actuals Supply Plan build (ALL items × orgs 2012+2120 × 4 months)
-- MAGIC READ-ONLY on `prod_edw`/`prod_operations`; writes only to `sandbox_operations.po_management.rung2_*`.
-- MAGIC **180-day window** (Monday snapshots 2026-03-02 → 2026-08-24; one snapshot per week).
-- MAGIC Org→plan: 2120 → '20 Mexico Supply Plan', all else → '20 Global Supply Plan' (kills the 2120 double-count).
-- MAGIC Same set-based logic as the Rung-1 slice with the item filter dropped + org→plan predicate + planner/wow/alert_tier.
-- MAGIC This notebook IS the reproducible source of the gold; Run All rebuilds all three tables idempotently.

-- COMMAND ----------
-- MAGIC %md ## Params — the ONLY things that change between rungs (window + org list)

-- COMMAND ----------
-- MAGIC %md ## Step 1 — Silver: rung2_planned_weekly (plan forward view, one snapshot/week, org→plan mapping)

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.rung2_planned_weekly AS
WITH params AS (
  SELECT 20260302 AS pd_lo, 20260824 AS pd_hi,          -- 4-month backfill: Monday snapshots
         1741829739420281188 AS mexico_org_key           -- org 2120 bigint key (on the Mexico plan)
),
snaps AS (  -- one snapshot per week = earliest process_date in each Monday-week
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
  MAX(s.applied_standard_cost)                AS applied_standard_cost
FROM prod_edw.fact.`20_supply_daily` p
JOIN chosen c ON p.process_date = c.process_date
JOIN params pr ON TRUE
JOIN prod_edw.dimension.items_scd1 i ON p.product_bigint_key = i.item_bigint_key
JOIN prod_edw.dimension.inventory_organization_scd1 o ON p.inventory_organization_bigint_key = o.inventory_organization_bigint_key
LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw s
       ON i.item_id = s.item_number AND o.organization_code = s.organization_code
-- org->plan predicate: 2120 on Mexico plan, everyone else on Global (prevents 2120 double-count)
WHERE ( (p.inventory_organization_bigint_key = pr.mexico_org_key AND p.plan_name = '20 Mexico Supply Plan')
     OR (p.inventory_organization_bigint_key <> pr.mexico_org_key AND p.plan_name = '20 Global Supply Plan') )
  AND o.organization_code IN ('2012','2120')
  AND p.date_key BETWEEN 20260302 AND 20261231
GROUP BY 1,2,3,4,5,6,7,8,9,10,11;

-- COMMAND ----------
-- MAGIC %md ## Step 2 — Silver: rung2_actuals_weekly (received+shipped summed; on-hand point-in-time, NEVER summed) — all items, both orgs

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.rung2_actuals_weekly AS
WITH params AS (SELECT DATE'2026-03-02' AS wk_lo, DATE'2026-08-31' AS wk_hi),
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
       oh.actual_end_on_hand, oh.actual_end_on_hand_cost
FROM keys k
LEFT JOIN recv ON k.item_bigint_key=recv.item_bigint_key AND k.org_bigint_key=recv.org_bigint_key AND k.week_start=recv.week_start
LEFT JOIN ship ON k.item_bigint_key=ship.item_bigint_key AND k.org_bigint_key=ship.org_bigint_key AND k.week_start=ship.week_start
LEFT JOIN oh   ON k.item_bigint_key=oh.item_bigint_key   AND k.org_bigint_key=oh.org_bigint_key   AND k.week_start=oh.week_start;

-- COMMAND ----------
-- MAGIC %md ## Step 3 — Gold: rung2_plan_vs_actual (prior-snapshot plan vs actual; variance, $ impact, status, planner, WoW, alert tier)

-- COMMAND ----------

CREATE OR REPLACE TABLE sandbox_operations.po_management.rung2_plan_vs_actual AS
WITH plan_pick AS (
  -- prior-week baseline (doc 5.1): nearest snapshot STRICTLY BEFORE the target week => consistent ~1-week lookback
  SELECT *, row_number() OVER (PARTITION BY item_bigint_key, org_bigint_key, target_week_start
                               ORDER BY snapshot_week DESC) AS rn
  FROM sandbox_operations.po_management.rung2_planned_weekly
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
  LEFT JOIN sandbox_operations.po_management.rung2_actuals_weekly a
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

-- COMMAND ----------
-- MAGIC %md ## Step 4 — Reconciliation (evidence)

-- COMMAND ----------

-- Grain: rows == distinct item×org×week (no fanout); months now = 4
SELECT COUNT(*) AS rows_total,
       COUNT(DISTINCT concat(item_bigint_key,'|',org_bigint_key,'|',cast(week_start AS string))) AS distinct_grain,
       COUNT(DISTINCT date_trunc('MONTH', week_start)) AS months,
       COUNT(DISTINCT week_start) AS weeks
FROM sandbox_operations.po_management.rung2_plan_vs_actual;

-- COMMAND ----------

-- Per-org counts
SELECT organization_code, COUNT(*) AS rows, COUNT(DISTINCT item_id) AS items
FROM sandbox_operations.po_management.rung2_plan_vs_actual GROUP BY organization_code ORDER BY organization_code;
