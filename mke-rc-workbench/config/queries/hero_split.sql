-- Live SS@LT decomposition for one SKU, anchored at its worst forward week (the low point).
-- Source: rc_snapshot_history (current vs prior plan vintage). Splits the gap into the part driven by
-- consumption vs the part that is the safety-stock TARGET refreshing on higher demand (DK-12 trap).
-- @param item_id STRING
WITH wk AS (
  SELECT
    target_week,
    pab_cur,
    ss_cur,
    (pab_cur - ss_cur)                                AS gap,
    COALESCE(delta_from_consumption, 0)               AS consumption,
    COALESCE(delta_from_target_refresh, 0)            AS target_refresh,
    COALESCE(delta_ss_gap, 0)                         AS ss_gap
  FROM sandbox_operations.po_management.rc_snapshot_history
  WHERE item_id = :item_id
)
SELECT
  target_week,
  ROUND(ss_cur, 0)          AS ss_at_lt,
  ROUND(pab_cur, 0)         AS pab,
  ROUND(gap, 0)             AS gap,
  ROUND(consumption, 0)     AS consumption,
  ROUND(target_refresh, 0)  AS target_refresh,
  ROUND(ss_gap, 0)          AS ss_gap_delta
FROM wk
ORDER BY gap ASC   -- worst (most-negative) forward week first
LIMIT 1;
