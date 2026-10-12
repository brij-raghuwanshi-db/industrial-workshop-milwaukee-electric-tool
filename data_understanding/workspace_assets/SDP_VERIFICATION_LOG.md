# SDP Pipeline — Verification Log (test cases, queries, results)

Parallel SDP build of P1 "Actuals Supply Plan". Every check below was run live on warehouse
`7bd33a82f4e92206`, profile `mke-rsc`, against `sandbox_operations.po_management.sdp_*` (READ-ONLY
on `prod_edw`/`prod_operations`). Pipeline `p1_actuals_sdp` id `b6f16cf7-b17e-4b08-beaa-6c8e7fb97585`.
Clone dashboard `01f1a5371959178aa137d5551347afff`. Live/original dashboard `01f1a50aed891d5c85b5e64b2c3c5d5b`
(untouched). Window: Monday snapshots 20260504→20260824 (4 months), orgs 2012+2120.

Legend: ✅ pass. All row/value diffs vs the live rung2_* tables are the equivalence guarantee.

---

## T0 — rootcause_plant re-derivation reconciliation (no saved build SQL; re-derived from source)
Anchor: plant 1006 Transfer/rebalance must equal 200,950 txns (Subinv Transfer 170,204 + Movement
Request 22,202 + Transfer Order Pick 5,698 + Transfer Order Interorg Shipment 2,846).
```sql
-- reconstructed CASE vs live table; count mismatched cells + total txn diff
WITH recon AS (
  SELECT l.organization_code AS org,
    CASE
      WHEN t.transaction_type_description LIKE '%Adjustment%'
        OR t.transaction_type_description IN ('Cycle Count Adjustment','Miscellaneous Receipt','Miscellaneous Issue',
                                              'Account Alias Issue','Account Alias Receipt','Return to Supplier') THEN 'Inventory adjustment'
      WHEN t.transaction_type_description LIKE '%Transfer%' OR t.transaction_type_description LIKE '%Movement Request%' THEN 'Transfer/rebalance'
      WHEN t.transaction_type_description LIKE 'Work in Process%' THEN 'Production (WIP)'
      WHEN t.transaction_type_description LIKE '%Purchase Order Receipt%' THEN 'Supply receipts'
      WHEN t.transaction_type_description LIKE 'Sales Order%' THEN 'Demand (issues/returns)'
      ELSE 'Other' END AS root_cause,
    COUNT(*) txns
  FROM prod_edw.fact.inventory_material_transaction t
  JOIN prod_edw.dimension.location_scd1 l ON t.location_bigint_key=l.location_bigint_key
  WHERE t.transaction_date_key BETWEEN 20260504 AND 20260831 GROUP BY 1,2)
SELECT COUNT(*) mismatched_cells, COALESCE(SUM(ABS(r.txns - CAST(p.txns AS BIGINT))),0) total_txn_diff
FROM recon r JOIN sandbox_operations.po_management.rootcause_plant p
  ON r.org=p.organization_code AND r.root_cause=p.root_cause WHERE r.txns <> CAST(p.txns AS BIGINT);
```
RESULT: mismatched_cells=16, total_txn_diff=660 (of ~1.3M = 99.95%). Entire residual = the
"Purchase Order Receipt Adjustment" label boundary (offsets equal-and-opposite between Supply-receipts
and Inventory-adjustment per org). ✅ derivation sound; SDP uses adjustment-first (cleaner semantic).

## T1 — Silver/Gold row-count equivalence (sdp vs live)
```sql
SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_plan_vs_actual;    -- 590275
SELECT COUNT(*) FROM sandbox_operations.po_management.rung2_plan_vs_actual;  -- 590275
SELECT COUNT(DISTINCT concat(item_bigint_key,'|',org_bigint_key,'|',cast(week_start AS string)))
  FROM sandbox_operations.po_management.sdp_plan_vs_actual;                  -- 590275 (grain==rows, no fanout)
SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_planned_weekly;    -- 16464696
SELECT COUNT(*) FROM sandbox_operations.po_management.rung2_planned_weekly;  -- 16464696
```
RESULT: sdp gold 590,275 == live 590,275; grain distinct == rows; planned_weekly identical. ✅

## T2 — Per-org value equivalence (rows, net variance $, red count) — must be ZERO diff
```sql
WITH s AS (SELECT organization_code, COUNT(*) n, ROUND(SUM(onhand_variance_dollar),0) netv,
             SUM(CASE WHEN onhand_status='red' THEN 1 ELSE 0 END) red
           FROM sandbox_operations.po_management.sdp_plan_vs_actual GROUP BY organization_code),
     l AS (SELECT organization_code, COUNT(*) n, ROUND(SUM(onhand_variance_dollar),0) netv,
             SUM(CASE WHEN onhand_status='red' THEN 1 ELSE 0 END) red
           FROM sandbox_operations.po_management.rung2_plan_vs_actual GROUP BY organization_code)
SELECT s.organization_code org, (s.n-l.n) row_diff, (s.netv-l.netv) net_diff, (s.red-l.red) red_diff
FROM s JOIN l ON s.organization_code=l.organization_code ORDER BY org;
```
RESULT: 2012 → (0, 0.0, 0); 2120 → (0, 0.0, 0). ✅ bit-exact both orgs.

