-- Analytics KPI header: inventory alignment = aligned book value / total book value.
-- Book value = on_hand × std_cost (real dollars sitting on the shelf), not shortfall.
WITH per_sku AS (
  SELECT
    item_id,
    MAX(CASE WHEN severity_class = 'healthy' THEN 1 ELSE 0 END) AS is_aligned,
    MAX(on_hand) * MAX(std_cost)                                AS book_value
  FROM sandbox_operations.po_management.rc_serving_sku_week
  GROUP BY item_id
)
SELECT
  ROUND(100.0 * SUM(CASE WHEN is_aligned = 1 THEN COALESCE(book_value, 0) ELSE 0 END)
        / NULLIF(SUM(COALESCE(book_value, 0)), 0), 0)  AS alignment_pct,
  ROUND(SUM(COALESCE(book_value, 0)), 0)               AS total_book_value,
  COUNT(*)                                             AS total_skus,
  SUM(is_aligned)                                      AS aligned_skus
FROM per_sku;
