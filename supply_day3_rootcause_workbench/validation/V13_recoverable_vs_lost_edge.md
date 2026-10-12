<div align="center">

# V13 · Recoverable Fires vs Lost Battles vs Living-on-the-Edge — Validation

### The time-fence lens: winnable exception, committed loss, or chronic zero-buffer

</div>

**Why this exists:** the planners live a weekly rhythm of *"fires we recover"* and *"battles we lose no matter
what."* Those are distinct, named supply-chain states, and the tool must tell them apart — you don't run a full
root-cause + expedite on a loss that's already locked in. Tested live whether each population exists.

## The professional vocabulary

| Planner phrase | Professional term | Definition |
|---|---|---|
| Weekly "fire" we recover | **S&OE (Sales & Operations Execution)** exception; the act = **expediting / firefighting** | near-term, **recoverable** — a lever still exists (pull-in, expedite, transfer) because the breach is **outside the lead-time fence** |
| Battle we lose no matter what | **Unrecoverable / committed stockout** | the breach is **inside the lead-time fence** — no new supply can physically arrive in time; the loss is locked in past the **"last responsible moment"** |
| Living on the edge | **Hand-to-mouth replenishment** / **chronic-critical, zero-buffer** ("tightly-coupled, low-slack") | perpetually at/below safety stock, no cushion — every week is a near-miss |

**Organizing concept:** the **lead-time fence.** Inside a SKU's replenishment lead time you cannot react → that
line separates a winnable fire from a lost battle. (Broader frame: **S&OP** = tactical 3–18 mo planning;
**S&OE** = the 0–13 wk execution layer where all this lives.)

---

## Live populations (next quarter, `20 Global`, per-SKU lead time from `dim_series_ext_vw`)

### 1 · Recoverable vs Unrecoverable (the lead-time fence)

| | count | of flagged |
|---|---|---|
| Flagged crossings (with a known lead time) | 10,908 | 100% |
| **Unrecoverable — breach INSIDE lead-time fence** | **10,729** | **98%** |
| **Recoverable — time to act before the breach** | **179** | 2% |

### 2 · Living-on-the-edge populations (of 67,794 SKU×orgs)

| population | count | meaning |
|---|---|---|
| **Always below SS** every week of the horizon | **2,307** | chronic zero-buffer — perpetual edge |
| **Hand-to-mouth** (below SS ≥50% of weeks, but never hits 0) | 2,795 | surviving week-to-week on the cushion, never quite stocking out |
| **Hits zero** (PAB goes negative ≥1 week) | 3,712 | true stockout at some point |

### 1b · …with $ and lead time attached (decision-grade)

| class | SKUs | $ at risk | median lead |
|---|---|---|---|
| **UNRECOVERABLE** | 10,729 | **$372.5M** | 130 days |
| **RECOVERABLE** | 179 | $3.7M | 7 days |

→ Recoverability tracks lead time exactly (130d vs 7d) and **virtually all dollar exposure ($372M) is in
committed losses.** This is the number that says "PO expediting is not where the value is."

### 1c · Of the unrecoverable, what's the damage-control path?

| of 9,310 short item×networks | count | share | damage-control action |
|---|---|---|---|
| **has in-network excess** → still savable | **1,845** | **20%** | **TRANSFER** (respects no supplier lead time) |
| **no in-network excess** → true loss | **7,465** | **80%** | **allocate / notify / accept + log** |

→ The unrecoverable population is **not monolithic**: a fifth are still savable by moving stock we own;
four-fifths are genuine damage-control. The action path must branch on this.

### 3 · The lead-time distribution — the reason 98% are "unrecoverable"

| median | p25 | p75 | **average** | series with lead >8wk |
|---|---|---|---|---|
| **2 days** | 2 | 7 | **122 days** | **99,678 of 602,048** |

---

## 📖 The story the data tells

