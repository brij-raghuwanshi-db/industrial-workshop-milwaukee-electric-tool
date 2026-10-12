-- Watchlist / Control Tower — one row per flagged SKU (worst org×week), sorted criticality × recoverability × verdict.
-- Reads rc_serving_sku_week (serving layer). Only flagged items (severity <> healthy).
WITH per_sku AS (
  SELECT
    item_id,
    MAX(selling_item_number)                                   AS selling_item_number,
    MAX(item_description)                                      AS item_description,
    MIN(projected_available_balance)                           AS low_point,
    MAX(safety_stock)                                          AS safety_stock,
    MAX(shortfall_units)                                       AS shortfall_units,
    MAX(committed_value)                                       AS dollars_at_risk,
    MAX(criticality_class)                                     AS criticality_class,
    MAX(recoverability_class)                                  AS recoverability_class,
    MAX(temporal_class)                                        AS temporal_class,
    MAX(lifecycle_class)                                       AS lifecycle_class,
    MAX(action_verdict)                                        AS action_verdict,
    MAX(likely_cause)                                          AS likely_cause,
    MAX(intentional_hold)                                      AS intentional_hold,
    MIN(CASE WHEN projected_available_balance < safety_stock THEN date_key END) AS first_risk_week
  FROM sandbox_operations.po_management.rc_serving_sku_week
  WHERE severity_class <> 'healthy'
  GROUP BY item_id
)
SELECT
  item_id, selling_item_number, item_description,
  low_point, safety_stock, shortfall_units,
  ROUND(dollars_at_risk, 0)                                    AS dollars_at_risk,
  criticality_class, recoverability_class, temporal_class, lifecycle_class,
  action_verdict, likely_cause, intentional_hold, first_risk_week
FROM per_sku
ORDER BY
  CASE action_verdict WHEN 'ACT' THEN 0 WHEN 'WATCH' THEN 1 ELSE 2 END,
  CASE criticality_class WHEN 'A' THEN 0 WHEN 'B' THEN 1 WHEN 'C' THEN 2 ELSE 3 END,
  CASE recoverability_class WHEN 'UNRECOVERABLE' THEN 0 ELSE 1 END,
  dollars_at_risk DESC
LIMIT 200;
