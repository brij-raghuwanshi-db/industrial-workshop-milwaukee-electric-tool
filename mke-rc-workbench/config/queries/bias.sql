-- Forecast bias / FVA lens — governed, per DG5 channel. Live from rc_bias (fact_forecast_accuracy).
SELECT
  dg5,
  planner_bias,
  system_bias,
  abs_error,
  error_cost,
  flag
FROM sandbox_operations.po_management.rc_bias
ORDER BY abs_error DESC
LIMIT 200;
