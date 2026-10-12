-- Databricks notebook source
-- MAGIC %md
-- MAGIC # P1FLOW — Order-Lifecycle / Stage-Timing Slice (Rung 1)
-- MAGIC Preemptive expected-vs-actual by stage, org-aware bands, recommended maneuver, chronic-slipper signal.
-- MAGIC READ-ONLY on prod_edw/prod_operations; writes only to sandbox_operations.po_management.p1flow_*.
-- MAGIC See P1FLOW_BUILDLOG.md for evidence. Warehouse 7bd33a82f4e92206, profile mke-rsc.

-- COMMAND ----------
-- MAGIC %md ## Step 1 — p1flow_transfer_stages (2012 transfer lane; dedup to receipt-line grain)

-- COMMAND ----------
CREATE OR REPLACE TABLE sandbox_operations.po_management.p1flow_transfer_stages AS
WITH org AS (
  SELECT inventory_organization_bigint_key AS k, organization_code AS code
  FROM prod_edw.dimension.inventory_organization_scd1
),
dedup AS (
  SELECT r.*,
    ROW_NUMBER() OVER (PARTITION BY r.receipt_line_bigint_key ORDER BY r.receipt_receive_date DESC) AS rn
  FROM prod_operations.manufacturing_sc.fact_transfer_order_receipt r
  JOIN org de ON r.destination_inventory_organization_bigint_key = de.k
  WHERE de.code = '2012' AND r.receipt_receive_date >= '2026-03-02'   -- 180-day window (aligned to gold)
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
  (d.quantity_shipped - d.quantity_received) AS qty_short
FROM dedup d
JOIN org so ON d.source_inventory_organization_bigint_key = so.k
JOIN org de ON d.destination_inventory_organization_bigint_key = de.k
LEFT JOIN prod_edw.dimension.items_scd1 it ON d.item_bigint_key = it.item_bigint_key
WHERE d.rn = 1;

-- COMMAND ----------
-- MAGIC %md ## Step 2 — p1flow_po_stages (BOTH orgs; REAL timing from historical lead-time-error)
-- MAGIC NOTE: prod_edw.fact.purchase_receipt_line.expected_receipt_date is a MIRAGE (== receipt date same-day
-- MAGIC 100%). Real PO timing = prod_operations.features.general_historical_purchase_order_lead_time_errors.

-- COMMAND ----------
CREATE OR REPLACE TABLE sandbox_operations.po_management.p1flow_po_stages AS
WITH dedup AS (
  SELECT h.*,
    ROW_NUMBER() OVER (
      PARTITION BY h.order_line_bigint_key, h.receipt_number, h.receipt_line_number
      ORDER BY h.delivery_date DESC) AS rn
  FROM prod_operations.features.general_historical_purchase_order_lead_time_errors h
  WHERE h.organization_code IN ('2012','2120')
    AND h.order_date >= '2026-03-02'
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
  CASE WHEN lead_time_error_days < 0 THEN 1 ELSE 0 END AS early_flag
FROM dedup WHERE rn = 1;

-- COMMAND ----------
-- MAGIC %md ## Step 3 + 3b — p1flow_order_stage_gold (unified, org-aware bands, maneuver, chronic-slip enrichment)

-- COMMAND ----------
CREATE OR REPLACE TABLE sandbox_operations.po_management.p1flow_order_stage_gold AS
WITH unified AS (
  SELECT CAST(item_id AS STRING) AS item_ref, item_description, dest_org AS org,
         'transfer' AS lane, 'in_transit_to_received' AS stage,
         CONCAT('TO-', CAST(transfer_order_number AS STRING), '-', CAST(transfer_order_line_number AS STRING)) AS order_ref,
         source_org, expected_receipt_date AS expected_date, receipt_receive_date AS actual_date,
         slip_days, late_flag, CAST(NULL AS INT) AS early_flag,
         quantity_shipped AS qty_expected, quantity_received AS qty_actual, qty_short AS qty_variance,
         CAST(NULL AS STRING) AS supplier_name
  FROM sandbox_operations.po_management.p1flow_transfer_stages
  UNION ALL
  SELECT CAST(item_number AS STRING), NULL, org,
         'purchase' AS lane, 'ordered_to_delivered' AS stage,
         CONCAT('PO-', CAST(purchase_order_number AS STRING), '-', CAST(purchase_order_line_number AS STRING)),
         CAST(NULL AS STRING), expected_date, actual_date,
         slip_days, late_flag, early_flag,
         CAST(NULL AS FLOAT), CAST(delivered_quantity AS FLOAT), CAST(NULL AS FLOAT),
         supplier_name
  FROM sandbox_operations.po_management.p1flow_po_stages
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

-- COMMAND ----------
-- MAGIC %md ## Reconcile (see P1FLOW_BUILDLOG.md): grain==distinct, gold slip==source slip (7.159 / 5.375), org-aware bands.