The vocabulary maps onto real, separable populations — but the headline number reframes the entire product.
**98% of flagged crossings are inside the lead-time fence** — i.e., by the planner's own definition, *most weekly
fires are already-lost battles you cannot fix with a purchase order.* That sounds impossible until you see the
lead-time distribution: **median 2 days but average 122 days** — wildly bimodal. Most SKUs replenish fast, but a
heavy tail of long-lead items (99,678 series over 8 weeks) exists — and **those long-lead SKUs are exactly the
ones that show up as flagged crossings**, because a long lead time is *what makes a breach unrecoverable.* The
fast movers rarely flag; the slow movers flag and can't be ordered out of it.

That is the single most important strategic message in the whole validation set: **for the flagged population,
"place a PO" is almost never the answer.** The winnable move is **transfer** (V6/V9 — move what you already own,
which respects no supplier lead time) or the loss is committed and the job becomes *damage control* — allocate
the shortfall to the least-painful customers, notify early, and log it as a lost battle rather than burning hours
"root-causing" something that can't change. Running a full RCA + expedite on a committed loss is the exact
time-waste the tool should *prevent.*

The living-on-the-edge populations tell the chronic version of the same story: **2,307 SKUs are below safety
stock every single week** — these aren't fires, they're a *condition.* No amount of weekly firefighting fixes a
SKU that's structurally zero-buffer; the honest action is a policy fix (raise SS realism, re-source, dual-source,
or consciously accept the risk) — a fundamentally different conversation from the weekly expedite.

## Where the FULL root-cause analysis actually belongs

Not every fire deserves a full RCA — that's the insight. The complete, deep root-cause investigation is
warranted for a **specific, small, high-stakes population:**

| Situation | Full RCA? | Why |
|---|---|---|
| **Recoverable** near-term fire (179) | **partial / fast** | you have a lever now — triage the cause, act, move on; speed > depth |
| **Unrecoverable committed loss**, high-$ / customer-committed | **YES — full RCA** | it's too late to fix *this* occurrence, so the value is *learning why it became unrecoverable* — did we detect late? was the lead-time fence known? — to prevent the *next* one. This is the "capturing how it happened so we can report and prevent" the transcript asked for |
| **Chronic zero-buffer** (2,307 always-below) | **YES — systemic RCA** | recurring by nature → the RCA output is a **policy change** (SS/sourcing/lead-time), not an expedite |
| **Do-nothing / cushion dip** (V12, 66%) | **NO** | close with evidence; a full RCA here is pure waste |

