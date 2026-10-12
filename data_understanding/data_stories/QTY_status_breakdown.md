# Quantity-status breakdown — "50 reached / 600 in progress / 350 still being made" + multi-supplier

**As-of 2026-08-30 · READ-ONLY · queried live.** Answer to: can we break a PO/item's quantity across stages
(received vs in-progress vs still-manufacturing), and see the same item sourced from multiple manufacturers?
**Yes to most of it** — with the honest grain caveats below.

## 1. PO-line fulfillment split — received vs open-remaining (REAL, works today)
`purchase_orders` carries `ordered_quantity`, `received_quantity` per line → the split is direct:
- **reached/received** = received_quantity
- **still open/outstanding** = ordered_quantity − received_quantity
- **% complete** = received/ordered

Real examples (partial receipts):
| PO | item | ordered | received | open remaining | % recv |
|---|---|--:|--:|--:|--:|
| 380014064 | Carbide Cylinder MS10 | 8,369,705 | 8,069,705 | **300,000** | 96% |
| 380085096 | Carbide Cylinder MS10 | 4,000,000 | 3,992,610 | 7,390 | 100%* |

→ So "of 1000 ordered, 650 received, 350 open" **is directly answerable per PO line.**

## 2. Split-delivery schedule — multiple scheduled receipts per line (REAL)
`purchase_order_schedule` has `purchase_order_schedule_number` + its own `ordered_quantity`,
`received_quantity`, `promised_delivery_date_key`, `promised_ship_date_key`,
`original_promised_delivery_date_key`, `last_acceptable_delivery_date_key`, `purchase_order_schedule_status`
per line. → One PO line can split into **several scheduled deliveries**, each with its own promised date and
received qty. That gives the finer "50 arriving this week, 600 next week, 350 later" *by schedule*.

## 3. Stage mix for the item (REAL — from the plan, per STATE_pointintime_stage.md)
`20_supply_daily` measures ARE the stage buckets as-of a snapshot:
- **reached / at rest** = on_hand · **in transit** = in_transit · **scheduled to receive** = scheduled_receipts
  · **being made (WIP)** = work_orders · **on order** = purchase_orders · total = total_supply.
So the "50 reached / 600 in progress / 350 under manufacturing" shape maps to:
received_quantity (reached) + in_transit/scheduled_receipts (in progress) + work_orders (being made). Real
hero-item snapshot: 169,515 on_hand / 721 in_transit / 2,297 scheduled.

## 4. Same item from MULTIPLE manufacturers/suppliers (REAL)
`dim_series_ext_vw` is grained at **item × org × supplier**, so one item legitimately has many supplier rows:
| item | # suppliers | # sites | example suppliers |
|---|--:|--:|---|
| 49960060 | **6** | 5 | 1019 Grenada, Milwaukee Electric Tool Corp, 2012 Olive Branch … |
| 06653720 | 5 | 3 | **B S B Products Corp**, 2092 3PL Parts & Service, 2012 Olive Branch |
| 28506360X | 5 | 3 | **SUS Cast Products Inc**, Milwaukee Electric Tool Corp, 2092 3PL … |
| 06974000 | 5 | 3 | **Fastenal Company**, 2092 3PL Parts & Service, 2012 Olive Branch |

→ **Multi-source is real** — an item comes from external vendors (Fastenal, SUS Cast, B S B) AND internal
orgs/plants. `allocation_percent` exists to split volume across sources (many items are 100% single-source;
multi-source ones can carry the %). So "same item arriving to a vendor/DC from multiple manufacturers" is
representable, and you can attribute each PO/receipt to its supplier.

## 5. The combination you asked for (all together)
For an item you can assemble, as-of a date:
- **By supplier:** which manufacturer each open PO / receipt belongs to (PO → supplier via dim_series_ext_vw / purchase_orders supplier keys).
- **By stage:** how many units reached (received_quantity) vs in transit (in_transit) vs scheduled (scheduled_receipts) vs still being made (work_orders / WIP issues at plant).
- **By schedule:** split-delivery lines with per-tranche promised dates.
- **By node:** where the reached units sit (inventory_days_on_hand by org).
→ e.g. "Item X: 1,000 on order across 2 suppliers (Fastenal 60% / SUS Cast 40%); 650 received (Fastenal
tranche fully in, SUS Cast 250 open), 350 still open with a promised date of <d>; received units sit 80% at
Olive Branch, 20% at Byhalia."

## Honest limits (same grain caveats as HOP / STATE)
- **Quantities, not units:** received/open/WIP are counts at item×PO×node×day — NOT serial/lot, so you can't
  say "these specific 50 units." No serial_number/lot columns.
- **"Under manufacturing" is WIP quantity, not a per-unit line-position:** work_orders / WIP-issue movements
  give how much is in production, not a build-status per unit. And for the finished-good hero item work_orders
  was null (make happens on components at the plant, e.g. the carbide cylinders).
- **Multi-supplier allocation_percent is often 100%** (single-source) — the split field exists but isn't always
  populated with a true split; verify per item.
- **PO SCD2 duplicates:** purchase_orders can show the same line as multiple versions — dedupe on latest
  valid_to before summing received/ordered (else the split is double-counted).
- **Received-vs-schedule reconciliation:** header received_quantity vs sum of schedule received_quantity vs
  purchase_receipt_line receipts should tie — but confirm, given the SCD2/duplicate quirk.

## One-paragraph answer
Yes — the **ordered → received → open-remaining** split is directly in `purchase_orders` (per line) and finer
in `purchase_order_schedule` (per scheduled delivery with its own promised dates), and the **reached / in-
transit / scheduled / being-made** stage mix comes from `20_supply_daily` measures + WIP movements — so
"50 reached, 600 in progress, 350 still being manufactured" is reconstructable as quantities as-of a date.
**Multi-supplier is real too**: `dim_series_ext_vw` grains at item×org×supplier (an item like 49960060 has 6
suppliers incl. external vendors + internal plants), with `allocation_percent` to split sourcing — so the
same item arriving from multiple manufacturers, and each PO/receipt attributed to its source, is
representable. The ceiling is the same everywhere: it's **quantity buckets by supplier/stage/schedule/node,
not serial-level unit tracking**, and you must dedupe PO SCD2 versions and verify allocation_percent per item.
