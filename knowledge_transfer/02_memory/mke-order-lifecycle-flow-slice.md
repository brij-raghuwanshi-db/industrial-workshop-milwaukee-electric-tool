---
name: mke-order-lifecycle-flow-slice
description: "p1flow order-lifecycle slice: order-timing tables, the expected-date mirage, chronic-slipper signal"
metadata:
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

Built 2026-08-31 (READ-ONLY prod; writes to `sandbox_operations.po_management.p1flow_*`): an order-lifecycle
/ stage-timing slice for **preemptive** action (expected-vs-actual per stage, org-aware timing bands,
recommended maneuver, chronic-slipper signal) — a NEW fact distinct from the P1 on-hand plan-vs-actual.

**Tables (verified populated):** `p1flow_transfer_stages` (19,024; 2012 transfer lane), `p1flow_po_stages`
(6,638; both orgs), `p1flow_order_stage_gold` (25,662; unified long-format item×org×order×lane×stage with
timing_band, recommended_maneuver, chronic_pct_late).

**Key data facts learned (verify before reuse):**
- **`prod_edw.fact.purchase_receipt_line.expected_receipt_date` is a MIRAGE for timing** — equals
  receipt_creation_date same-day 100%. Real PO timing = `prod_operations.features.
  general_historical_purchase_order_lead_time_errors` (requested_delivery_date vs delivery_date, 89–92%
  differ, `lead_time_error_days` precomputed; 13mo@2012 / 3yr@2120). `order_date_adjusted_during_P2` is 0%
  populated (don't use).
- **`fact_transfer_order_receipt` fans out ~1.45×** (167,038 rows vs 114,901 distinct receipt_line_bigint_key)
  → dedup with QUALIFY ROW_NUMBER before aggregating.
- **Only 2 real stages populated**: receipt_accept_date 0%, putaway 0 days → honest ladder is
  ordered→in-transit→received, NOT a 5-gate flow. No live "where is it now" feed (shipments all Closed).
- **No SCD2 on these facts** (only valid_partition load flag) → don't hand-build snapshot history;
  re-promise history is a Rung-3 accrual (pipeline stamps weekly).

**Signal that made it valuable:** cross timing_band with chronic_pct_late → 2120 has 345/453 (76%) of
"expedite" orders on chronically-late suppliers = systemic (fix the source), vs 76 at 2012 = one-off. 2120's
PO base is 3 suppliers, 80.6% late. Reinforces [[mke-orgs-are-not-interchangeable]]. Build log:
`data_understanding/workspace_assets/P1FLOW_BUILDLOG.md`; network-table discovery:
`data_understanding/data_stories/org2120_validation/D_network_flow_tables.md`. See [[mke-data-profiling-facts]].
