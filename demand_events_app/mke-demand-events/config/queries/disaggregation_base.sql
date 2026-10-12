-- READ-ONLY source: prod_edw.fact.10_demand_daily + dims
-- Base-measure shares for ratio disaggregation of one item across mkedg5 customers.
-- Default measure = planner_baseline (live-verified column name). The app posts
-- these (mkedg5, base_measure) pairs to /api/events/:id/disaggregate.
-- Dash-less item_id (e.g. 369722 for hero 3697-22).
-- @param item_id STRING = 369722
SELECT
  c.mkedg5,
  SUM(f.planner_baseline) AS base_measure
FROM prod_edw.fact.`10_demand_daily` f
JOIN prod_edw.dimension.items_scd1 i
  ON f.product_bigint_key = i.item_bigint_key
JOIN prod_edw.dimension.dg5_customer_scd1 c
  ON f.dg5_customer_bigint_key = c.dg5_customer_bigint_key
WHERE i.item_id = :item_id
GROUP BY c.mkedg5
HAVING SUM(f.planner_baseline) IS NOT NULL
ORDER BY base_measure DESC
