# P1FLOW — Order-Lifecycle / Stage-Timing Slice (Rung 1) — Build Log & Evidence

**Built:** 2026-08-31 · profile `mke-rsc` · warehouse 7bd33a82f4e92206.
**READ-ONLY** on `prod_edw`/`prod_operations`; **writes only** to `sandbox_operations.po_management.p1flow_*`
(NEW assets; nothing existing touched/deleted).
**Purpose:** move from reactive "did it arrive on time? (one threshold)" to **preemptive** — per-order
expected-vs-actual with **org-aware timing bands** + a **recommended maneuver**, and a **chronic-slipper**
signal that separates a one-off miss from a systemic supplier problem. Design note:
`data_stories/org2120_validation/D_network_flow_tables.md`.

## Two lanes, because the two orgs move goods differently (verified)
- **2012 = transfer hub** — inter-org transfer network (395,940 "Transfer from" sourcing rules, 19 source
  orgs). Lifecycle from `manufacturing_sc.fact_transfer_order_receipt`.
- **2120 = directly-sourced leaf** — ZERO transfers; Buy/Make only. Lifecycle from PO history.
- Honest stage ladder = **ordered → in-transit → received**. The 5-gate vision (accept/putaway as separate
  timed stages) is NOT built — `receipt_accept_date` 0% populated, putaway 0 days. Not inventing gates.

## Assets produced (all NEW)
- `p1flow_transfer_stages` — 2012 transfer lane; **19,024 rows == 19,024 distinct receipt lines** (deduped).
- `p1flow_po_stages` — PO lane both orgs; 2012 1,616 / 2120 5,022 rows == distinct grain.
- `p1flow_order_stage_gold` — unified long-format (item×org×order_ref×lane×stage), org-aware `timing_band`,
  `recommended_maneuver` (+reason), chronic-slip enrichment. 25,662 rows.

## CRITICAL data correction found during reconcile (why we don't build on a mirage)
- **`prod_edw.fact.purchase_receipt_line.expected_receipt_date` is unusable for timing** — it equals
  `receipt_creation_date` on the **same calendar day 100%** of the time (0.0% differ, both recent & older
  windows). My earlier probe claim "2012 21% / 2120 59.6% late" was a **probe bug** (diffed raw timestamps →
  same-day time-of-day counted as "late"). Discarded.
- **Real PO timing** = `prod_operations.features.general_historical_purchase_order_lead_time_errors`:
  `requested_delivery_date` vs `delivery_date` (**89–92% differ** — genuine), `lead_time_error_days`
  precomputed. Recent-window: **2012 48% late / 44% early (err −104..+187d); 2120 80.6% late (err −10..+41d)**.
  This one table serves BOTH the PO lane and the chronic-slipper enrichment.
- `order_date_adjusted_during_P2` (a re-promise flag) is **0% populated** — NOT used. True re-promise /
  expected-date-slip history is a **Rung-3 accrual** (weekly pipeline stamps snapshots forward), NOT a
  hand-built SCD2 (none exists on these facts; only a `valid_partition` load flag). Building SCD2 now = the
  over-engineering the user asked me to avoid.

## Verification — done ≥ reconciled (all PASS)
1. **Grain / no fan-out — PASS.**
   - transfer: 167,038 raw receipt rows → **1.45× fan-out** vs 114,901 distinct `receipt_line_bigint_key`;
     QUALIFY ROW_NUMBER dedup → gold lane **19,024 rows == 19,024 distinct receipt lines**.
   - PO: rows == distinct (order_line × receipt_number × receipt_line).
   - item join 1:1 (0 null items in both lanes).
2. **Source→gold tie — PASS (exact).** gold avg slip == source-lane avg slip to 3 dp:
   transfer_2012 **7.159 == 7.159**; po_2120 **5.375 == 5.375**. No transformation drift.
3. **Org-aware bands — PASS.** Band edges are per lane×org (percentile-based). 2120-PO's late-skewed
   distribution yields NO "1 Early" bucket while 2012-PO has a full early/late spread — same code, different
   cut-points per org (the org-relative-threshold lesson, applied to TIME).
4. **Guardrail — PASS.** Every prod reference SELECT; every write `sandbox_operations.po_management.p1flow_*`.
   Write privilege smoke (create+drop `p1flow_smoke`) passed; smoke table dropped.

## What the slice shows (the preemptive payoff)
- **Action queue:** 2012 6,828 / 2120 1,098 orders carry a non-None maneuver (Expedite/Defer/Monitor/Reorder).
- **Chronic vs one-off (the decision upgrade):** of 2120's **453 "Expedite" orders, 345 (76%) are ALSO
  chronically-late items** (supplier ≥60% late historically) → systemic supplier problem, not a one-off;
  the real fix is source-side, not per-order expediting. At 2012 only 76 overlap → its expedites are more
  genuinely one-off. This separation is the individual-level, better-decision signal, and it required the
  historical lead-time-error table (surfaced by the user's SCD2/history prompt).
- **2120 supply base is concentrated & unreliable:** 5,022 PO lines across only **3 suppliers**, 80.6% late.

## Scale path (Rung 2/3 = filter-widening, not rewrite)
Window/org list/lane are the only parameters; aggregation is set-based at stage grain with dedup + date keys
already present → weekly incremental MERGE works unchanged when widened to all orgs / full year. Org-aware
bands should read a per-org config (same `threshold_config` idea as the 2120 synthesis). Re-promise history
accrues via the pipeline stamping snapshots weekly (Rung 3), not a backfill.

## NOT in this slice (unchanged from approved plan)
No dashboard page yet (decide next). No live/open-order queue (needs open-backlog source — transfer shipments
are all `Closed`; these are completed-event facts, not live track-and-trace). No accept/putaway stages (empty).
No hand-built SCD2. No Oracle writeback / action execution. No pipeline.

## Open items for the business owner (non-blocking)
Which maneuvers are actionable & who executes them; is there an open-order backlog table for a live past-due
queue; confirm `requested_delivery_date` is the right "plan" datum; percentile cut-points for the bands;
add $-weighting (applied_standard_cost) to rank the action queue by dollars — deferred, easy add.
