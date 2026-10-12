-- Case-file evidence for one SKU: live root-cause signals for the investigation page.
-- Holds are the real supply-side signal (PO who-moved-it is absent — sentinel originals).
-- demand_pressure_units is DERIVED from the plan's demand-vs-supply split (chip DERIVED in UI).
-- @param item_id STRING
SELECT
  item_id,
  likely_cause,
  shortfall_units,
  criticality_class,
  demand_pressure_units,
  recent_holds,
  max_hold_lag_hrs
FROM sandbox_operations.po_management.rc_case_evidence
WHERE item_id = :item_id;
