<div align="center">

# V5 · Holds / Adjustments / Quality — Validation

</div>

**Claims (design):** the long-tail root causes — inventory adjustments (lost/found), on-hold (present, not
shippable), quality rejects. **Sources:** `inventory_material_transaction` (adjustments),
`sales_fulfillment_hold_transactions` (+`hold_codes_vl`), `receiving_receipt_transactions` (quality).

---

## Test 1 — Adjustments by reason (cleanest of the three) ✅

| type | reason | count | net qty |
|---|---|---|---|
| Cycle Count Adjustment | *(none)* | 22,708 | −1,074,833 |
| Purchase Order Receipt Adjustment | *(none)* | 9,907 | −17,452,102 |
| Cycle Count Adjustment | CC- UNDETERMINED | 9,301 | −10,924,085 |
| Cycle Count Adjustment | INV - Inv Adjustment | 8,829 | +26,062 |
| Cycle Count Adjustment | CC- ADJUSTMENT ERROR | 4,894 | −41,534,130 |
| Cycle Count Adjustment | CC-INACCURATE RM TRANSFER TRAN | 2,464 | −5,467,542 |
| Cycle Count Adjustment | CC-RECOUNT | 1,732 | **+42,081,673** |
| Cycle Count Adjustment | CC- UNREPORTED SCRAP | 1,610 | −12,051,659 |

→ Rich, usable reason taxonomy; signed net qty (− = lost, + = found). `CC-RECOUNT +42M` = found inventory;
`ADJUSTMENT ERROR −41.5M` = lost. This is exactly the "DCs lost inventory" root cause, and it's well-populated.

## Test 2 — Holds ⚠️ (grain trap)

| metric | value |
|---|---|
| hold transaction rows | **2,405,150,375** (2.4B) |
| distinct sales orders | 10,231,125 |
| rows per order | **~235** |
| `hold_release_date_key IS NULL` | **0** |
| sentinel release (0 / <19000000) | **180,996,126** |
| apply-date range | 2017-06-22 … 2026-09-02 |

→ The table is **~235 rows per order** — it is a **periodic (daily) snapshot of hold state**, not one row per
hold event. So "currently held" is **NOT** `hold_release_date_key IS NULL` (that returns 0). It's: latest
snapshot **AND** a sentinel/blank release. The naïve pattern in the design doc returns nothing.

## Test 3 — Quality (genuinely rare long tail) ✅

| inspection_status_code | count |
|---|---|
| NOT INSPECTED | 11,131,993 |
| ACCEPTED | 81,359 |
| **REJECTED** | **154** |
| None | 6 |

→ Quality rejects = **154 of 11.1M** receipts. Confirms the transcript ("usually quality, but very unique") —
quality is a real but *tiny* long-tail cause. Don't over-invest a screen in it; a flag suffices.

## 📖 The story the data tells

The long tail behaves exactly as the planners described — and the data sharpens the priorities. **Adjustments
are the substantive long-tail cause:** millions of units swing through cycle-count corrections, with named
reasons that read like a shrinkage report — UNREPORTED SCRAP (−12M), ADJUSTMENT ERROR (−41.5M), and a giant
RECOUNT *gain* of +42M. The story here is that a big chunk of "we lost inventory" is really **count accuracy /
scrap reporting**, and it's already coded by reason — so root-causing an adjustment-driven miss is genuinely
answerable.

**Quality is the smallest tail of all** — 154 rejects in 11M receipts. The planners said quality is "usually the
reason but very unique," and the data agrees: it's real, nameable, but rare. It deserves a flag, not a franchise.

**Holds are the trap.** At face value the table says "0 currently held" — which is *wrong*, an artifact of it
being a 2.4-billion-row daily snapshot where release is a sentinel, not a null. The story the data quietly tells
is a governance one: **the most operationally-loaded of the three signals is also the one most likely to be
mis-read by a naïve query** — and a tool that showed "0 holds" would be confidently, dangerously wrong.

## Verdict: 🟡 — adjustments ✅ ready, quality ✅ ready (rare), holds 🔴 need grain handling

**Data-quality findings**
- 🔴 **DQ-1 — holds is a 2.4B-row daily snapshot** (~235 rows/order). "Currently held" ≠ `release IS NULL` (=0);
  use latest snapshot + sentinel-release logic. Naïve query returns a false "0 holds."
- 🟡 **DQ-2 — adjustment `reason_name` often null** (top 2 buckets have no reason) — a third of volume is
  uncoded; usable but not complete.
- 🟢 **DQ-3 — quality is clean but tiny** (154 rejects) — scope accordingly.
- 🟡 **DQ-4 — adjustment magnitudes are huge** (±40M) — same component/bulk-org UoM concern as V1/V2; segregate.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| "0 holds" (DQ-1) | table is a periodic **snapshot of hold state**, not an event log; release uses a **sentinel**, not null |
| Adjustments uncoded (DQ-2) | some Oracle cycle-count txns post without a reason flexfield value |
| Quality tiny (DQ-3) | most receipts are **NOT INSPECTED** (inspection is exception-based) → rejects are inherently rare |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Holds "currently held" = latest snapshot + non-sentinel/blank release** — never `IS NULL`; validate the snapshot grain with the data owner | build + data owner | 🔴 must |
| 2 | Adjustments: ship the **reason-coded view** (it's rich); show "uncoded" explicitly for the null-reason third | build | 🟢 ready |
| 3 | Quality: a **flag/badge**, not a full screen — 154 rejects don't warrant more | build | 🟢 ready |
| 4 | Segregate component/bulk orgs from finished-goods on adjustment magnitudes (DQ-4) | build | 🟡 should |
| 5 | Reconcile hold **units** (not just txns) against the on-hand balance for the "not shippable" number | build | 🟡 should |

---

## ✅ Logged successful queries

```sql
-- V5 Test 1: adjustments by reason (READ-ONLY).
SELECT transaction_type_description typ, reason_name reason,
       COUNT(*) n, ROUND(SUM(transaction_quantity),0) net_qty
FROM prod_edw.fact.inventory_material_transaction
WHERE transaction_type_description LIKE '%Adjustment%'
GROUP BY 1,2 ORDER BY n DESC LIMIT 10;
```
```sql
-- V5 Test 2: holds grain probe (READ-ONLY) — reveals the snapshot nature + sentinel release.
SELECT COUNT(*) rows, COUNT(DISTINCT sales_order_id) orders,
       SUM(CASE WHEN hold_release_date_key IS NULL THEN 1 ELSE 0 END) null_release,
       SUM(CASE WHEN hold_release_date_key=0 OR hold_release_date_key<19000000 THEN 1 ELSE 0 END) sentinel_release,
       MIN(hold_apply_date_key) min_apply, MAX(hold_apply_date_key) max_apply
FROM prod_edw.fact.sales_fulfillment_hold_transactions;
```
```sql
-- V5 Test 3: quality inspection status (READ-ONLY).
SELECT inspection_status_code, COUNT(*) n
FROM prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions
GROUP BY 1 ORDER BY n DESC LIMIT 6;
```

**Gotcha logged:** `sales_fulfillment_hold_transactions` is a **2.4B-row periodic snapshot** — `hold_release_date_key
IS NULL` returns **0** (false "no holds"). Use latest snapshot + sentinel-release detection to find currently-held.
