-- Hero investigation: forward PAB-vs-SS curve for one SKU, aggregated across orgs by week
-- (worst PAB per week so the line is clean and comparable to safety stock).
-- @param item_id STRING
SELECT
  date_key,
  MIN(projected_available_balance) AS projected_available_balance,
  MAX(safety_stock)                AS safety_stock,
  SUM(shortfall_units)             AS shortfall_units
FROM sandbox_operations.po_management.rc_serving_sku_week
WHERE item_id = :item_id
GROUP BY date_key
ORDER BY date_key;
