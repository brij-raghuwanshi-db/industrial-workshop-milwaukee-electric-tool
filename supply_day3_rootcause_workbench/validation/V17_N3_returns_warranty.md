<div align="center">

# V17 (N3) · Returns / Warranty / Reverse Logistics — Validation

</div>

**Lead (from V14):** a whole domain the Day-3 scope never touched. For a tool brand, returns + warranty are
material and are *both* a demand signal and a supply source. Does the data exist and is it usable?

> **⚠ CORRECTION (2026-09-03) — verdict upgraded 🟡 cross-system → ✅ conformed & item-keyed.**
> The original verdict below was based on the **raw `staging_jde` / `staging_ax` tables** (keyed on
> `tool_nbr`/`tool_serial_nbr`). A deeper table sweep found the **governed, conformed fact**
> `prod_edw.fact.warranty_transaction` — which carries **`item_bigint_key`** and joins straight to
> `items_scd1` (no crosswalk to build). The whole `prod_edw.domain_service` schema already integrated
> JDE/AX/Oracle/Connect upstream. **60 real SKU IDs pulled** (e.g. `2446-20, 6536-21, MXF302-2HD, 6161-33`).
> Query: `JOIN prod_edw.fact.warranty_transaction w … w.item_bigint_key = i.item_bigint_key WHERE
> w.posting_date_key >= 20260101`. Columns available: `replacement_reason_code`, `problem_description`,
> `part_quantity`, `material_cost`/`labor_cost`/`freight_cost`, `warranty_claim_id`, `serial_number`.
> **Remaining watch-out:** `part_bigint_key` (replaced part) ≠ `item_bigint_key` (returned tool) — choose grain
> deliberately. The "profile + build crosswalk" action below is superseded — the crosswalk already exists.

---

## What exists (live)

| table | rows | key columns |
|---|---|---|
| `prod_edw.staging_jde.fact_warranty_tool` | **3,204,168** | `tool_serial_nbr`, `tool_qty`, `reason_cd`, `gl_date` |
| `prod_edw.staging_ax.return_reason_code_temporal` | taxonomy | reason code + description |
| `prod_edw.dimension.warranty_scd1`, `domain_item.fact_item_service_return_eligibility` | — | warranty/return master |

**Return reason codes (real):** Customer Error/Duplicate Shipment (restock fee), Order Processing Error,
Keypunch Error, Shipping Error, **Annual Stock Adjustment** — a mix of *operational* returns and *stock*
movements.

## 📖 The story the data tells

Returns and warranty are a **real, populated, and completely untapped** domain — **3.2M warranty-tool records**
with serial-level detail, plus a governed return-reason taxonomy. The reason codes reveal *two* different
stories hiding in "returns":
- **Operational returns** (Customer Error, Shipping Error, Duplicate Shipment) → these come *back into stock* →
  a **supply source** that can heal a shortage or inflate excess. Today the plan almost certainly doesn't count
  inbound returns as available supply.
- **Warranty / quality returns** (the warranty-tool flow) → a *quality* and *reverse-logistics* signal — and for
  a power-tool brand, a leading indicator of product issues.

So the untapped value is twofold: returns as a **supply source** the plan ignores (relevant to shortage healing
and the DK-11 count-integrity story), and warranty as a **quality/root-cause lens** of its own. Neither is in the
Day-3 shortage tool.

**The honest caveat:** this lives in **JDE / AX staging** (`staging_jde`, `staging_ax`), *separate* from the
Oracle Fusion supply plan (`20_supply_daily`) and its `series`/`product` keys. So joining returns to the shortage
board is a **cross-system integration** (needs an item-key crosswalk JDE/AX ↔ EDW) — more than a one-join lens.
That's why it's a candidate, not a quick add.

## Verdict: ✅ CONFIRMED exists & material — 🟡 but cross-system to integrate

**What works ✅**
- 3.2M warranty records + governed return-reason taxonomy — real, populated, serial-level.
- Two distinct usable signals: returns-as-supply-source, warranty-as-quality-lens.

**Data-quality / integration findings**
- 🟡 **DQ-1 — different source system.** JDE/AX staging, not Oracle Fusion EDW → needs an **item-key crosswalk**
  to tie to the supply plan. Not a `series_bigint_key` join.
- 🟡 **DQ-2 — mixed semantics in "returns."** Reason codes span operational restocks vs quality vs stock
  adjustments — must be split before use (a "return" isn't one thing).
- 💭 **DQ-3 — scope.** Warranty (3.2M) is large; assess whether it's a demand-decomposition input, a supply
  source, or its own quality lens before building.

## 🔍 Root causes (of it being untapped)

| Finding | Root cause |
|---|---|
| Never in the supply plan | returns/warranty live in JDE/AX; the Oracle Fusion plan doesn't ingest inbound returns as supply |
| "Returns" is ambiguous | one word covers restock, quality, and stock-adjustment flows |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Profile the warranty/return facts properly** (grain, item-key, date coverage) + build the JDE/AX↔EDW crosswalk | data eng | 🟡 should |
| 2 | Split returns by reason: **operational restock (supply source)** vs **warranty/quality (root-cause lens)** | build | 🟡 should |
| 3 | Assess **returns-as-supply** in the shortage-heal path (a large restock can downgrade a shortage — ties to N4/DK-11) | analyst | 🟡 could |
| 4 | Consider a **warranty/quality lens** as a separate future capability (leading indicator of product issues) | product | 💭 later |

---

## ✅ Logged successful queries

```sql
-- V17 N3: warranty volume + columns (READ-ONLY).
SELECT COUNT(*) rows FROM prod_edw.staging_jde.fact_warranty_tool;
SELECT column_name FROM prod_edw.information_schema.columns
WHERE table_schema='staging_jde' AND table_name='fact_warranty_tool';
-- return reason taxonomy:
SELECT * FROM prod_edw.staging_ax.return_reason_code_temporal LIMIT 5;
```

**Note:** returns/warranty are **cross-system** (JDE/AX staging), so integrating them with the Fusion supply plan
requires an item-key crosswalk — a real project, not a one-join lens. Confirmed present & material; deferred.
