# P1 Vertical Slice — Build Log & Evidence (Rung 1)

**Built:** 2026-08-31 · **By:** brijendra.raghuwanshi@databricks.com · profile `mke-rsc`.
**READ-ONLY** on `prod_edw`/`prod_operations`; **writes only** to `sandbox_operations.po_management.p1slice_*`.
**Anchor:** item 48111850 (M18 XC5.0 Battery) @ org 2012 Olive Branch, plan '20 Global Supply Plan', 8 weeks
(2026-07-06 → 2026-08-24).

## Assets produced
- Workspace notebook (runnable): `/Workspace/Users/brijendra.raghuwanshi@databricks.com/mke_supply_chain/p1_actuals_vertical_slice` (SQL). Source mirror: `workspace_assets/p1_actuals_vertical_slice.sql`.
- Delta tables in `sandbox_operations.po_management`:
  - `p1slice_planned_weekly` — plan's forward weekly view, one snapshot/week, enriched (item/org/cost).
  - `p1slice_actuals_weekly` — actual received (SUM), shipped (filtered SUM), week-end on-hand (point-in-time).
  - `p1slice_plan_vs_actual` — Gold: prior-snapshot plan vs actual + variance + $ impact + status. 8 rows.

## Verification (done ≥ reconciled)
1. **Source-to-Gold reconciliation — PASS.** Gold `actual_po_received` for week 2026-08-10 = **382,144**;
   raw `purchase_receipt_line` weekly SUM = **382,144**. Exact tie.
