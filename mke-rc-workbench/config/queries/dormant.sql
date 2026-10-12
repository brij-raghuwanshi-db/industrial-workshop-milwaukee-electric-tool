-- Dormant / E&O lens — items with no recent shipments. Live from rc_dormant.
-- managed_hold=Yes → intentional reserve, not E&O (DK-17). Managed items first (actionable review).
SELECT
  item_id,
  abc,
  last_ship_week,
  status,
  managed_hold,
  verdict
FROM sandbox_operations.po_management.rc_dormant
ORDER BY (verdict = 'review E&O') DESC, abc
LIMIT 200;
