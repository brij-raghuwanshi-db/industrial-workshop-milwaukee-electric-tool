# Genie Enablement — from our hand-analysis to an AI that reproduces it

> **BUILT (2026-08-31):** Genie Space **"P1 Actuals — Supply Plan vs Actual (SDP)"**, id
> `01f1a542c3f7132681b64d8ff08b4033`, grounded on 5 `sdp_*` tables (sdp_plan_vs_actual, sdp_agg_scorecard,
> sdp_exceptions, sdp_order_stage_gold, sdp_rootcause_plant). Definition:
> `workspace_assets/genie_agent.json` (8 sample Qs, 15 example SQLs, 1 merged instructions block).
> **Default behavior: every answer shows the underlying records (item_id/org/week) behind the number,
> ranked by $.** Verified via Conversation API: off-plan-by-$ returns named SKUs; the "on-hand value"
> guardrail correctly uses latest week (no cross-week sum); bias 2012 vs 2120 = 74.0% vs 28.8% (matches
> scorecard). The table names below say `rung2_`/`p1flow_`/`ds_`; the deployed Space uses the `sdp_*`
> equivalents (rung2_plan_vs_actual→sdp_plan_vs_actual, p1flow_order_stage_gold→sdp_order_stage_gold,
> ds_scorecard→sdp_agg_scorecard, + sdp_exceptions, sdp_rootcause_plant).

**Written:** 2026-08-31 · profile `mke-rsc` (adb-4482605715640778) · warehouse 7bd33a82f4e92206.
**Purpose:** the user's directive — *"note all interactions and activities we are doing, because we will need
Genie to be doing the same, but via AI, through the data we are populating from here."* This is the bridge:
every analytical move we made by hand → the **data surface**, **metric definitions**, **reasoning rules**, and
**sample Q&A** a Databricks AI/BI **Genie space** needs so a planner can ask in natural language and get the
same answers, over the *governed sandbox tables* — never raw prod.

> **Golden rule for the Genie space:** point it at `sandbox_operations.po_management.*` (our reconciled
> gold/derived tables), **NOT** at `prod_edw`/`prod_operations` raw. Every trap below was solved once, in the
> gold. Genie should inherit the solution, not re-hit the trap. Prod stays READ-ONLY and out of Genie's scope.

---

## Part A — The arc of what we did (chronological, so Genie's instructions mirror the real reasoning)

1. **Understood the domain before touching SQL** — requirements P1–P4, snapshot semantics, plan-vs-actual,
   the supply-plan vocabulary. *(Genie needs this as curated instructions + a glossary, not raw tables.)*
2. **Profiled real tables, verified every join/grain/filter** against live data — did not trust the doc map.
3. **Built a P1 vertical slice** (1 item→all items→multi-org) EDW→gold plan-vs-actual at item×org×week,
   reconciled to source, into `sandbox_operations.po_management`.
4. **Built native AI/BI dashboards** on the gold (Rung-1 + Rung-2, incl. a Cross-Org Contrast page).
5. **Added org 2120** via an org→plan mapping; killed a double-count with a single predicate.
6. **Validated: orgs are NOT interchangeable** — 2 logged subagents + my re-verification; found the logic
   generalizes but the *judgement* (thresholds/bias/comparisons) must be org-aware.
7. **Corrected our own errors when data refuted them** (three times — see Part D). This discipline is the
   single most important thing to transfer to Genie.
8. **Explored unexplored metadata** → found the network/flow tables; built the **order-lifecycle / stage-timing
   slice** with org-aware timing bands, recommended maneuvers, and a chronic-slipper signal.

---

## Part B — The DATA SURFACE Genie reasons over (all in `sandbox_operations.po_management`)

| Table | Grain | What it answers | Key columns |
|---|---|---|---|
| `rung2_plan_vs_actual` | item × org × week | plan-vs-actual on-hand, variance, status, alert tier, bias | organization_code, plan_name, week_start, planned_pab, actual_end_on_hand, onhand_variance_abs/pct/dollar, onhand_status, alert_tier, planner_name, abc, wow_onhand_delta |
| `p1flow_order_stage_gold` | item × org × order × lane × stage | order-lifecycle timing, preemptive maneuvers, chronic slip | lane (transfer/purchase), slip_days, timing_band, recommended_maneuver, chronic_pct_late, chronic_avg_err_days, supplier_name |
| `p1flow_transfer_stages` | receipt line (2012) | transfer transit/slip detail | transit_days, slip_days, source_org→dest_org, qty_short |
| `p1flow_po_stages` | PO receipt line (both orgs) | PO lead-time error detail | slip_days, late_flag/early_flag, supplier_name, lead-time days |
| (Rung-2 dashboard datasets `ds_*`) | various rollups | pre-shaped question answers | see rung2_dashboard.json |

**Provenance (Genie should cite, not re-derive):** on-hand plan/actual from `prod_edw.fact.20_supply_daily` +
`inventory_days_on_hand`; receipts `purchase_receipt_line`; shipments `sales_order_line_transactions`; transfer
lifecycle `prod_operations.manufacturing_sc.fact_transfer_order_receipt`; **PO timing**
`prod_operations.features.general_historical_purchase_order_lead_time_errors`; cost `dim_series_ext_vw`;
org/plan mapping (2120→'20 Mexico Supply Plan', else '20 Global Supply Plan').

---

## Part C — The REASONING PLAYBOOK Genie must encode (as space instructions + metric definitions)

These are the rules we applied by hand. In Genie they become **curated instructions**, **certified metric
definitions**, and **SQL example queries** so the model doesn't reinvent (or mis-invent) them.

