-- Rebalance lens — SKUs short in one org with in-network excess in another (transfer-before-buy). Live from rc_rebalance.
SELECT
  item_id,
  short_org,
  short_units,
  excess_org,
  excess_units,
  coverable,
  pct_covered
FROM sandbox_operations.po_management.rc_rebalance
ORDER BY coverable DESC
LIMIT 200;
