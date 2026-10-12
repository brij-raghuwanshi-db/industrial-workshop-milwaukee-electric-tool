<div align="center">

# V11 · Convergence Scenarios — Validation

### The class of problem the whole design missed: when causes/constraints/risks *pile up*

</div>

**Why this exists:** V1–V10 (and the transcript) assume **single-dominant-cause triage** — "is it demand, OR
supply, OR holds?" That framing breaks when things **converge**. Three convergence types tested live, all
material. **Source:** `20_supply_daily`, `10_demand_daily`, `purchase_orders`, `dim_series_ext_vw`.

---

## Type 1 — Multi-cause convergence on ONE SKU (the triage-breaker)

SKUs simultaneously (a) below safety stock, (b) demand over-consumed >120% of late-3, (c) supplier PO slipped:

| Population | Count | % of shortage SKUs |
|---|---|---|
| Shortage SKUs (below SS, next qtr) | 8,853 | 100% |
| …also have a **PO slip** | 7,789 | 88% |
| …also **demand over-consumed** | 4,686 | 53% |
| **…have ALL THREE at once** | **4,604** | **52%** |

→ **Over half of shortage SKUs are convergent — multiple causes stacking, not one.** The transcript's
"is it demand OR supply OR holds?" is the *wrong question for the majority of cases.*

## Type 2 — Shared-constraint convergence (one supplier → many SKUs)

Suppliers ranked by how many *distinct shortage SKUs* they touch:

| supplier | shortage SKUs it feeds |
|---|---|
| **TECHTRONIC CORDLESS GP (OUTSRCD PRDCTN)** | **3,035** |
| TTI (TECHTRONIC CORDLESS GP) LIMITED | 1,894 |
| TTI (TECHTRONIC CORDLESS GP) LTD | 870 |
| TTI (TECHTRONIC CORDLESS GP) LMTD | 317 |
| TECHTRONIC CORDLESS GP (OUTSRC SVPT) | 273 |
| MILWAUKEE MANUFACTURING CORP | 218 |
| PINEHURST MANUFACTURING GMBH | 123 |

→ **One supplier (Techtronic Cordless) sits behind 3,035 shortage SKUs** — a single constraint radiating into
thousands of per-SKU fires. Per-SKU triage would investigate 3,035 tickets and never see the *one* root.
⚠️ **DQ:** the same supplier appears under 4+ name variants (LIMITED/LTD/LMTD) — true concentration is even
higher; needs supplier-name normalization.

## Type 3 — Temporal convergence (the risk wave)

SKUs by the week they *first* cross below safety stock:

| first-cross week | # SKUs |
|---|---|
| **2026-09-07** | **6,933** |
| 2026-09-14 | 612 |
| 2026-09-28 | 441 |
| 2026-10-05 | 435 |
| 2026-11-02 | 360 |

→ **6,933 SKUs pile into the first week** (largely "already breaching now"), then a long tail. Risk arrives in
**waves, not a smooth stream** — with direct expediter/capacity-load implications.

## 📖 The story the data tells

This is the most important story in the whole validation, because it contradicts the operating assumption of the
tool we designed. The Day-3 room described root-causing as **process-of-elimination down a single most-likely
cause** — and we built a triage strip and a "likely cause" chip around exactly that. **The data says that's only
true for a minority of cases.** For **52% of shortage SKUs, demand *and* supply *and* holds are all firing at
once.** A tool that makes the planner pick one cause will, more than half the time, be hiding the other two — and
the planner's real job on those SKUs isn't "which cause" but "how do these *combine*, and which lever moves the
needle most."

Type 2 tells the scarier story: the fires are **correlated through shared constraints.** 3,035 of the shortage
SKUs trace to a single supplier. That means a huge fraction of the "8,853 individual problems" are actually **one
problem wearing 3,035 costumes.** A planner triaging SKU-by-SKU is doing 3,035 investigations of the same root
cause — the single biggest *time sink* the tool could eliminate, and it's completely invisible on a per-SKU
screen.

