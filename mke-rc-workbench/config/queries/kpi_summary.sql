-- Cockpit KPI header: flagged / ACT / unrecoverable$ / chronic — one aggregated row (small payload).
SELECT
  COUNT(DISTINCT item_id)                                                                       AS flagged_skus,
  COUNT(DISTINCT CASE WHEN action_verdict='ACT'   THEN item_id END)                             AS act_skus,
  COUNT(DISTINCT CASE WHEN action_verdict='WATCH' THEN item_id END)                             AS watch_skus,
  COUNT(DISTINCT CASE WHEN action_verdict='DISMISS' THEN item_id END)                           AS dismiss_skus,
  COUNT(DISTINCT CASE WHEN temporal_class='chronic' THEN item_id END)                           AS chronic_skus,
  COUNT(DISTINCT CASE WHEN recoverability_class='UNRECOVERABLE' THEN item_id END)               AS unrecoverable_skus,
  MAX(snapshot_date)                                                                            AS snapshot_date
FROM sandbox_operations.po_management.rc_serving_sku_week
WHERE severity_class <> 'healthy';
