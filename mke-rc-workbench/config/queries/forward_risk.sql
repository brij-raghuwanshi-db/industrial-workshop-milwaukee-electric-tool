-- Analytics / Coming-Risk: risk wave — SKUs first-crossing per week, from rc_forward_risk.
SELECT
  crosses_week,
  COUNT(*)                                                        AS skus_crossing,
  SUM(CASE WHEN within_lead_time THEN 1 ELSE 0 END)               AS unrecoverable_skus,
  ROUND(SUM(committed_value), 0)                                  AS dollars_at_risk,
  COUNT(CASE WHEN criticality_class = 'A' THEN 1 END)             AS a_class_skus
FROM sandbox_operations.po_management.rc_forward_risk
WHERE crosses_week IS NOT NULL
GROUP BY crosses_week
ORDER BY crosses_week
LIMIT 60;