2. **Semi-additivity guard — PASS.** Week of 2026-08-24: WRONG `SUM(on_hand)` = **538,116** vs RIGHT
   point-in-time = **83,254**. The slice stored 83,254 (matches the dashboard's headline claim & the S2 story).
3. **$ impact sanity — PASS.** applied_standard_cost = **$26.9609/unit** (a real A-item cost, not the
   $0.0134 penny-part illusion). Variances dollarize sanely (e.g. week 08-10 on-hand variance +105,169 units
   ≈ +$2.84M).
4. **Idempotency — PASS.** Re-running the Gold create leaves row count unchanged (8 → 8).
5. **Guardrail — PASS.** Every `prod_edw`/`prod_operations` reference is SELECT; every write is
   `sandbox_operations.po_management.p1slice_*`. Write privilege confirmed via smoke test (created + dropped).

## What the slice shows (business read)
The M18 battery ran **progressively above plan** over the 8 weeks — actual on-hand outpaced the plan's
projected drawdown (variance +$0.54M in mid-July climbing to +$2.8M by mid-August). A real plan-accuracy
signal, cost-quantified. onhand_status bands: 2 yellow (early), 6 red — the plan under-predicted stock.

## Design for scale (Rungs 2–3, no rewrite)
- Logic is set-based; anchor item/org are isolated in the `params` CTE. **Rung 2** = drop the item filter,
  keep the 8-week window (same SQL; scale handled by one-snapshot-per-week + process_date/date_key pruning).
- **Rung 3** = bounded 180-day backfill + weekly incremental `MERGE` on
  (item×org×target_week_start×snapshot_date); tables already carry snapshot_date/week_start for this.

## Open items for the business owner (raised, non-blocking)
- Confirm `purchase_receipt_line` as the long-term receipt source (deprecated `purchase_order_delivery`
  avoided; doc-named `receiving_receipt_transactions` superseded — no item column, raw Oracle ids).
- Confirm planned-receipts should come from PO promised dates (`20_supply_daily.purchase_orders` measure is
  empty for this item); Rung-2 will add M1 receipt-attainment from `purchase_orders`.
- Confirm variance % bands (15/30) and whether comparison PAB should be prior-week vs same-week snapshot.

## Native AI/BI (Lakeview) dashboard — PUBLISHED
- **Dashboard ID:** `01f1a504e3a31d6097591184469039b4` · display name "P1 Actuals Supply Plan — M18 Battery Slice".
- **Path:** `/Workspace/Users/brijendra.raghuwanshi@databricks.com/mke_supply_chain/dashboards/`. Lifecycle ACTIVE, published, tagged `ai-dev-kit`.
- Appears in the workspace **SQL → Dashboards** list (the `/sql/dashboards` link).
- Backed by `sandbox_operations.po_management.p1slice_plan_vs_actual` (bare table name; catalog/schema via dataset flags). Warehouse `7bd33a82f4e92206`.
- Widgets: 4 KPI counters (weeks, avg |variance|%, max $ variance, weeks off-plan) + plan-PAB-vs-actual-on-hand line (+ safety stock) + on-hand $ variance bar colored by green/yellow/red status + weekly flows line (planned SO / shipped / received) + weekly detail table. All 4 queries CLI-tested (SUCCEEDED) before deploy.
- Source JSON: `workspace_assets/p1_dashboard.json`. Update via `databricks lakeview update <id> --dataset-catalog sandbox_operations --dataset-schema po_management ...` then `publish` (never re-create).

### "No data" fix (published view was empty on first publish)
- **Symptom:** published dashboard rendered layout/titles but every widget said "No data" (table verified populated; warehouse RUNNING).
- **Changes applied + republished (rev 2026-08-31T06:32):** (1) counters converted from `MEASURE()`/dataset-`columns` to **inline aggregation** (self-contained); (2) dataset query **fully-qualified** the source (`FROM sandbox_operations.po_management.p1slice_plan_vs_actual`) to remove any bare-name resolution dependency.
- **Verified:** the deployed (draft) dataset query returns **8 rows** when run verbatim on warehouse 7bd33a82f4e92206; JSON valid; catalog/schema attached. CLI cannot render the visual — confirm in browser (hard-refresh the published view).
- Note: `lakeview get-published` returns metadata only (no serialized body) — not a fault; use `lakeview get` to inspect the draft's serialized JSON.

### ROOT CAUSE of "Select fields to visualize" (the real one)
- Widgets showed "Select fields to visualize" (encodings not binding) even though dataset + query returned 8 rows.
- **Cause:** each widget's query was named `"q"`. The known-good working example (skill `4-examples.md`) names EVERY widget query **`"main_query"`** — the binding relies on that. My hand-authored skeleton used `"q"`, so encodings never resolved. (Grant/data/catalog were all fine — the earlier fixes were not the issue.)
- **Fix (rev 2026-08-31 ~06:4x):** renamed all 8 widget queries `q` → `main_query`; update + publish on same ID; verified deployed dashboard now has only `main_query`. Lesson: copy the exact serialized structure from a working dashboard, don't hand-invent widget JSON.

### Second "No data" (3 counters only) — widget expressions can't wrap functions
- After the `main_query` fix, charts + table + the COUNT counter rendered, but 3 counters still said "No data".
- **Cause:** widget field expressions may only be a PLAIN aggregation of a BARE column. `COUNT(week_start)` worked; `AVG(ABS(...))`, `MAX(ABS(...))`, `SUM(CASE WHEN ...)` were rejected (ABS/CASE not allowed in a widget expression).
- **Fix:** pushed the ABS()/CASE logic into the DATASET SELECT as aliased columns (`abs_var_pct`, `abs_var_dollar`, `off_plan_flag`); counters now do plain `AVG/MAX/SUM` on those bare columns. Verified values: avg |var| 172.65%, max $ 2,835,451, weeks off-plan 8. Redeployed + published.
- Rule: all business logic (ABS, CASE, ratios) goes in the dataset SQL with aliases; widget expressions = one of SUM/AVG/COUNT/MIN/MAX/COUNT(DISTINCT)/DATE_TRUNC on a bare column only.

### Third break — MISSING COMMA broke the whole dataset (all widgets errored)
- When I injected the derived columns, the prior line ended `applied_standard_cost ` with NO comma, so the SELECT read `applied_standard_cost ABS(...)` → PARSE_SYNTAX_ERROR → the entire dataset failed → every widget showed "Unable to render visualization / Show error."
- **Cause:** `queryLines` are joined VERBATIM with no separator; each line must end with its own comma/space. Hand-editing them is fragile.
- **Fix:** rewrote the whole `queryLines` block cleanly (comma after `applied_standard_cost,`); TESTED the full query returns 8 rows BEFORE redeploying. Lesson: always run the exact concatenated dataset query via CLI after any queryLines edit, before publish.

### Added filters (was missing)
- Added 3 page-level filters (field-based binding, `disaggregated:false`, distinct query name matching `encodings.fields[].queryName`): `filter_status` (on-hand status multi-select), `filter_week` (date-range picker), `filter_abc` (ABC multi-select). Shifted content down 2 rows. Field-based filters are safe here because the dataset is a plain SELECT (no GROUP BY/CTE) — engine auto-injects WHERE.

## Reproduce
Open the workspace notebook and Run All (serverless SQL warehouse), or re-run `workspace_assets/p1_actuals_vertical_slice.sql`.