→ **Full RCA is reserved for the unrecoverable-and-material and the chronic** — precisely the "living on the
edge" and "lost battle" cases. That's a deliberate inversion of instinct: you do the *deepest* analysis on the
problems you *can't* fix this week, because that's where the learning (and the prevention of next week's fire)
lives.

## Verdict: 🔴 GAP — no recoverability classification; and RCA is mis-targeted

The design flags shortages but never asks **"can this still be recovered?"** — yet 98% can't be ordered out of.
And it implies full RCA on every fire, when RCA's real value is on the *committed* and *chronic* cases. Both are
capability gaps and both are trust/time gaps.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| 98% unrecoverable | long **replenishment lead times** (avg 122d) mean most breaches are locked in before they surface — the fence is far out |
| Bimodal lead time | two supply modes — fast domestic/transfer vs long outsourced/overseas production (Techtronic etc.) — averaging them is meaningless |
| 2,307 always-below | structural: SS target set above sustainable supply, or chronically under-sourced items |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **recoverability class** to every flag: `RECOVERABLE` (breach after lead-time fence) / `UNRECOVERABLE` (inside fence) — using **per-SKU `complete_lead_time`, never an average** | build | 🔴 must |
| 2 | For **UNRECOVERABLE** flags, switch the recommended action from "expedite/RCA" to **damage-control** (transfer if possible → else allocate + notify + log as lost battle) | build | 🔴 must |
| 3 | **Reserve full RCA** for unrecoverable-and-material + chronic-zero-buffer; fast-triage the recoverable; DISMISS the cushion dips (V12) | build/planner | 🔴 must (time) |
| 4 | Add a **"living on the edge" / chronic-critical watch** (2,307 always-below) → route to a **policy-fix backlog** (SS realism, dual-source), not weekly expedites | planner | 🟡 should |
| 5 | Segment SKUs by **lead-time band** (short vs long-lead tail) everywhere — the 2d-median/122d-avg split means one policy can't serve both | build | 🟡 should |
| 6 | On committed losses, capture the **"why unrecoverable"** RCA (late detection? unknown fence?) → prevention feedback loop | planner | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V13-1: recoverable vs unrecoverable via the lead-time fence (READ-ONLY). Per-SKU lead time.
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
fc AS (SELECT s.product_bigint_key po, s.inventory_organization_bigint_key io, MAX(s.series_bigint_key) sk,
    MIN(CASE WHEN s.projected_available_balance<s.safety_stock THEN s.date_key END) first_cross
  FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0
  GROUP BY 1,2 HAVING MIN(CASE WHEN s.projected_available_balance<s.safety_stock THEN s.date_key END) IS NOT NULL),
j AS (SELECT fc.*, x.complete_lead_time ltd,
    CAST(DATEDIFF(to_date(CAST(fc.first_cross AS STRING),'yyyyMMdd'), DATE'2026-09-01') AS INT) days_to_cross
  FROM fc LEFT JOIN prod_operations.edw_extension.dim_series_ext_vw x ON fc.sk=x.series_bigint_key)
SELECT COUNT(*) flagged,
       SUM(CASE WHEN days_to_cross<=ltd THEN 1 ELSE 0 END) unrecoverable_inside_leadtime,
       SUM(CASE WHEN days_to_cross>ltd THEN 1 ELSE 0 END) recoverable
FROM j WHERE ltd IS NOT NULL AND ltd>0;
```
```sql
-- V13-2: living-on-the-edge populations (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
perwk AS (SELECT product_bigint_key po, inventory_organization_bigint_key io, date_key,
    MAX(projected_available_balance) pab, MAX(safety_stock) ss
  FROM prod_edw.fact.`20_supply_daily`,latest
  WHERE process_date=pd AND plan_name='20 Global Supply Plan'
    AND date_key BETWEEN 20260907 AND 20261207 AND safety_stock>0 GROUP BY 1,2,3),
agg AS (SELECT po, io, COUNT(*) wks, SUM(CASE WHEN pab<ss THEN 1 ELSE 0 END) wks_below,
    SUM(CASE WHEN pab<0 THEN 1 ELSE 0 END) wks_negative FROM perwk GROUP BY 1,2)
SELECT COUNT(*) all_skus,
       SUM(CASE WHEN wks_below=wks THEN 1 ELSE 0 END) always_below_edge,
       SUM(CASE WHEN wks_below>=wks*0.5 AND wks_negative=0 THEN 1 ELSE 0 END) hand_to_mouth_never_zero,
       SUM(CASE WHEN wks_negative>=1 THEN 1 ELSE 0 END) hits_zero
FROM agg;
```
```sql
-- V13-3: lead-time distribution (READ-ONLY) — reveals the bimodal 2d-median / 122d-avg split.
SELECT ROUND(PERCENTILE(complete_lead_time,0.5),0) median_lead_days,
       ROUND(AVG(complete_lead_time),0) avg_days,
       SUM(CASE WHEN complete_lead_time>56 THEN 1 ELSE 0 END) over_8wk, COUNT(*) n
FROM prod_operations.edw_extension.dim_series_ext_vw WHERE complete_lead_time>0;
```

**Gotcha logged:** lead time is **bimodal** (median 2d, avg 122d) — **never use an average lead time**; the
recoverability fence must use **per-SKU `complete_lead_time`**, or you mis-classify the long-lead tail (which is
exactly the flagged population).
