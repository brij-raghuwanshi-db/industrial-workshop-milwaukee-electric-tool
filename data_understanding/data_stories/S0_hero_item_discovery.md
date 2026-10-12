# S0 — Hero item discovery + presence map

## How I found the candidate (the search method, step by step)
I did NOT pick an ID at random. I searched for the item with the richest, provable cross-table presence,
starting from the hardest constraint and narrowing:

1. **Started at the hardest link — receipts.** Tried to group `receiving_receipt_transactions` by item to
   find items with many recent RECEIVE events. **Finding:** the receipts table has **no item column at all**
   (`discover-schema` showed only `product_category`/`product_type`, no item id). → A receipt reaches an
   item only via `po_header_id`/`po_line_id` → PO → item. The crosswalk is a **two-hop bridge**, not a
   direct key. (Recorded; S1 handles it.)
2. **Pulled A-class `PurchPlan` items** from `items_scd1` as first candidates (recognizable M18 products).
3. **Scored 6 candidates** across `20_supply_daily` (plan), `inventory_days_on_hand` (on-hand),
   `sales_order_line_transactions` (ship), `inventory_material_transaction` (movements) for the latest
   period. **Finding:** plan + on-hand populated, but **ship = 0 and movements = 0 for every PurchPlan
   candidate** — even a top M18 seller.
4. **Tested the "conformed key" assumption.** Confirmed shipped `item_bigint_key` DOES join to `items_scd1`
   (20,299 matched in one month), so the key is conformed — the zeros were real: **`PurchPlan` items are the
   upstream "ready to purchase/plan" population and are largely NOT the items actively shipping** (those are
   `ShipSO`). This is a genuine semantic finding: the P3/P4 "Status 20" gate selects a different slice than
   the P1/P2 actuals population.
5. **Re-anchored on cross-table richness, not status.** Ranked the top 25 volume shippers (last 30d,
   Standard, shipped_qty>0) and joined presence counts across all four facts.
6. **Confirmed the receipt bridge exists** for the winner via `purchase_orders` (real POs, some OPEN, some
   CLOSED-FOR-RECEIVING with received_quantity>0).

## The hero item (chosen on evidence)
| field | value |
|---|---|
| item_bigint_key | **3879620845706693458** |
| item_id (string, crosswalk key) | **48111850** |
| description | **M18 XC5.0 BATTERY** |
| ABC | A · status | ShipSO |
| ship lines (30d) | 7,707 · ship qty 122,613 |
| on-hand orgs (20260829) | 47 |
| plan rows (snapshot 20260829) | 9,728 |
| movement rows (since 20260801) | 56,039 |
| POs | multiple; incl. OPEN (480002236, promised 20261005, 0 received) and CLOSED-FOR-RECEIVING (280023711, received 1) |

## Presence map — where the hero item lives and the key it uses in each
| Table | Key used | End-user lens |
|---|---|---|
| `items_scd1` | item_bigint_key ← origin of item identity; item_id is the string crosswalk | ✅ "what is this item" (name, ABC, PL, COO, status) |
| `20_supply_daily` | product_bigint_key (=item_bigint_key) | ✅ "what's the plan for it" (PAB, demand, supply, SS by week) |
| `inventory_days_on_hand` | item_bigint_key | ✅ "how much is on hand, where" (point-in-time) |
| `sales_order_line_transactions` | item_bigint_key | ✅ "what shipped" (actual outbound) |
| `inventory_material_transaction` | item_bigint_key | ✅/⚠️ "why on-hand moved" (27 types) — but mostly plumbing rows |
| `purchase_orders` | item_bigint_key | ✅ "what we ordered & its status/dates" |
| `receiving_receipt_transactions` | **po_header_id/po_line_id → PO → item** (NO item col) | ⚠️ receipt event; needs the 2-hop bridge to become an item answer |
| `dim_series_ext_vw` | item (item_id) / series_bigint_key | ✅ "who supplies it, lead time, cost, MOQ, planner" |
| `10_demand_daily` | product_bigint_key + dg5_customer_bigint_key | ✅ "demand forecast by customer" (only if it has demand rows — verify) |

## Key learning that shapes the build
`item_bigint_key` **is** conformed across the EDW facts/dims (safe to join). The break is ONLY at
`receiving_receipt_transactions` (raw-Oracle world, no item column) → the receipt→PO→item bridge is the one
real join risk for P1/P2. And the **status filter matters**: PurchPlan (P3/P4 gate) ≠ the actively-shipping
population (P1/P2). Anchor P1/P2 stories on shipping items; anchor P3/P4 on PurchPlan/demand items.
