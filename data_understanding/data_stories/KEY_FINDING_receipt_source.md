# KEY FINDING — the clean PO-receipt fact exists (resolves the P1 crosswalk blocker)

**Verified live 2026-08-30 by the lead (not just a subagent).**

## What changed
Earlier profiling flagged `prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions` (the
doc-named P1 receipt source) as a **blocker**: it uses raw Oracle ids and has **no item column at all**
(reaches an item only via a 2-hop po_header_id/po_line_id → PO bridge). Tracing S1 discovered a better table.

## The better source: `prod_edw.fact.purchase_receipt_line`
Verified by `discover-schema` + queries:
- **2,715,917 rows · 69,871 distinct items · coverage 2023-08-01 → 2026-08-30 · ZERO null item_bigint_key.**
- Carries **clean EDW/business keys**: `item_bigint_key` (conformed to items_scd1 & all EDW facts),
  `purchase_order_number` (string), `purchase_order_line_number` (int).
- Carries the measures P1 needs: `shipped_quantity`, `received_quantity`, `delivered_quantity`,
  `accepted_quantity`, `rejected_quantity`, `returned_quantity`, plus `receipt_creation_date`,
  `receipt_line_creation_date`, `expected_receipt_date`.
- Joins to `purchase_orders` directly on (`purchase_order_number`, `purchase_order_line_number`) — 1:M
  (a PO line can have multiple receipt lines / partial receipts). Verified on hero item 48111850:
  PO 280023711 line 1 → received 1 on 2026-08-29 (on-time, full); PO 280023712 line 2 → received 1 on
  2026-08-28; flagship PO 480002236 (2176 units, promised 2026-10-05) not yet received.

## Why this matters
- **The raw-id crosswalk is NOT required for P1 receipts.** Use `purchase_receipt_line` (EDW keys) as the
  receipt actual instead of `receiving_receipt_transactions` (raw Oracle staging).
- `expected_receipt_date` vs `receipt_creation_date` gives **on-time** directly; `received_quantity` vs PO
  `ordered_quantity` gives **in-full** — both P1 M1 + M4 with no bridge.
- This also likely supersedes the deprecated `purchase_order_delivery` for the same purpose.

## Still to confirm (carry as open items)
1. Is `purchase_receipt_line` refreshed/maintained (not itself legacy)? Check load_date recency + owner.
   (Max receipt date is 2026-08-30, i.e. today — looks live.)
2. `accepted_quantity` was 0 on the hero receipts while `received_quantity`=1 — confirm whether acceptance
   is populated elsewhere (QC/inspection) or lags.
3. `purchase_orders` shows duplicate/SCD rows per PO line (e.g. 480002236 line 1 as 2176 AND 2560) — pick
   latest by valid_to/valid_from before computing attainment.
4. How does `purchase_receipt_line` relate to `receiving_receipt_transactions` (is it the modeled fact on
   top of the raw staging)? If so, the docs simply pointed at the raw layer instead of the fact.
5. Plan-side `purchase_orders`/`planned_orders` measures were NULL for the hero item on the snapshot —
   confirm where planned receipts live in `20_supply_daily` (grain/measure) so plan-vs-actual is complete.

Feeds SYNTHESIS §0 and the P1 open items. Supersedes the "crosswalk mandatory" framing for receipts.

---

# Other verified cross-cutting findings from the data-story walkthrough (2026-08-30)

1. **P3 item validation is a DASH-NORMALIZATION rule, not a data crisis.** For event "Oracle_Phase 2_THD",
   raw join of expansion_loads.item_number → items_scd1.item_id matched **77/1,604 (4.8%)**; stripping dashes
   (`REPLACE(item_number,'-','')`) matched **1,584/1,604 (98.7%)**. Expansion codes are dashed
   (`49-56-0507`), item master is dash-less. → P3 validate on the normalized key; re-run the PurchPlan-status
   gate on the normalized match (the "0% PurchPlan" figure was measured on wrong-key matches).

2. **P4 `frozen_*` columns are 100% NULL** in `10_demand_daily` (frozen_working_final_forecast,
   frozen_planner_baseline). The intended "since last freeze" comparison isn't populated yet → use
   **process_date day-over-day deltas** as the drift proxy until the freeze mechanism is enabled. The
   warehouse shows WHAT changed, not WHO/WHY → the reason/audit must live in **Lakebase** (action_audit_event).

3. **Prioritizing P2 by raw unit-miss over-ranks cheap components.** The #1 safety-stock "breach" (17.6M units)
   was item 88930100 (carbide cylinder, $0.0134/unit, 58-day lead, org 1019 Grenada = a PLANT) → real $ impact
   ~$235K, and un-expeditable. → P2 priority must blend unit-miss × applied_standard_cost, stratified by ABC
   and by org-role (DC vs plant). Confirms the requirement's $-impact + ABC stratification is essential.

4. **The customer↔mkedg5 map is clean 1:1** for HOME DEPOT (dg5_customer_bigint_key -1703558802731158218);
   the P3 event round-trip WORKS — event increments appear in `10_demand_daily` as expansions_runrate /
   non_repeating_events for the event month.

5. **On-hand vs the movement ledger will NOT tie out naively** — transfer orders post as both shipment and
   receipt rows across multiple subinventories, so summing `inventory_material_transaction.transaction_quantity`
   double-counts inter-org flows. Net inter-org movements before reconciling to `inventory_days_on_hand`.
