-- Live value baseline for the ledger / value pages — from rc_value_baseline_daily (Job-published).
-- at_risk_dollars = committed $ on the flagged book at this snapshot; unrecoverable_dollars = the locked-in slice.
SELECT
  baseline_snapshot_id,
  as_of_date,
  ROUND(at_risk_dollars, 0)        AS at_risk_dollars,
  at_risk_sku_count,
  ROUND(unrecoverable_dollars, 0)  AS unrecoverable_dollars,
  build_ts
FROM sandbox_operations.po_management.rc_value_baseline_daily
ORDER BY as_of_date DESC
LIMIT 1;
