-- Hero drill: which scenarios a given SKU belongs to (from rc_scenario_membership).
-- @param item_id STRING
SELECT scenario_code, MAX(scenario_title) AS scenario_title, MAX(requirement_map) AS requirement_map
FROM sandbox_operations.po_management.rc_scenario_membership
WHERE item_id = :item_id
GROUP BY scenario_code
ORDER BY scenario_code;
