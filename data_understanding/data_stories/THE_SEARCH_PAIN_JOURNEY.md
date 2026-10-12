# The Search Pain Journey — why "the data is there" is not the same as "you can use it"

*A first-person account of what it actually took to extract meaning from Milwaukee's mature EDW and
operations layers — written so the pain is visible, because it is invisible in every finished dashboard.*

---

## The premise everyone believes (and why it's a trap)

"The data is in the EDW. It's modeled, it's governed, it's daily-refreshed, it's got conformed dimensions and
SCD tables and a medallion architecture. So the hard part is done — now you just query it."

That belief is the trap. The EDW *is* mature. `prod_edw` has 13.4-billion-row fact tables, 366 daily
snapshots, clean surrogate keys, a real date dimension going out to the year 9999. And **it still took me
dozens of queries, five parallel profiling agents, and a running list of "gotchas" just to answer basic
questions** like "did this PO arrive?" or "is this item valid?" A human planner, doing this by hand, every
Monday morning, for hundreds of SKUs — that is not easier. It is the same pain, multiplied by people and
repeated forever.

This is the story of that pain.

---

## Chapter 1 — You can't even name the thing you want

I started where anyone starts: the requirements doc named the tables. `receiving_receipt_transactions` for PO
receipts. `items_scd1` for item validation. Simple.

Except the first table I reached for — the receipts — **had no item column at all.** Not a renamed one. None.
I ran `discover-schema` and stared at 134 columns of `product_category`, `product_fisc_class_id`,
`product_type` — and no `item_id`. A receipt in this table only knows a *PO number*. To learn *what was
received* you have to hop receipt → PO → item, through a table the requirements never mentioned.

And the table the requirements *did* name for validation — "item_status must be Status 20" — has no "20"
anywhere. The value is the string `'PurchPlan'`. The column the doc told me to filter on
(`item_status_description`) is **truncated in the actual data** ("Ready to Purchase or Plan Productio" — the
"n" is gone). If I'd trusted the doc, my filter would have quietly matched nothing and I'd never have known.

> **The pain:** the names in the documentation, written by smart people who know the business, did not match
> the bytes on disk. Every single "confirmed source" had to be re-verified against reality. A name in a doc is
> a rumor until you query it.

## Chapter 2 — The data lies to you politely (semi-additivity)

I found the on-hand table. 2.7 billion rows, beautifully clean, zero negative quantities. I wanted "how much
of this battery do we have across the week," so I did the obvious thing: `SUM(on_hand_qty)` across the week's
dates.

**538,116 units.** The real answer was **83,254.**

On-hand is a *point-in-time* measure. Summing it across six days counts the same batteries six times. The
query ran without error. The number looked plausible. It was wrong by 6.5×. Nothing in the data warned me —
no constraint, no flag, no comment. You only avoid this if you *already know* the measure is semi-additive.
That knowledge lives in someone's head, not in the schema.

> **The pain:** the warehouse will happily hand you a confident, precise, completely meaningless number. The
> guardrail is tribal knowledge, and tribal knowledge doesn't scale to hundreds of users.

## Chapter 3 — The grain fights back

I wanted to compare planned receipts for one battery in one week. One product, one org, one week, one plan.
That should be one row. It was **up to 3,989 rows** — the plan fact silently splits by `series_bigint_key` and
`order_type_bigint_key`, dimensions nobody told me about. 41 million rows per snapshot where I expected ~27
million distinct keys. Any naive `JOIN` or `SUM` fans out or double-counts, and again — no error, just a
wrong number wearing a suit.

Then the movement ledger, when I tried to reconcile why on-hand changed: transfer orders post as **both** a
shipment row **and** a receipt row, across multiple sub-inventories, so summing "transaction_quantity" to get
net flow double-counts the transfers. My reconciliation didn't tie out and the *reason it didn't tie out* was
itself a piece of buried knowledge.

> **The pain:** the true grain of a table is not what the business thinks it is, and discovering it costs a
> query, a wrong answer, and a moment of "wait, why is this number too big?"

## Chapter 4 — The keys don't speak the same language

To connect what we *received* to what we *planned*, I needed the receipt's item and org to match the plan's.
But the receipts table speaks **raw Oracle** (`organization_id` = 300000016168122, a 15-digit Oracle id),
while every EDW fact and dimension speaks **surrogate bigint keys** (`item_bigint_key` = 3879620845706693458).
They do not join. A crosswalk is required — and it isn't documented, and for the receipts it's a *two-hop*
bridge through the PO.

Meanwhile, on the demand side, the event file lists items as `49-56-0507` (dashed) and the item master stores
them as `4956050 7`→dashless. A raw join matched **4.8%** of items and screamed "95% of your data is broken!"
The truth, after I thought to strip the dashes: **98.7% match.** The crisis was a punctuation mismatch.