## T3 — DQ expectations (T5 closure): predicate violations must all be ZERO
```sql
SELECT
  SUM(CASE WHEN item_bigint_key IS NULL OR org_bigint_key IS NULL OR week_start IS NULL THEN 1 ELSE 0 END) viol_keys,
  SUM(CASE WHEN organization_code NOT IN ('2012','2120') THEN 1 ELSE 0 END) viol_org,
  SUM(CASE WHEN onhand_status NOT IN ('green','yellow','red','no-data') THEN 1 ELSE 0 END) viol_status,
  SUM(CASE WHEN alert_tier NOT IN ('0 · OK','1 · Monitor','2 · Alert','3 · Escalate') THEN 1 ELSE 0 END) viol_tier,
  COUNT(DISTINCT concat(organization_code,'|',plan_name)) org_plan_pairs
FROM sandbox_operations.po_management.sdp_plan_vs_actual;
```
RESULT: viol_keys=0, viol_org=0, viol_status=0, viol_tier=0, org_plan_pairs=2. Pipeline 0 ERROR events.
✅ all 4 EXPECT constraints hold; 2120 double-count guard holds (each org on exactly one plan).

## T4 — Number-level equivalence on marquee metrics (cockpit newly-red, FVA)
```sql
-- newly-red count/$ (latest week) from pre-aggregated transitions
WITH wks AS (SELECT DISTINCT week_start, DENSE_RANK() OVER (ORDER BY week_start DESC) r
             FROM sandbox_operations.po_management.sdp_agg_transitions),
     latest AS (SELECT week_start w FROM wks WHERE r=1)
SELECT SUM(newly_red) newly_red, ROUND(SUM(newly_red*dollar),0) newly_red_dollar
FROM sandbox_operations.po_management.sdp_agg_transitions WHERE week_start=(SELECT w FROM latest);
-- FVA sdp vs live recompute
SELECT org, fva_pct FROM sandbox_operations.po_management.sdp_agg_fva ORDER BY org;
```
RESULT: newly_red=2,243 / $23,723,747 (== known live 2,243 / $23.7M). FVA 2012=−3.7%, 2120=−11.2%
== live recompute −3.7% / −11.2%. ✅ pre-aggregation reconstructs exact values.

## T5 — Performance gate: serving-table row counts (live scan per widget class)
```sql
SELECT (SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_agg_week_org) week_org,   -- 32
       (SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_agg_scorecard) scorecard,  -- 2
       (SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_agg_fva) fva,               -- 2
       (SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_agg_rootcause_dc) rootcause_dc, -- 160
       (SELECT COUNT(*) FROM sandbox_operations.po_management.sdp_agg_money_ow) money_ow;     -- 32
```
RESULT: overview/accuracy/KPI serving tables = 2–160 rows (vs 590,275 live → up to ~18,400× cut). ✅
Detail tiles (action list / exception queue) return LIMIT-bounded 200/500 over pre-materialized
row tables (heavy chronic-join + WoW-LAG computed once, not per render).

## T6 — All 42 cloned datasets return rows at default params (org_f=[], wk=2026-05-11..08-24, sku=48111850)
Method: substitute params, `SELECT COUNT(*) FROM (<thin query>)` for every dataset.
RESULT: TESTED 42/42, OK=42, FAIL=0, EMPTY=0. Aggregate tiles 2–128 rows; drill tiles row-level
(pruned at runtime by :sku/:org filters — ds_drill_sku proves sku-drill → 32 rows). ✅
(Fix applied mid-test: ds_sla referenced organization_code; serving MV outputs `org` → corrected.)

