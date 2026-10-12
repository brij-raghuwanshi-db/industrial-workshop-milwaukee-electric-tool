# Project Scope & Delivery — P1–P4, Waves, Completion Package

> ⚠️ **VALIDATE-FIRST — this is project *state*, not operating pattern.**
> **As-of:** 2026-08-30. **Source docs:** `customer_requirements/Actuals_Supply_Plan_Requirements.md`,
> `customer_requirements/Red_Keychain_Supply_Planning_Requirements.md`,
> `customer_requirements/01_Requirements.md` (Demand Events). **Evidence level:** the tables,
> decisions, and thresholds below marked **[req-confirmed]** are stated in those docs; items marked
> **[synthesized]** are design inference from the operating-pattern discussions and are NOT
> customer-confirmed. Nothing here is workspace-verified until you check it live.
>
> **Before building from this file:**
> 1. Re-read the current `customer_requirements/` docs — they are authoritative and may have
>    changed since the as-of date; a newer requirement always wins over this summary.
> 2. Verify **[req-confirmed]** table names, grains, and thresholds against live Unity Catalog
>    (existence, schema, `process_date` coverage) before depending on them — see
>    `lessons-and-evidence.md` (a name in a doc is "Mentioned", not "Profiled").
> 3. If confirmed, re-stamp the as-of date and raise the evidence level; if it conflicts, correct
>    this file and follow the newer source.
> 4. If the as-of date is stale (weeks old), treat the whole file as unverified until re-checked.

**Authoritative priority order** [req-confirmed — customer email]: P1 Actuals Supply Plan → P2
Supply Exceptions → P3 Demand Events App → P4 Demand Exceptions. **PO Exceptions are OUT of scope**
[req-confirmed — but this flipped once in project history; **verify it still holds**]. Use-cases
are first priority: if P2 signal emerges while doing P1, that's good — don't stop; respect the
exclusions.

> 🚧 **Write-boundary reconciliation [RESOLVED — write to sandbox].** The requirement docs name
> `prod_operations` for the Actuals derived layer (Actuals **D5**) and
> `prod_edw.staging_flat_files.expansion_dims` / `expansion_loads` for the Demand Events output.
> Those doc locations are **overridden by the project's non-negotiable guardrail**: `prod_edw` and
> `prod_operations` are **READ-ONLY**. **Decision:** write **all** of these to
> `sandbox_operations.po_management` — the Actuals derived tables AND the Demand Events
> `expansion_dims` / `expansion_loads` equivalents (e.g. `sandbox_operations.po_management.
> expansion_dims` / `…expansion_loads`) — plus Lakebase for transactional app state. Any handoff of
> the `expansion_*` output to Oracle Demand Planning Cloud Fusion happens through a **separately
> approved, governed publish step from the sandbox tables**, never a direct write into `prod_edw`.
> The guardrail is the most recent explicit instruction and wins over the docs.

## P1 — Actuals Supply Plan
**Outcome** [req-confirmed]: compare *what we planned* vs *what actually happened* so planners
quickly find root causes for week-over-week changes; replace manual multi-system reconciliation.
Monday–Sunday week; Monday-AM snapshot reflects Sunday EOD. Comparison grain = **item × org ×
week** (flows summed over the week; ending on-hand selected point-in-time).

**Confirmed sources [req-confirmed]:**
- Plan snapshot: `prod_edw.fact.20_supply_daily` (`process_date` yyyyMMdd = snapshot). Plan filter:
  `'20 Global Supply Plan'` (all orgs except 2120), `'20 Mexico Supply Plan'` (org 2120). Measures
  include on_hand, purchase_orders, planned_orders, sales_orders, shipped_sales_orders,
  total_demand, total_supply, projected_available_balance, safety_stock.
- PO receipts actual: `prod_edw.staging_oracle_fusion_erp.receiving_receipt_transactions`
  (`quantity`, `transaction_date`, `transaction_type`; grain = one receipt event).
  ⚠️ `prod_edw.fact.purchase_order_delivery` is **deprecated — do not depend on it** [req-confirmed];
  open-item O9 is to confirm the long-term receipt source — build the silver layer behind an
  interface (item_id, org, week, qty_received) so the source can be swapped.
