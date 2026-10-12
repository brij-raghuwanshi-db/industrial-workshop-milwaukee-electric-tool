<div align="center">

# V18 (N4) · "Found Inventory" — Positive Adjustments as a Supply Source — Validation

</div>

**Lead (from V5):** adjustments were framed one-directionally as *losses*, but V5 showed `CC-RECOUNT` = +42M units
*found*. Hypothesis: positive adjustments are **unexpected available supply** that can heal a shortage / flag a
count error — and treating all adjustments as bad news is wrong.

---

## Sign-split of adjustments (live)

| | events | units |
|---|---|---|
| **Found** (transaction_quantity > 0) | **25,089** | **+81,855,942** |
| **Lost** (transaction_quantity < 0) | 45,890 | −134,413,238 |
| **Net** | — | −52,557,296 |

→ Found inventory is **~35% of adjustment events and +81.9M units** — not a rounding error; a **large,
recurring positive-supply signal.**

## 📖 The story the data tells

The instinct — "adjustments = we lost inventory" — is only two-thirds right. **A third of all adjustment
events (25,089) are inventory *found*, totaling +81.9M units.** Some of that is genuine (a recount discovers
stock that was mislaid); some is the *correction* of an earlier phantom loss. Either way it's **supply the plan
didn't know it had** — and on a SKU currently flagged short, a large positive adjustment can partially or fully
*heal* the shortage, or reveal the "shortage" was a counting error in the first place (directly the DK-11
count-integrity story).

The design today would only ever read `inventory_material_transaction` adjustments as a *negative* root cause.
The data says it must read them **signed**: negative = a real loss to root-cause; positive = a heal signal that
should *downgrade* a shortage's severity, not be ignored. It's the same insight as V13's recoverability and V12's
do-nothing — **not every signal is bad news, and treating them uniformly over-states the problem.**

## Verdict: ✅ CONFIRMED — adjustments must be read signed; "found" is material

**What works ✅**
- Clean sign-split; +81.9M found across 25,089 events — a real positive-supply signal.

**Data-quality findings**
- 🟡 **DQ-1 — found ≠ new supply always.** A positive adjustment may be a *correction* of an earlier over-count,
  not net-new stock. Pair with the prior negative to avoid double-counting a heal.
- 🟡 **DQ-2 — timing.** An adjustment is a past event; to heal a *forward* shortage it must be reflected in the
  current on-hand the plan projects from — confirm the plan already ingested it before crediting a heal.
- 💭 **DQ-3 — huge magnitudes** = the recurring component/bulk-org / UoM concern (N6).

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| 35% of adjustments are "found" | recounts discover mislaid stock + corrections of earlier phantom losses |
| Tool would miss it | adjustments modeled as one-directional losses; sign ignored |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Read adjustments **signed** in the holds/adjustment lens: negative = loss (root cause), **positive = found / heal signal** | build | 🔴 must |
| 2 | On a shortage SKU, a recent **large positive adjustment downgrades severity** (heal candidate) — ties to DK-11 count-integrity and V13 recoverability | build | 🟡 should |
| 3 | Guard against double-count: net a positive adjustment against a prior offsetting negative before crediting new supply | build | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V18 N4: sign-split adjustments — found vs lost (READ-ONLY).
SELECT SUM(CASE WHEN transaction_quantity>0 THEN 1 ELSE 0 END) found_events,
       SUM(CASE WHEN transaction_quantity<0 THEN 1 ELSE 0 END) lost_events,
       ROUND(SUM(CASE WHEN transaction_quantity>0 THEN transaction_quantity ELSE 0 END),0) units_found,
       ROUND(SUM(CASE WHEN transaction_quantity<0 THEN transaction_quantity ELSE 0 END),0) units_lost,
       ROUND(SUM(transaction_quantity),0) net
FROM prod_edw.fact.inventory_material_transaction
WHERE transaction_type_description LIKE '%Adjustment%';
```