## T7 — Overview cube (perf gap closure): equivalence of the 9 additive tiles vs raw ds_pva
User caught that the overview page still scanned raw 590k (its counters/bars aggregate in-widget).
Built `sdp_agg_overview` = week×org×abc×status cube (**626 rows**), repointed the 9 additive tiles
(c_off, c_maxd, p1_money_so/ex, p1_statusbar/abcbar/orgstatus/orgdollar, p1_nettrend). c_bias (AVG)
and c_items (COUNT DISTINCT) stay on raw ds_pva — a widget cannot reconstruct those from a rollup.
First cut ROUNDed per-cell → a $9-on-$2.5bn rounding-order drift; fixed by storing FULL-PRECISION
sums in the cube and rounding only at display. Diff after fix:
```sql
WITH cube AS (SELECT SUM(off_flag_sum) off, ROUND(SUM(sum_abs_dollar),0) absd, ROUND(SUM(net_dollar),0) net,
  ROUND(MAX(max_abs_dollar),0) maxd, ROUND(SUM(stockout_dollar),0) so, ROUND(SUM(excess_dollar),0) ex
  FROM sandbox_operations.po_management.sdp_agg_overview),
raw AS (SELECT SUM(CASE WHEN onhand_status IN ('yellow','red') THEN 1 ELSE 0 END) off,
  ROUND(SUM(ABS(onhand_variance_dollar)),0) absd, ROUND(SUM(onhand_variance_dollar),0) net,
  ROUND(MAX(ABS(onhand_variance_dollar)),0) maxd,
  ROUND(SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand<planned_safety_stock THEN (planned_safety_stock-actual_end_on_hand)*applied_standard_cost ELSE 0 END),0) so,
  ROUND(SUM(CASE WHEN planned_safety_stock>0 AND actual_end_on_hand>3*planned_safety_stock THEN (actual_end_on_hand-3*planned_safety_stock)*applied_standard_cost ELSE 0 END),0) ex
  FROM sandbox_operations.po_management.rung2_plan_vs_actual)
SELECT (cube.off-raw.off) d_off, (cube.absd-raw.absd) d_absd, (cube.net-raw.net) d_net,
       (cube.maxd-raw.maxd) d_maxd, (cube.so-raw.so) d_so, (cube.ex-raw.ex) d_ex FROM cube, raw;
```
RESULT: d_off=0, d_absd=0, d_net=0, d_maxd=0, d_so=0, d_ex=0 — **bit-exact**. Overview live scan
590,275 → **626 rows** for the 9 additive tiles. ✅ (Learning: never ROUND inside a pre-agg serving
table; round only at display, else re-summing rounded cells drifts vs the base fact.)

## T8 — Full-dashboard structural sweep (clone)
Method: walk every page/widget — flag line/area with >1 y-field (multi-y collapse bug) and any
encoding fieldName absent from its query fields.
RESULT: multi-y line/area = 0; binding mismatches = 0 (across all 8 pages). ✅

## T9 — Safety net: originals unchanged
`SHOW TABLES IN sandbox_operations.po_management` → 35 sdp_* present; all 8 originals intact
(rung2_plan_vs_actual/planned_weekly/actuals_weekly, p1flow_*×3, rootcause_plant/dc).
`rung2_plan_vs_actual` still 590,275 rows. Original dashboard 01f1a50aed891d5c85b5e64b2c3c5d5b state
ACTIVE, name unchanged. ✅ SDP build is fully parallel; nothing live was disturbed.

## Job wiring proof
Manual `jobs run-now 418760739520160` triggered pipeline update `8d6f641c-…` which reached COMPLETED
→ Job→pipeline path works end-to-end. Job left PAUSED until go-live.

## T10 — 180-day widening (both stacks) + equivalence
Window widened to 2026-03-02 (doc D4/P4 180-day backfill; cutoff ~175d, under the "do not exceed 180" cap).
SDP widened via the ONE config knob (p1.pd_lo etc.) + full-refresh — no SQL edits. Original rung2_*/p1flow_*/
rootcause_plant rebuilt from their (widened) notebooks.
```sql
-- both gold tables at 180d + per-org equivalence
SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM sandbox_operations.po_management.sdp_plan_vs_actual;   -- 2026-03-09..08-24, 924987
SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM sandbox_operations.po_management.rung2_plan_vs_actual; -- 2026-03-09..08-24, 924987
-- per-org diff rung2 vs sdp: all 0
```
RESULT: sdp gold 924,987 == rung2 gold 924,987; per-org (2012,2120) row/net-$/red diffs all 0. SDP DQ 0
violations; overview cube 980 rows (perf holds). Both dashboards redeployed with default window lower bound
2026-03-02 (11 param defaults each). Clone thin queries at new default: 25-week rollup, SLA 2 rows, cockpit
newly-red 2,236 (latest week; ~stable vs 4-mo 2,243 — newly-red is edge-sensitive, latest-week action count
holds). Gold starts 03-09 (one week after 03-02) because the prior-week baseline needs a preceding snapshot.

## T11 — SDP clone has ZERO external dependency (self-contained in the pipeline)
Parsed all 42 clone datasets: 0 references to any non-sdp_ table. The flow/timing/chronic tiles read
sdp_order_stage_gold / sdp_po_stages / sdp_rootcause_plant / sdp_agg_po_timing / sdp_agg_transitions /
sdp_exceptions — all pipeline MVs. p1flow_* is used ONLY by the original safety-net dashboard, not the clone.

## The window is now ONE KNOB (design fix)
SDP load window lives in pipeline `configuration`: p1.pd_lo, p1.pd_hi (INT yyyyMMdd), p1.wk_lo, p1.wk_hi
(DATE), p1.ledger_hi (INT), referenced in SQL via ${...}. To change the window: `databricks pipelines update
--json` with new config values + `start-update --full-refresh`. No SQL edit, no re-upload.