- Sales shipped actual: `prod_edw.fact.sales_order_line_transactions` (`shipped_quantity`,
  `fulfillment_timestamp`; filter `order_type='Standard'`, shipped-line status).
- On-hand actual: `prod_edw.fact.inventory_days_on_hand` (`on_hand_qty`, `process_date` = week-end;
  on_hand is point-in-time — **do not sum across dates**).
- Dimensions: `items_scd1`, `date_scd1`, `inventory_organization_scd1`,
  `prod_operations.edw_extension.dim_series_ext_vw` (supplier/planner/lead time/std cost/MOQ),
  `supply_and_demand_plans_scd1`.

**Derived outputs [synthesized target — write to `sandbox_operations.po_management`, per
reconciliation above]:** `actuals_weekly_summary`, `planned_weekly_summary`, `plan_vs_actual`
(variance_abs, variance_pct, variance_category), `plan_accuracy_metrics`, `variance_summary`.
Reuse the existing dashboard's scaffold + window comparison pattern (two snapshots: prior-week plan
vs current-week day-0). D6 [req-confirmed]: start with day-0 snapshot values as baseline actuals,
layer transactional sources for receipt timing / shipment detail as needed.

**Confirmed thresholds [req-confirmed — refine after 4–6 weeks of data]:** PO on-time receipt
>85% (±1 wk); PO qty accuracy >90% (±10%); on-hand MAPE <15%; demand accuracy >80% (±20%);
stratify tighter for A-items (ABC code). Alert tiers: Monitor >15% variance; Alert >30% or >$50K;
Escalate >50% or >$200K or missed safety stock (A-items 10/20/40, C-items 25/50/75); cost impact
via `applied_standard_cost` from `dim_series_ext_vw`. Backfill **180 days (~26 weekly snapshots),
no more** [req-confirmed D4]; incremental weekly appends forward.

**Pipeline / semantic / dashboard / Genie / App:** weekly Lakeflow pipeline (Monday cadence,
idempotent reruns [T2], late-data handling [T3], validation + alerting [T5/T6], backfill [T7]);
metric view (planned/actual qty, abs & % variance, receipt attainment, timing, ending-inventory
variance, plan accuracy & bias, semi-additive on-hand); Phase-1 standalone AI/BI dashboard modeled
on the Supply Historical Snapshots dashboard, Phase-2 Control Tower integration [req-confirmed O7]
+ native Ask Genie; focused Actuals Genie with certified SQL, benchmark Q&A, inventory-additivity
tests; App drill-down + Ask Actuals Genie, **no PO actions/writebacks**.

**Acceptance [req-confirmed success criteria]:** one SKU-org-week reconciles source→Gold; dashboard
& Genie return the same governed metrics; plan vintage reproducible; on-hand not summed over time;
data available before 8 AM Monday [S4]; match rate vs manual >99% [S3]; planner UAT.

**Open items to carry [req-confirmed]:** O8 alerting thresholds finalization; O9 receipt-source
confirmation (EDW ticket); O10 validate `process_date` covers full 180 days *before* building the
Phase-1 pipeline (a ~5-min `MIN/MAX/COUNT(DISTINCT process_date)` check).

## P2 — Supply Exceptions (supply portion of Red Keychain)
**Outcome** [req-confirmed]: prioritized queue of meaningful supply conditions; investigate
evidence; assign/dispose; track resolution. Writes case state to Lakebase; **must not modify POs**
in *this* scope. **Prioritization = time urgency by largest unit miss** (financial impact
bookmarked) [req-confirmed B.2].

