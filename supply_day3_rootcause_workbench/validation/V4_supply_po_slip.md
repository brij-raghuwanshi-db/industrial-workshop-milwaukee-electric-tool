<div align="center">

# V4 · Supply / PO Slip + Who-Moved-It — Validation

</div>

**Claims (design):** show PO requested vs promised/ETA slip in days; detect date drift; attribute "who moved it"
(BUYER/SUPPLIER/…). **Measures:** `slip_days = DATEDIFF(promised, requested)`, `drift = promised − original`,
`change_order_originator_type`. **Source:** `purchase_orders` + `purchase_order_change_orders` + `date_scd1`.

---

## Test 1 — requested-vs-promised slip (10 real POs, realistic dates)

| # | PO | item | requested | promised | slip (days) |
|---|---|---|---|---|---|
| 1 | 380046660 | 204021 | 2026-06-03 | 2027-01-01 | **212** |
| 2 | 380047564 | 202321 | 2026-06-03 | 2027-01-01 | 212 |
| 3 | 380063820 | 202021 | 2026-06-08 | 2027-01-01 | 207 |
| 4 | 380047564 | 202321 | 2026-06-09 | 2027-01-01 | 206 |
| 5 | 380047560 | 204121 | 2026-06-09 | 2027-01-01 | 206 |
| 6 | 380058554 | 301420 | 2026-06-01 | 2026-12-22 | 204 |
| 7 | 380047570 | 204421 | 2026-06-17 | 2027-01-01 | 198 |
| 8 | 380089802 | 5809EM70 | 2026-06-10 | 2026-12-23 | 196 |
| 9 | 380089802 | 5809EM70 | 2026-06-10 | 2026-12-23 | 196 |
| 10 | 380047571 | 204421 | 2026-06-23 | 2027-01-01 | 192 |

→ Real, sensible slips (~6–7 month promise-outs). The **requested→promised** comparison works cleanly.

## Test 2 — who moved it (change originators, 2026 YTD)

| originator | changes | distinct suppliers |
|---|---|---|
| BUYER | 1,862,294 | 1,936 |
| REQUESTER | 5,718 | 215 |
| **SUPPLIER** | **1,283** | **19** |
| SYSTEM | 304 | 9 |

→ The accountability signal works: supplier-initiated changes are a **tiny, concentrated (19 suppliers)** slice —
the high-value "did they warn us or did we catch it" signal.

## 📖 The story the data tells

The supply story has two layers. On the surface, **slips are large and pervasive** — 200+ day promise-outs are
easy to find, and 2.24M of 3.84M POs show promise ≠ original. A planner is right to feel PO dates move constantly.

