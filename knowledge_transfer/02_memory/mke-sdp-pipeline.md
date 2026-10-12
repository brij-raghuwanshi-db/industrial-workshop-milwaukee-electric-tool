---
name: mke-sdp-pipeline
description: "MKE P1 SDP pipeline — parallel sdp_* tables + clone dashboard + weekly Job; pre-agg for scale; roadmap step 2 done"
metadata:
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

Roadmap step 2 (stable pipeline) is BUILT and verified for MKE P1 "Actuals Supply Plan". A Lakeflow
Declarative Pipeline `p1_actuals_sdp` (id b6f16cf7-b17e-4b08-beaa-6c8e7fb97585, serverless/triggered) writes
**35 materialized views** to `sandbox_operations.po_management.sdp_*` — a fully PARALLEL copy that never
touches the live rung2_*/p1flow_* tables or the original dashboard (01f1a50aed891d5c85b5e64b2c3c5d5b), which
stay as the safety net. 4 silver + 3 gold (source-equivalent to the existing builds, read live from prod,
zero literals) + 28 per-widget-grain serving aggregates. Weekly Job `p1_actuals_weekly_sdp` (id
418760739520160, Mon 07:57 CT, PAUSED, on_failure email) triggers it. Clone dashboard "P1 Actuals — SDP
(Rung 2)" id **01f1a5371959178aa137d5551347afff** runs THIN queries over the serving tables.

**Verified (all in `workspace_assets/SDP_VERIFICATION_LOG.md` with queries):** sdp gold == live gold EXACT
(590,275 rows, per-org $ and counts 0-diff); newly-red 2,243/$23.72M and FVA −3.7%/−11.2% identical; DQ 4
EXPECT constraints 0 violations; perf gate overview/KPI serving tables 2–160 rows (was 590,275 live →
~18,000× cut); overview cube (sdp_agg_overview, 626 rows) bit-exact after full-precision fix; 42/42 clone
datasets return rows; 0 multi-y / 0 binding breaks; originals unchanged.

**Durable learnings (apply to any pre-agg/serving layer):**
- Pre-aggregate to per-WIDGET grain and store **additive components** (sum + count), never pre-divided
  averages — the thin query does SUM/SUM to reconstruct the exact average over any filtered window.
- A Lakeview counter/bar does ONE aggregation over one field → **COUNT DISTINCT and weighted-AVG tiles
  cannot be served from a rollup**; they must read a raw (narrow) dataset. Not every tile collapses to 32 rows.
- **Never ROUND inside a serving table** — round only at display; re-summing rounded cells drifts vs base.
- A pipeline MOVES computation, it does not add data (same prod reads, materialized once).
- Weekly batch vs real-time is per-SURFACE: analytics=weekly MVs, App=Lakebase real-time. Match freshness to
  the signal's change rate; don't stream a weekly fact.

Window stays 4-month (2012+2120) for the equivalence check; widen to 180d/full-network = flip `pd_lo` +
full-refresh (verify-then-widen, user's call). Gap scorecard vs the requirement doc: `P1_STATUS.md`
(carried-forward gaps — PO-qty-accuracy%, demand-accuracy%, ABC-tiered thresholds — are pre-existing, NOT
introduced by SDP). Next: roadmap step 3, the App (Lakebase real-time state, SIMULATED writeback — no real
Oracle per [[mke-project-guardrails]]). See [[dashboard-action-not-state]], [[mke-genie-app-enablement]],
[[mke-worklog-practice]].
