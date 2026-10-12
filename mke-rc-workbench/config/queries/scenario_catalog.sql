-- Scenarios page: the 26-scenario catalog with member counts + spine-coverage. Aggregated (small payload).
SELECT
  scenario_code,
  MAX(scenario_title)  AS scenario_title,
  MAX(activity)        AS activity,
  MAX(requirement_map) AS requirement_map,
  MAX(source_table)    AS source_table,
  MAX(predicate_note)  AS predicate_note,
  COUNT(*)                                            AS member_ids,
  SUM(CASE WHEN joins_to_spine THEN 1 ELSE 0 END)     AS on_spine
FROM sandbox_operations.po_management.rc_scenario_membership
GROUP BY scenario_code
ORDER BY scenario_code;
