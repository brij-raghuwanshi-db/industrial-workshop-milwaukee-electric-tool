-- Supplier constraints / concentration lens — supplier dimension of rc_pattern_rollup.
-- Each row: a supplier, its dominant cause, how many flagged SKUs and $ ride on it.
SELECT
  group_key   AS supplier,
  likely_cause,
  sku_count,
  ROUND(dollars_at_risk, 0) AS dollars_at_risk
FROM sandbox_operations.po_management.rc_pattern_rollup
WHERE dimension = 'supplier'
ORDER BY dollars_at_risk DESC
LIMIT 200;
