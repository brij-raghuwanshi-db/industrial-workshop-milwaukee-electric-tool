-- Analytics: driver pattern rollup (supplier / org / criticality) ranked by $-at-risk.
-- @param dimension STRING
SELECT
  group_key,
  likely_cause,
  sku_count,
  dollars_at_risk
FROM sandbox_operations.po_management.rc_pattern_rollup
WHERE dimension = :dimension
ORDER BY dollars_at_risk DESC NULLS LAST
LIMIT 50;
