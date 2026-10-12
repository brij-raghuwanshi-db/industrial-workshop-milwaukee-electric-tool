-- Drill: the member IDs of one scenario (join spine for badges where present).
-- @param scenario_code STRING
SELECT
  m.item_id,
  m.in_seed_catalog,
  m.joins_to_spine,
  s.criticality_class,
  s.recoverability_class,
  s.action_verdict,
  s.lifecycle_class,
  ROUND(s.committed_value, 0) AS dollars_at_risk
FROM sandbox_operations.po_management.rc_scenario_membership m
LEFT JOIN (
  SELECT item_id,
         MAX(criticality_class)    AS criticality_class,
         MAX(recoverability_class) AS recoverability_class,
         MAX(action_verdict)       AS action_verdict,
         MAX(lifecycle_class)      AS lifecycle_class,
         MAX(committed_value)      AS committed_value
  FROM sandbox_operations.po_management.rc_serving_sku_week
  GROUP BY item_id
) s ON m.item_id = s.item_id
WHERE m.scenario_code = :scenario_code
ORDER BY dollars_at_risk DESC NULLS LAST
LIMIT 200;
