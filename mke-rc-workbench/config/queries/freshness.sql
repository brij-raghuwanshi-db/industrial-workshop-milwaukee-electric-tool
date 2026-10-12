-- Freshness / snapshot stamp — LIVE from rc_run_control + the prior comparison vintage.
-- supply/demand process dates, forward window end, plan, build time, and the prior plan vintage
-- (from rc_snapshot_history) used for the plan-nervousness comparison.
SELECT
  rc.run_label,
  rc.supply_process_date,
  rc.demand_process_date,
  rc.supply_plan_name,
  rc.forward_window_end,
  rc.build_ts,
  (SELECT MAX(prior_vintage) FROM sandbox_operations.po_management.rc_snapshot_history) AS prior_vintage
FROM sandbox_operations.po_management.rc_run_control rc
ORDER BY rc.build_ts DESC
LIMIT 1;
