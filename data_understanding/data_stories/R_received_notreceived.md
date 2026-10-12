# R — Received / Not-Received scenarios + unhappy Plan-vs-Actual

**As-of 2026-08-30 · READ-ONLY · profile mke-rsc.** Every number below is from a live query. This closes the
"did it arrive or not" and "actual missed plan" polarity that the happy-path stories didn't cover.

## R1 — The PO fulfillment-state matrix (the full received/not-received spectrum)
Every PO line lands in exactly one state. Real distribution (POs promised on/after 2026-01-01):

```sql
-- READ-ONLY
SELECT CASE
  WHEN received_quantity=0 AND order_status='OPEN' AND promised_delivery_date_key < 20260829 THEN '1 PAST-DUE not received'
  WHEN received_quantity=0 AND order_status='OPEN' THEN '2 OPEN not yet received'
  WHEN received_quantity>0 AND received_quantity<ordered_quantity THEN '3 PARTIALLY received'
  WHEN received_quantity=ordered_quantity THEN '4 FULLY received (exact)'
  WHEN received_quantity>ordered_quantity THEN '5 OVER received'
  ELSE '6 other' END AS state,
  COUNT(*) po_lines, SUM(ordered_quantity) ordered, SUM(received_quantity) received
FROM prod_edw.fact.purchase_orders
WHERE ordered_quantity>0 AND promised_delivery_date_key>=20260101 GROUP BY 1 ORDER BY 1
```

| State | PO lines | Ordered qty | Received qty | Polarity |
|---|--:|--:|--:|---|
| 1 **PAST-DUE not received** | **355,999** | 1.378B | 0 | 🔴 red — promised date passed, nothing in (exception #12) |
| 2 OPEN not yet received | 203,610 | 1.115B | 0 | 🟡 in-flight — not due yet (fine) |
| 3 **PARTIALLY received** | 27,683 | 382M | 244M | 🟠 amber — short so far; watch |
| 4 **FULLY received (exact)** | **1,232,501** | 7.64B | 7.64B | 🟢 green — the healthy majority |
| 5 **OVER received** | 11,957 | 642M | 665M | 🟠 amber — received > ordered (+23M units; over-ship / data issue) |
| 6 other | 55,392 | 329M | 0 | ⚠️ needs status rules (closed w/ 0, cancelled…) |

**Reading it:** the healthy state (fully received) dominates at **1.23M lines** — good. But **356K PO lines are
past-due with zero receipts** — that is the P2 "PO past due" queue, and it's large. **Over-received (+23M
units)** is its own quiet red flag (pay-for-more, cycle-count noise). ✅ this single matrix is the receiving
health KPI a planner would open Monday morning.

> Note the grain caveat: `purchase_orders` is SCD2, so a PO line can appear as multiple rows — treat these as
> line-versions, not distinct POs. Numbers are directional health, not an exact PO count.

## R2 — Concrete PAST-DUE (was expected, didn't arrive) — real A/B items
```sql
-- READ-ONLY: OPEN, received 0, promised in the past, A/B items, by overdue size
```
| PO | item_id | description | ABC | ordered | received | promised | days overdue |
|---|---|---|---|--:|--:|---|--:|
| 380069729 | 49940003 | 4.5" METAL CUT WHEEL (25pk) | A | 453,600 | 0 | 2026-07-06 | **54** |
| 380079204 | 367520 | M18 FUEL REBAR CUTTER | B | 480,396 | 0 | 2026-07-27 | 33 |
| 380085029 | 48223100P | (36) INKZALL BLACK MARKER | A | 869,760 | 0 | 2026-08-19 | 10 |

**Story:** *"PO 380069729 for 453,600 metal-cut wheels (A-item) was promised July 6 — 54 days overdue, still
zero received. The plan assumed this supply; every downstream week that counted on it is now optimistic."*
🔴 This is exactly the plan-vs-actual gap source, and a P2 escalate candidate. ✅ answers "what did I expect
that never came, and how late is it?"

## R3 — Unhappy Plan-vs-Actual (the not-happy stories)
The happy stories (G1–G4) showed on-time/in-full/stable. The unhappy cuts, all evidenced elsewhere and
summarized here:
- **On-hand missed plan** (S2): Olive Branch M18 battery — plan projected 60,121 for the week; actual path
  crashed to 70,166 on 8/27 (−32K in a day) before a late transfer recovered it. Plan never saw the spike.
- **Plan ↔ actual DISCONNECT** (P-pattern #1): 25+ items where the latest plan's PAB and today's actual
  on_hand differ by >10M units — some 100% disconnected (plan exists, actual NULL). Plan not tied to reality.
- **Phantom demand** (P-pattern #2): 8.4M units of standing forecast on product-customer pairs with **zero
  shipments** Aug–Sep — plan-vs-actual will always "miss" because the demand isn't real.
- **Past-due supply** (R2): planned receipts that are 10–54 days late and counting.
- **Forecast drift** (S9): +184K-unit (+23,016%) baseline revision — the plan itself moved, so last week's
  plan-vs-actual baseline is already stale.

**The synthesis point:** "actual vs planned" is not one number — it's **four different misses** (demand didn't
happen / supply didn't arrive / plan was disconnected / plan itself changed), and the root-cause category
(from `inventory_material_transaction` + the PO state matrix) is what tells them apart. That mapping is the
core of P1 metric 2.3.7 and the P2 queue.

## Received/Not-received → workflow (ties to T_status_transitions_workflow.md)
| State | Green/Red | Planner action | Lakebase state |
|---|---|---|---|
| Fully received on-time | 🟢 | none | (no case) |
| Partially received | 🟠 | monitor / chase balance | exception_case open→monitor |
| Past-due not received | 🔴 | expedite / escalate (evidence only; no PO write here) | exception_case open→assigned→resolved |
| Over received | 🟠 | investigate (over-ship / count) | exception_case open→disposition |
| Not yet due | 🟡 | none | (no case) |
