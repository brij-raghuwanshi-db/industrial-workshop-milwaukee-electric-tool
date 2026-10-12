-- Excess / E&O lens — every SKU whose projected position sits well above target. Live from rc_excess.
SELECT
  item_id,
  min_pab,
  safety_stock,
  criticality_class,
  surplus_units,
  dollars,
  weeks_cover,
  driver
FROM sandbox_operations.po_management.rc_excess
ORDER BY dollars DESC
LIMIT 200;
