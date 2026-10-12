# Point-in-time "where / what stage" — the temporal state layer (also = lineage over time)

**As-of 2026-08-30 · READ-ONLY · queried live.** Answer to "can we show where the product is at a particular
time / in what stage?" Yes — as a **stage MIX and node MIX as-of a date**, not a GPS dot on one unit.

## Two point-in-time views, both real (hero item M18 XC5.0 BATTERY, snapshot 20260829, week 20260824)

### A. WHAT STAGE — the supply-state mix (from `20_supply_daily` measures)
Each plan measure IS a stage bucket, so summing them per snapshot tells you how many units are in which stage:

| Stage | Measure | Units (real) |
|---|---|--:|
| At rest (on hand) | on_hand | **169,515** |
| In transit (moving) | in_transit | 721 |
| Scheduled to receive | scheduled_receipts | 2,297 |
| Being made (WIP) | work_orders | (null for this FG item) |
| On order (PO) | purchase_orders | (null this week) |
| **Total supply** | total_supply | 170,668 |

→ "As of 2026-08-29, ~169.5K units are at-rest, 721 in transit, 2,297 inbound scheduled." That's the
**stage breakdown at a point in time.**

### B. WHERE — the node/location mix (from `inventory_days_on_hand`, point-in-time)
| org | name | on-hand |
|---|---|--:|
| 2012 | Olive Branch (US DC) | 83,254 |
| 2013 | OB – Home Depot | 63,273 |
| 1080 | Byhalia, MS | 9,168 |
| 2093 | 3PL Canada Geodis | 7,019 |
| 2120 | Mexico | 2,077 |
| 9043 | Indy Service Hub | 1,950 |

→ "As of 2026-08-29, the item sits mostly at Olive Branch + its Home Depot DC, some in Canada/Mexico/Service."

## Why this IS lineage (the temporal dimension the user spotted)
- **Static lineage** (L_lineage) = the table/edge map: which source feeds which measure, join keys.
- **Temporal state** (this file) = **the same lineage evaluated AT a moment** — where the quantity sits and in
  what stage, and (because 20_supply_daily has 366 daily snapshots) how that state MOVED over time.
- Combine with the hop-chain (HOP_product_journey): hops = the *edges* (node→node moves), state = the *node
  occupancy* at each instant. Together they are a time-lapse of the product's position through the network.

## What we CAN show
- **Stage mix as-of any snapshot date** (on-hand / in-transit / WIP / on-order / scheduled) — per item, per org, or network-wide.
- **Node occupancy as-of any date** — how much sits at each DC/plant/3PL/service hub.
- **State-over-time / time-lapse** — replay stage & node mix across the daily snapshots (e.g. the S2 story:
  108K→70K→83K at Olive Branch across a week; in-transit rising before a receipt lands).
- **"Rolled toward" a stage** — e.g. units moving from in_transit → on_hand week over week.
- **As-of ("time travel") reconstruction** — pick any process_date and see the world as the plan saw it then
  (this is what powers "was green last week, now red").

## What we CANNOT show (honest limits — same as HOP)
- **Not a single unit's location** — grain is item × node × day (quantities), no serial/lot, so "where is unit
  #12345 right now" is impossible.
- **Not real-time** — snapshots are daily (early-morning, prior-day EOD state); intraday position isn't captured.
- **In-transit is a count, not a track** — you see "721 units in transit" but not which leg/lane/ETA per unit
  (carrier/tracking exists only on the OUTBOUND customer shipment leg, per HOP).
- **DC→DC leg open** — interorg receipt lands in a separate system, so mid-transfer "between DC-A and DC-B"
  is inferred from the shipment side, not confirmed by a matched receipt.

## One-paragraph answer
Yes — we can show **where a product is and in what stage at a given time**, as a *quantity distribution*:
the plan's stage measures (on_hand / in_transit / scheduled_receipts / work_orders / purchase_orders) give the
**stage mix as-of a snapshot**, and `inventory_days_on_hand` gives the **node/location mix as-of a date**;
because there are 366 daily snapshots we can replay this as a **time-lapse** of the product moving through
stages and nodes — which is exactly the *temporal* half of lineage. The limit is grain: it's aggregate
quantities per item × node × day, so we can say "169K at rest, 721 in transit, 83K at Olive Branch on Aug 29"
and how that shifts over time, but not track one physical serial-numbered unit or an intraday/real-time position.