1. **Semi-additive on-hand: NEVER SUM across dates.** On-hand is point-in-time (week-end value). Flows
   (received/shipped) sum; stock does not. (The 538,116-vs-83,254 trap.) → encode as a certified measure;
   forbid `SUM(on_hand)` in instructions.
2. **Org is a judgement context, not just a filter.** Thresholds/bands must be **org-relative** (percentile
   or per-org config), because 2012 is ~24× larger; a fixed $200K escalate never fires at 2120. Bias
   magnitude differs ~5× (both over-plan; 2012 harder — NOT "inverted"). → per-org logic, never one global cut.
3. **Grain discipline / no double-count.** Cross-org "same item" comparisons INNER JOIN on the 5,717 shared
   SKUs (2120 is 41% Mexico-exclusive). 2120 appears under both plans in raw fact → the org→plan predicate
   prevents double-count. Transfer receipt fact fans out 1.45× → dedup to receipt-line grain.
4. **Filter traps:** shipments need `order_type='Standard'` + status IN ('Invoiced','Closed') + qty>0.
   `purchase_receipt_line.expected_receipt_date` is a MIRAGE (same-day) — use the historical lead-time table
   for PO timing.
5. **Timing → preemptive, not reactive.** Band slip within each lane×org's own distribution; recommend a
   maneuver (Expedite/Defer/Monitor/Reorder); cross with **chronic slip** to tell systemic (fix the supplier)
   from one-off (expedite this order). 2120: 76% of expedite candidates are chronically-late suppliers.
6. **Org roles differ:** 2012 = transfer hub (19 source orgs); 2120 = directly-sourced leaf (Buy/Make, zero
   transfers). Don't flag a hub's low ship-rate as a miss.
7. **Verify before asserting; correct when refuted.** (Part D.) Genie should prefer certified measures and,
   when uncertain, say so rather than fabricate a number.

---

## Part D — Errors we caught (Genie must be built so these can't recur)
Each was a plausible-but-wrong claim killed by checking data. The gold tables bake in the fix so Genie
inherits the corrected version:
- **"Inverted bias"** (subagents) → refuted by a row-sign test; both orgs over-plan. Gold stores signed
  variance; instructions frame it as magnitude.
- **"2120 fed by transfer from 2012"** → refuted; 2120 has zero transfers. `org_role` encodes hub vs leaf.
- **"PO 21%/60% late"** → my probe bug (raw-timestamp diff); real signal is the historical lead-time table.
  Gold's PO lane uses the correct source.

---

## Part E — Genie space build recipe (fit-for-purpose; the databricks-genie-agents skill governs the how)
1. **Scope:** a Genie space on `sandbox_operations.po_management` with **only** the gold tables above
   (`rung2_plan_vs_actual`, `p1flow_order_stage_gold`, and the detail lanes). Not prod.
2. **Certified measures / metric views** for the semi-additive + org-relative rules (on-hand point-in-time;
   variance %/$; org-relative bands; slip; chronic %). Prefer a UC **metric view** so "define once" holds.
3. **Curated instructions** = Part C verbatim + the glossary (plan-vs-actual, PAB, safety stock, alert tier,
   timing band, maneuver, chronic slipper, org role).
4. **Example (benchmark) Q&A** — seed from the **full question bank**:
   [GENIE_QUESTION_BANK.md](GENIE_QUESTION_BANK.md) — every question our observed scenarios (S1–S9, G, R, V,
   T, C, RW, LG, EM, N, O, P, AP, HOP/STATE/QTY, GEO, 2120, flow) imply a planner will ask, each tied to the
   answering table/measure and the expected answer/gotcha, PLUS the guardrail (wrong-if-naive) questions.
   Seed the ★ rows as benchmarks; a few anchors:
   - "Which items at 2120 are off-plan this week, ranked by dollar impact?"
   - "Compare plan bias between 2012 and 2120." (expect: both over-plan, 2012 ~5×)
   - "Which purchase orders should we expedite, and which are chronically-late suppliers we should fix
     instead?" (the 76% overlap story)
   - "Show orders arriving too early we could defer or downsize."
   - "Is 2120 a transfer hub?" (expect: no — directly-sourced leaf)
   - "What's the on-hand value by org?" (must NOT sum on-hand across dates)
5. **Guardrails:** READ-ONLY; answer only from the sandbox gold; cite provenance; if a measure isn't
   certified, say it's uncertain rather than compute a raw-table number that might hit a known trap.
6. **Evaluation:** run the benchmark Q&A through MLflow eval / LLM-judge against our known answers before
   trusting it (matches the project's "done = reconciled/UAT-passed, not deployed" rule).

---

## Part F — Human activity → Genie equivalent (the mapping the user asked for)
| We did (by hand) | Genie does (via AI) | Backed by |
|---|---|---|
| Profiled tables, verified grain | Answers from certified gold; grain pre-solved | gold tables + metric views |
| Applied org-aware thresholds | Reads org-relative measures / per-org config | Part C rule 2; threshold_config (planned) |
| Reconciled source→gold | Trusts certified measures; cites provenance | Part B provenance |
| Cross-org contrast (relative terms) | Answers comparative NL questions | rung2 + example Q&A |
| Preemptive maneuver + chronic slip | Recommends action & systemic-vs-one-off | p1flow_order_stage_gold |
| Caught & corrected wrong claims | Prefers certified measures; flags uncertainty | Part D + guardrails |

**Bottom line:** the tables we populate ARE Genie's knowledge; the rules we applied ARE its instructions; the
answers we proved ARE its benchmark. Build the space on the gold, encode Parts C–D as instructions, seed
Part E's Q&A, evaluate before trusting. This note is the source-of-truth for that build.
