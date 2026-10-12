-- Analytics: portfolio health by status — book value = on_hand × std_cost (the real book, not shortfall $).
-- Chart-shaped: health_status on X, dollars/sku_count as measures.
WITH per_sku AS (
  SELECT
    item_id,
    MAX(CASE WHEN severity_class = 'healthy' THEN 'aligned'
             WHEN severity_class = 'projected-negative-PAB' THEN 'short'
             ELSE 'at-risk' END)                    AS health_status,
    MAX(on_hand) * MAX(std_cost)                     AS book_value
  FROM sandbox_operations.po_management.rc_serving_sku_week
  GROUP BY item_id
)
SELECT
  health_status,
  COUNT(*)                              AS sku_count,
  ROUND(SUM(COALESCE(book_value, 0)), 0) AS dollars
FROM per_sku
GROUP BY health_status
ORDER BY health_status;