But the deeper story is a **data-trust one**, and it's the most important thing V4 surfaced: **the "original
promise" field is largely a placeholder.** Sort by orig→current slip and the entire top is `2000-01-01 →
2100-12-31` sentinels giving a fake 36,889-day slip. So the *drift* metric ("promise moved from its original")
is **not trustworthy as-is** — most "moves" are just "no original was ever recorded." The reliable story comes
from **requested→promised** (what the buyer asked vs what the supplier committed), which is clean and real.

The accountability layer tells the sharpest story: of ~1.87M PO changes in 2026, **only 1,283 were
supplier-initiated, across just 19 suppliers.** Nearly all churn is *internal* (BUYER). So when the transcript
says "we'd have more ability to hold suppliers accountable" — the data says the supplier-caused slips are a
*small, nameable set*, which is exactly what makes a targeted supplier scorecard (V-supplier) feasible rather
than boiling the ocean.

## Verdict: 🟡 works — but only with the right date columns and sentinel filtering

**What works ✅**
- Requested→promised slip: clean, real, sensible magnitudes.
- Originator attribution: works; supplier slips are concentrated (19 suppliers) — the accountability win.

**Data-quality findings (this screen has the most DQ traps so far)**
- 🔴 **DQ-1 — date-key subtraction is NOT day-count.** `promised_date_key − original_date_key` on `yyyyMMdd`
  integers gives garbage (20270101−20261230 = 871, not 2 days). **Must use `DATEDIFF` via `date_scd1`.** A naïve
  keydiff sort returns nonsense — this exact trap returned an empty/garbage result until fixed.
- 🔴 **DQ-2 — sentinel dates pollute "original promise."** `original_promised_delivery_date_key` is frequently
  `2000-01-01` (and current `2100-12-31`), i.e. placeholders. The 2.24M "promise moved" count is **inflated by
  no-original-recorded** cases. **Drift (orig→current) is unreliable; use requested→promised instead**, and
  filter sentinels (date between realistic bounds).
- 🟡 **DQ-3 — PO grain fan-out.** POs repeat across lines/schedules (380047564 appears twice) — aggregate to
  PO+line or dedupe before ranking, or one PO double-counts.
- 🟡 **DQ-4 — supplier join.** Originator supplier is `supplier_bigint_key` on the change table; naming needs the
  supplier dim (deferred, noted in mapping).

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Garbage slip on keydiff (DQ-1) | `date_key` is an integer label (yyyyMMdd), not a day number — arithmetic on it is meaningless across month/year boundaries |
| "Original promise" untrustworthy (DQ-2) | Oracle populates a **default sentinel** (2000-01-01 / 2100-12-31) when no original commit exists → "moved" is often "never set" |
| Most changes are BUYER (story) | internal replanning dominates; genuine supplier reschedules are rare (1,283) and concentrated |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Always compute slip via `DATEDIFF(date_scd1)`**, never key subtraction — bake into serving layer & join-doc hazard | build | 🔴 must |
| 2 | Use **requested→promised** as the primary slip; treat orig→current *drift* as unreliable until sentinels are handled | build | 🔴 must |
| 3 | **Filter sentinel dates** (`2000-01-01`, `2100-12-31`) everywhere PO dates are used | build | 🔴 must |
| 4 | **Dedupe PO lines/schedules** before ranking slips (DQ-3) | build | 🟡 should |
| 5 | Feed the **19 supplier-slip suppliers** into the supplier scorecard as the targeted-QBR list | sourcing | 🟡 should |
| 6 | Confirm with a planner whether "original promise" is ever meaningful, or always sentinel | planner | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V4 Test 1: requested->promised slip (READ-ONLY). Use DATEDIFF via date_scd1, filter realistic dates.
SELECT po.purchase_order_number pon, i.item_id,
       dreq.date_value requested, dcur.date_value promised,
       DATEDIFF(dcur.date_value, dreq.date_value) AS slip_days
FROM prod_edw.fact.purchase_orders po
JOIN prod_edw.dimension.items_scd1 i ON po.item_bigint_key=i.item_bigint_key
JOIN prod_edw.dimension.date_scd1 dreq ON po.requested_delivery_date_key=dreq.date_key
JOIN prod_edw.dimension.date_scd1 dcur ON po.promised_delivery_date_key=dcur.date_key
WHERE dreq.date_value BETWEEN DATE'2026-06-01' AND DATE'2027-01-01'
  AND dcur.date_value BETWEEN DATE'2026-06-01' AND DATE'2027-01-01'
  AND DATEDIFF(dcur.date_value, dreq.date_value) > 0
ORDER BY slip_days DESC LIMIT 10;
```
```sql
-- V4 Test 2: who moved it (READ-ONLY).
SELECT change_order_originator_type, COUNT(*) changes, COUNT(DISTINCT supplier_bigint_key) suppliers
FROM prod_edw.fact.purchase_order_change_orders
WHERE change_order_date_key > 20260101 GROUP BY 1 ORDER BY changes DESC;
```
```sql
-- V4 DQ probe: column population + how many "moved" are really sentinels.
SELECT COUNT(*) total,
       SUM(CASE WHEN promised_delivery_date_key<>original_promised_delivery_date_key THEN 1 ELSE 0 END) promise_moved,
       SUM(CASE WHEN promised_delivery_date_key<>requested_delivery_date_key THEN 1 ELSE 0 END) promise_ne_req
FROM prod_edw.fact.purchase_orders;
```

**Gotchas logged:** (1) `date_key` subtraction ≠ days — use `DATEDIFF(date_scd1.date_value)`; (2)
`original_promised_delivery_date_key` is often a **sentinel** (2000-01-01/2100-12-31) — orig→current "drift" is
unreliable; prefer requested→promised and filter sentinel dates.
