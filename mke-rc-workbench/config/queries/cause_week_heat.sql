-- Cause × week heatmap (DK-22): one drill level at a time. Filter by level + parent_filter.
-- @param level STRING
-- @param parent_filter STRING
SELECT
  row_key,
  row_label,
  week,
  cell_value_signed,
  at_risk_skus,
  child_row_count
FROM sandbox_operations.po_management.rc_cause_week_heat
WHERE level = :level
  AND parent_filter = :parent_filter
ORDER BY row_label, week;
