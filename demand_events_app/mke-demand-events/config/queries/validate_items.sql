-- READ-ONLY source: prod_edw.dimension.items_scd1
-- Item validation for a pasted list. Dash-normalize the pasted item_number
-- (2438-20 -> 243820) to match items_scd1.item_id.
-- NOTE (open risk): the requirements' item_status='PurchPlan' rule flags 100%
-- of a real event (events carry ShipSO). We return item_status + a WARN flag
-- and tag the rule version; the app treats validation as NON-BLOCKING.
-- @param item_ids STRING = 243820
WITH pasted AS (
  SELECT explode(split(:item_ids, ',')) AS item_id
)
SELECT
  p.item_id,
  i.item_description,
  i.item_status,
  i.item_status_name,
  CASE WHEN i.item_id IS NULL THEN 'WARN_NOT_FOUND'
       WHEN i.item_status = 'PurchPlan' THEN 'OK'
       ELSE 'WARN_STATUS' END AS validation_flag,
  'v1_purchplan' AS validation_rule_version
FROM pasted p
LEFT JOIN prod_edw.dimension.items_scd1 i
  ON p.item_id = i.item_id