> **The pain:** the same real-world thing (an item, an org) wears three different costumes in three tables,
> and reconciling them is detective work you must redo for every new question.

## Chapter 5 — The most important columns are empty

For demand exceptions, the *designed* mechanism is `frozen_working_final_forecast` — "what did we forecast at
the last freeze, vs now." I wrote the query. Zero rows. The column is **100% NULL** across 17.8 billion rows.
The feature exists in the schema and not in the data. So "what changed since last plan" — the entire point —
has to be reconstructed from day-over-day snapshot deltas instead, which I only figured out after the obvious
path returned nothing.

And the SKU-supersession mapping that transition exceptions (#9–11) need? Not there at all. Three of the
eighteen exception types are simply undetectable because the linking data doesn't exist.

> **The pain:** you can't tell "this is empty because nothing happened" from "this is empty because the
> pipeline never filled it" without going and asking a human. The data's silence is ambiguous.

## Chapter 6 — A single number means five different things

I found the "biggest safety-stock breach": 17.6 million units short. Alarm bells. Then I enriched it — and it
was a **carbide cylinder worth $0.0134 a unit, at a manufacturing plant, with a 58-day lead time.** Real
dollar impact ~$235K, and un-fixable by expediting anyway. The "top crisis," ranked by the obvious metric
(unit miss), was a rounding error wearing a costume.

The same PAB-below-safety-stock signal means "expedite from supplier" at a DC, "cut production" at a plant,
"field-service risk" at a service hub — three different actions, three different owners. **69% of items have
no named planner**, so even "who do I send this to" is a lookup. One number, five meanings, and the data
doesn't tell you which one you're looking at.

> **The pain:** raw magnitude is not importance. Turning a number into a *decision* requires joining cost,
> ABC class, org role, lead time, and ownership — five more tables — before it means anything.

## Chapter 7 — The truth is only visible if you look at time

The single most useful finding — "this week was on track, now it's not" — is *invisible in any single
snapshot.* I only saw the Oct-5 week flip from a healthy PAB of 151,929 to a breach of −3,464 because I lined
up the *same future week* across five monthly snapshots. Every standard dashboard shows one snapshot. The
deterioration, the plan nervousness, the supplier that *just* started slipping, the past-due cluster forming
*this* month — all of it lives in the comparison *between* snapshots, which nobody does by default because
it's expensive and awkward and you have to know to do it.

> **The pain:** the data holds the movie, but every tool shows you a frame. The meaning is in the motion, and
> the motion is work to extract.

---

## What it actually cost — the receipts of the pain

To answer a *foundational understanding* pass (not even build anything), it took:
- **~20 profiling/tracing agents**, each running 15–50 queries → **several hundred queries.**
- A **running "gotchas" register** that grew to ~15 distinct traps, each of which silently produces a
  wrong-but-plausible answer if you don't know it.
- **~36 findings documents** to hold the knowledge, because it did not fit in anyone's head.
- Repeated cycles of: reach for the documented table → find it's wrong/empty/mis-keyed → discover the real
  one → re-verify → record the gotcha → move on.

And I had advantages a human planner does not: I can run 20 things in parallel, I never get bored on query
#300, I remember every gotcha perfectly, and I don't have a Monday-morning deadline while my inbox fills up.

## Now multiply it

A demand planner does a version of this **every week**, by hand, in spreadsheets, for hundreds of SKUs, under
time pressure, without the ability to fan out 20 parallel investigations. They pull from multiple systems,
reconcile by eye, and re-derive the same gotchas the same way every time — or worse, *don't* know the gotchas
and ship the 6.5×-inflated number. Every planner re-learns "don't sum on-hand," re-discovers the dash
problem, re-finds the right receipt table, re-builds the cost-weighted ranking, re-does the snapshot
comparison. The knowledge doesn't compound; it's re-paid, per person, per week, forever.

**That is the search pain.** It is not a data-*availability* problem — Milwaukee solved that; the EDW is
genuinely mature and well-built. It is a data-*meaning* problem: the distance between "the correct data exists
in a governed table" and "a human extracted the right, trustworthy answer and knew what to do about it." That
distance is paved with wrong table names, semi-additive traps, hidden grain, mismatched keys, empty columns,
magnitude illusions, and time-blindness — and today, each user walks that distance alone, every time.

## The one-line version
> The hard part was never storing the data. Milwaukee already won that. The hard part is that **every
> question re-pays the full cost of understanding** — and that cost, paid by many users on a daily loop, is
> the real pain. The data being *there* is table stakes. The data being *usable, trustworthy, and decision-
> ready without tribal knowledge* is the actual unmet need.
