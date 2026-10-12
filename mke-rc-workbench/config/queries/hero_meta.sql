-- Hero badges/meta for one SKU (single row).
-- @param item_id STRING
SELECT
  MAX(likely_cause)        AS likely_cause,
  MAX(criticality_class)   AS criticality_class,
  MAX(recoverability_class) AS recoverability_class,
  MAX(temporal_class)      AS temporal_class,
  MAX(lifecycle_class)     AS lifecycle_class,
  MAX(action_verdict)      AS action_verdict
FROM sandbox_operations.po_management.rc_serving_sku_week
WHERE item_id = :item_id;