**Exception taxonomy — the doc confirms 18 types across 5 categories** [req-confirmed]. **In scope
for P2 = supply exceptions only.** Note the **verify boundary**: the 18-type list interleaves
PO-action exceptions (pull-in #3, push-out #4, new PO #5, cancel #6, past-due #12) which belong to
the excluded PO-Exceptions/ordering scope — **confirm the exact supply-vs-PO split with the owner.**
Supply-side candidates: demand exceeds supply/stockout (#1), excess vs target (#2), supplier late/
lead-time risk (#7), safety-stock violation (#8), transition risks (#9–11), lead-time drift (#13),
demand-forecast volatility (#14), DC imbalance/rebalance (#15), MOQ waste (#16), frozen-zone
violation (#17), plan-vs-actual receipt variance (#18).
**Excluded (PO/ordering execution):** PO pull-in/push-out, create/cancel PO, past-due PO queue, PO
grouping/release, Oracle PO modification, bulk PO actions.

**[synthesized] data products & Lakebase workflow:** versioned rule registry, exception detection
+ evidence facts, taxonomy dimension, lifecycle history, priority-score components, open-exception
MV, metric view, linkage to P1 evidence; Lakebase case/assignment/status/root-cause/disposition/
comment/snooze/recommendation/audit with optimistic concurrency + idempotency. Dashboard + focused
Genie (count/severity reconciliation, guardrail against claiming PO actions) + App queue (filters,
approved bulk disposition, evidence, comments, audit, writebacks, outcome tracking).
**Acceptance:** every exception → approved rule/model version; no PO Exceptions appear; repeated
evaluation creates no duplicate active cases; writebacks survive refresh + appear in audit; counts
reconcile across dashboard/Genie/App.

## P3 — Demand Events App
**Outcome** [req-confirmed]: replace the Excel process for incremental demand events (above
baseline) — non-repeating (load-in) and repeating (run-rate). **Output grain = one row per mkedg5
customer × item × month.** **Platform:** Databricks App (Streamlit prototype) [req-confirmed;
production platform is open-item #7]. **Downstream:** Oracle Demand Planning Cloud Fusion.

**Confirmed specifics [req-confirmed]:**
- **Output tables:** the docs name `prod_edw.staging_flat_files.expansion_dims` / `…expansion_loads`,
  but per the write-boundary decision above we **write the sandbox equivalents**
  (`sandbox_operations.po_management.expansion_dims` / `…expansion_loads`) and publish to Oracle
  through a governed step — never write `prod_edw` directly. Keep the doc's column contract (§8.1)
  so the sandbox tables stay publish-compatible. Only **Active** events export; **daily
  truncate-and-reload before 5 PM pickup** (incremental-merge is open-item #4).
- **EXP ID** = auto sequential `max+1`, immutable. **Three-state lifecycle:** In Progress (draft,
  not exported) / Active (exported daily) / Deactivated (soft-delete, retained). **Event locking**
  (one editor; view-only for others; released on save/close/timeout). **Audit trail** at item/
  month/field before-after.
- **Customers:** multi-select from `prod_edw.dimension.dg5_customer_scd1`; 6-level hierarchy
  (mkedg0–mkedg5, mkedg5 = output grain); **ratio-based disaggregation** to mkedg5 using measures
  from `prod_edw.fact.10_demand_daily` (`working_final_forecast`, `planner_baseline_forecast`, +4–5
  TBD — open-item #3).
- **Items:** freeform + bulk paste; validate against `items_scd1`, primary rule
  `item_status_description` = Status 20, **non-blocking warning** (open-item #1 confirms field
  logic).
- **Time:** monthly buckets; end month max = first-of-month **23 months** out. **Forecast Builder:**
  non-repeating = `#stores × Load Per Store` on start date; repeating = `#stores × ASPV` spread
  across months; header vs line-level assumptions; per-cell override on the main page.
- **Access:** all planners see all events; edit gated by lock; **no approval workflow** (planner
  submission = ready to load).

**[synthesized] Lakebase model / API / analytics / acceptance** as previously scoped (header, type,
customers, items, assumptions, monthly values, overrides, lock, publication state, field-level
audit; create/update/duplicate/activate/lock/calculate/validate/import/publish APIs; baseline-vs-
event views; Lakebase→publish reconciliation). Genie stays analytical — **it will not activate/edit
events** (typed App actions do). Acceptance: full create-to-activate workflow; concurrent editing
controlled; output expands to customer-item-month; App & publication totals reconcile; deactivated
events leave active output but retain history.

## P4 — Demand Exceptions (demand portion of Red Keychain)
**Outcome** [req-confirmed scope boundary]: focused queue of material problems across baseline
forecasts, event increments, overrides, final forecasts, and actual-demand signals. **ML only after
deterministic rules + historical evidence establish measurable need** [synthesized discipline,
consistent with req]. Candidate exceptions [synthesized from taxonomy]: significant forecast
change, actual materially different from plan, persistent bias, unusually large override, active
event with no demand, expired/invalid event, overlapping events, incorrect repeating/non-repeating
pattern, disaggregation anomaly, baseline-plus-event inconsistency, new-item signal gap. Data
products, ML deliverables (baseline model, time-based validation, segment eval, MLflow, UC
registration, batch-vs-serving, drift monitoring, champion/challenger), dashboard/Genie/App, and
acceptance as previously scoped. **Deep link to P3** when an event needs correction.

## Red Keychain scope note (P2/P4 come from one doc)
The Red Keychain doc also confirms a broader ordering/optimization program largely **beyond P2/P4**
(and overlapping the excluded PO scope): requested-vs-confirmed plans (NEW-1), rec-not-before-PO
(NEW-2), order-vs-rebalance (NEW-3), stranded-inventory pooling (NEW-4), PO grouping/sequencing +
Truckload-PaaS replacement (NEW-5/8/17), supplier forecast → Oracle SCC weekly EDI Fri-4PM freeze
(NEW-6/16), TTi-first rollout (NEW-7), probabilistic scenario simulation (NEW-9/10), tribal-
knowledge rule capture via planner interviews — Matt Michael, Dana Balog, Alyssa Bubik — (NEW-11/12/
13, "To Build"), Redwood edit-in-spreadsheet restore (NEW-14), feedback loop (NEW-18), and future
virtual-DC/postponement items (NEW-19–22). **Treat these as context, not P2/P4 build scope** unless
the owner pulls a specific item in.

## Unified planner App (one experience, no giant Agent)

```
Planner Home
├── Actuals Supply Plan   → Ask Actuals Genie
├── Supply Exceptions     → Ask Supply Exceptions Genie
├── Demand Events         → Ask Demand Events Genie
└── Demand Exceptions     → Ask Demand Exceptions Genie
```
Route questions to the active module's Agent with selected SKU/org/week/event/exception context.
(Assistant mode separation — Analyst/Investigator/Planner/Workflow/Decision/Execution — is in
`supply-chain-domain.md`.) [synthesized — the docs specify P3 as its own app and Actuals Phase-2
into Control Tower; a single unified shell is a design proposal, confirm before committing.]

## Delivery sequence (waves) [synthesized]

- **Wave 0** — validate auth & source access; **profile the confirmed P1 tables and check
  `process_date` 180-day coverage (O10)**; confirm grains & week/vintage semantics; prove SQL
  Warehouse + App + Lakebase + dashboard + Genie connectivity; establish canonical workspace
  structure; **resolve the write-boundary reconciliation and the P2 supply-vs-PO split.**
- **Wave 1** — one P1 SKU-org-week vertical slice; P1 dashboard page + Ask Genie; P1 App drill-down
  + Ask Actuals Genie; begin P2 rule discovery from P1 signals.
- **Wave 2** — productionize P1; deliver P2 detection + Lakebase workflow + dashboard + Genie; small
  P3 App/Lakebase feasibility skeleton in parallel when capacity permits.
- **Wave 3** — complete P3 Events App + event dashboard + Genie; capture P4 candidate signals.
- **Wave 4** — P4 detection + workflow; add forecasting/anomaly models only where justified;
  complete dashboard/Genie/App.

## Completion package (per priority — 20 parts) [synthesized checklist]

1. Business use case & scope · 2. Domain & metric definitions · 3. Source inventory & profiling ·
4. Grain & dimensional model · 5. Join & aggregation contracts · 6. Source-to-target mappings ·
7. Pipeline or transactional implementation · 8. UC objects & permissions · 9. Metric view &
certified SQL · 10. AI/BI dashboard with native Ask Genie · 11. Focused App Genie Agent ·
12. Genie benchmark & evaluation evidence · 13. App UI & API contracts · 14. Lakebase model where
writeback is required · 15. Data-quality & reconciliation tests · 16. Auth, security & network
validation · 17. Workspace deployment & DAB/CI-CD promotion · 18. Monitoring, runbook & recovery ·
19. Planner UAT script · 20. Evidence-backed acceptance record.

> A priority is complete only when its **deployed planner workflow passes, data reconciles, Genie
> passes its benchmark questions, required writebacks persist, errors are observable, and the
> business owner accepts the result** ("done" ≥ UAT-passed — see `lessons-and-evidence.md`).