Type 3 adds the operational punchline: risk doesn't arrive evenly — **~7,000 SKUs crest in one week.** So even if
every root cause were known, the *capacity to act* is the binding constraint in the wave weeks. The planner needs
to see the wave coming and triage by impact, not work a flat queue.

**Net: convergence isn't an edge case — it's the common case, and the design's single-cause spine under-serves
the majority of the book.** This is a genuine gap, found by asking the data a question the transcript never did.

## Verdict: 🔴 GAP in the design — convergence is real, material, and unhandled

All three convergence types are live-confirmed and large. The current design (single-cause triage, per-SKU
screens) **does not surface any of them.** This is not a "measure breaks" 🔴 — the measures work; it's a
**missing capability** 🔴: the product has no convergence lens.

## 🔍 Root causes (of the gap)

| Convergence type | Why the design misses it |
|---|---|
| Multi-cause on one SKU | "likely cause" chip forces a single winner; no "combined contribution" view |
| Shared-constraint (supplier/component/DC) | screens are SKU-first; no constraint-first ("what's the one thing behind these 3,035") pivot |
| Temporal wave | forward-risk lists SKUs, but doesn't aggregate the **week-level load** or flag capacity crunch |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Add a **"multi-cause" flag + combined contribution bars** to the waterfall — show demand/supply/holds *together* when they co-fire (52% of cases), not a single winner | build | 🔴 must |
| 2 | Add a **constraint-first pivot** ("group my shortages by supplier / component / DC") — the Patterns view (Gap 4) is the seed; make convergence its headline. One click from 3,035 SKUs → 1 supplier action | build | 🔴 must (biggest time-saver) |
| 3 | **Normalize supplier names** (TTI LIMITED/LTD/LMTD → one entity) before concentration is trusted | build + master data | 🔴 must (or convergence is understated) |
| 4 | Add a **risk-wave / week-load view** to Coming-Risk — SKUs-crossing-per-week + a capacity flag on spike weeks | build | 🟡 should |
| 5 | Add a **convergence score** per SKU (# active causes) to the watchlist rank — a 3-cause SKU ≠ a 1-cause SKU at the same $ | build | 🟡 should |
| 6 | Route convergent SKUs to a **combined-action** path (one escalation covering the stacked causes), not three separate tickets | planner | 🟡 should |

---

## 🎬 The action model — what to DO on convergence

Detection is worthless without the action, and convergence needs a **different action model** than single-cause
triage. **Core principle:** don't "pick the biggest cause and act on it" — instead
**act on the constraint that maximizes (contribution × actionable-by-me), show the residual gap after each
action, and collapse many fires into one action where they share a root.** Convergence changes the *unit of
action* — from a SKU, to a cause-stack / a constraint / a week.

### Type 1 — Multi-cause on one SKU → **stacked mitigation (residual-gap tracker)**
One lever rarely closes a gap that's the *sum* of demand + supply + holds. So:
1. Rank co-firing causes by **contribution × who-can-act** (a 60%-demand-bias gap is a demand re-baseline, not the supply planner's expedite).
2. Apply the top movable lever, then **show what's left**: *"pull-in covers 300 of 900; remaining 600 is demand over-consumption → flag to demand."*
3. Emit **one combined escalation** covering the stack — never three disconnected tickets.
**New UI element:** a **residual-gap tracker** — each action closes part of the bar; planner sees the leftover + who owns it.

### Type 2 — Shared constraint (1 supplier → 3,035 SKUs) → **act on the constraint ONCE + allocate capacity**
The highest-leverage action in the product; it changes *who* acts (planner → sourcing):
1. **Don't triage per-SKU.** Aggregate: *"Techtronic Cordless is behind 3,035 shortage SKUs, X units, $Y, N customer-committed."*
2. **One constraint action** — supplier QBR / capacity negotiation / expedite-batch — not 3,035 expedites.
3. **Allocate the constrained capacity** to the highest-value SKUs *within* the supplier — the real decision is "given the constraint, what runs first," not "are we short."

### Type 3 — Risk wave (6,933 crossing one week) → **capacity-triage, not a flat queue**
You can't work 6,933 SKUs in a week, so manage workload:
1. **Impact-rank the wave** ($ / committed / strategic), work top-N, and **log the deferred/accept-risk tail** (a recorded decision, not an omission).
2. **Smooth** — pull next week's crossings forward where lead time allows, to flatten the spike.
3. Treat it as a **workload forecast** — staff the expediting capacity for the crest week.

### Unifying action model

| Convergence | Detect | Action | Unit of action | Who acts |
|---|---|---|---|---|
| Multi-cause / SKU | # active causes + contributions | stacked mitigation + **residual-gap tracker**; one combined escalation | **cause-stack** | planner (+ route residuals) |
| Shared constraint | group by supplier / component / DC | **one constraint action + capacity allocation** to top SKUs | **constraint** | **sourcing / procurement** |
| Temporal wave | SKUs-crossing-per-week | **impact-rank + work top-N + log deferrals + smooth** | **week** | planner + capacity plan |

**Two guardrails on convergence actions:** (1) **propose, don't auto-execute** — these move *batches*, not one
PO, so human-in-the-loop and the deterministic-vs-AI split matter *more* here; rules rank & allocate, they don't
commit. (2) **Supplier-name normalization is a prerequisite** for Type 2 — the TTI LIMITED/LTD/LMTD variants must
be unified or the constraint action fragments the very convergence it's trying to act on.

---

## ✅ Logged successful queries

```sql
-- V11 Type 1: multi-cause convergence on one SKU (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
shortage AS (SELECT DISTINCT s.product_bigint_key po FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0 AND s.projected_available_balance<s.safety_stock),
poslip AS (SELECT DISTINCT item_bigint_key po FROM prod_edw.fact.purchase_orders
  WHERE promised_delivery_date_key<>requested_delivery_date_key),
demand_over AS (SELECT DISTINCT dm.product_bigint_key po FROM prod_edw.fact.`10_demand_daily` dm,latest
  WHERE dm.process_date=pd AND dm.shipments_history > dm.final_demand_forecast_3_month_ago*1.2 AND dm.final_demand_forecast_3_month_ago>0)
SELECT COUNT(DISTINCT sh.po) shortage_skus,
       COUNT(DISTINCT CASE WHEN ps.po IS NOT NULL THEN sh.po END) also_poslip,
       COUNT(DISTINCT CASE WHEN dov.po IS NOT NULL THEN sh.po END) also_demand_over,
       COUNT(DISTINCT CASE WHEN ps.po IS NOT NULL AND dov.po IS NOT NULL THEN sh.po END) all_three
FROM shortage sh LEFT JOIN poslip ps ON sh.po=ps.po LEFT JOIN demand_over dov ON sh.po=dov.po;
```
```sql
-- V11 Type 2: shared-constraint — suppliers behind many shortage SKUs (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
shortage AS (SELECT DISTINCT s.product_bigint_key po, s.series_bigint_key sk FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0 AND s.projected_available_balance<s.safety_stock)
SELECT x.origin_supplier_name supplier, COUNT(DISTINCT sh.po) shortage_skus
FROM shortage sh JOIN prod_operations.edw_extension.dim_series_ext_vw x ON sh.sk=x.series_bigint_key
WHERE x.origin_supplier_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
```
```sql
-- V11 Type 3: temporal risk wave — SKUs first-crossing per week (READ-ONLY).
WITH latest AS (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`),
firstcross AS (SELECT s.product_bigint_key po, s.inventory_organization_bigint_key io,
    MIN(CASE WHEN s.projected_available_balance<s.safety_stock THEN s.date_key END) cross_wk
  FROM prod_edw.fact.`20_supply_daily` s,latest
  WHERE s.process_date=pd AND s.plan_name='20 Global Supply Plan'
    AND s.date_key BETWEEN 20260907 AND 20261207 AND s.safety_stock>0
  GROUP BY 1,2 HAVING MIN(CASE WHEN s.projected_available_balance<s.safety_stock THEN s.date_key END) IS NOT NULL)
SELECT cross_wk, COUNT(*) skus_crossing_this_week FROM firstcross GROUP BY 1 ORDER BY 2 DESC LIMIT 8;
```
