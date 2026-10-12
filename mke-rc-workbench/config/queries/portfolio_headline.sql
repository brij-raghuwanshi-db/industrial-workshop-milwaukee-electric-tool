-- Portfolio headline numbers — all LIVE, replacing the seeded PORTFOLIO constants.
-- Excess $ from rc_excess; unrecoverable $ + counts from the spine; rebalance/nervous/chronic from serving tables.
SELECT
  (SELECT ROUND(SUM(dollars), 0) FROM sandbox_operations.po_management.rc_excess)                                    AS excess_dollars,
  (SELECT COUNT(*) FROM sandbox_operations.po_management.rc_excess)                                                  AS excess_skus,
  (SELECT COUNT(*) FROM sandbox_operations.po_management.rc_rebalance)                                               AS rebalance_rows,
  (SELECT ROUND(SUM(committed_value), 0) FROM sandbox_operations.po_management.rc_serving_sku_week
     WHERE recoverability_class = 'UNRECOVERABLE')                                                                   AS unrecoverable_dollars,
  (SELECT COUNT(DISTINCT item_id) FROM sandbox_operations.po_management.rc_serving_sku_week
     WHERE recoverability_class = 'UNRECOVERABLE')                                                                   AS unrecoverable_skus,
  (SELECT COUNT(DISTINCT item_id) FROM sandbox_operations.po_management.rc_serving_sku_week
     WHERE temporal_class = 'nervous')                                                                               AS nervous_skus,
  (SELECT COUNT(DISTINCT item_id) FROM sandbox_operations.po_management.rc_serving_sku_week
     WHERE temporal_class = 'chronic')                                                                               AS chronic_skus,
  (SELECT COUNT(DISTINCT item_id) FROM sandbox_operations.po_management.rc_serving_sku_week
     WHERE action_verdict = 'DISMISS')                                                                               AS dismiss_skus;
