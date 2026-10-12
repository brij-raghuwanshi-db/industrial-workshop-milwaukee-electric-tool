# Milwaukee Supply-Chain Domain Knowledge

Understand the business *before* coding. Milwaukee Electric Tool (Milwaukee Tool), part of
Techtronic Industries (TTI), runs Oracle-based planning (Oracle Fusion / Oracle SCC). Bring
patterns from manufacturing, retail, automotive, industrial distribution, and logistics — but
present outside ideas as **candidate patterns** (why it might help, data required, assumptions,
risks, a small proof-of-value, accept/reject criteria), and never assume a familiar metric has
the same definition inside Milwaukee.

## Supply-chain domains to reason across

Demand planning & forecast accuracy · sales orders/backlog/allocation/fulfillment · purchase
orders & supplier commitments · supplier delivery/lead-time/quality/risk · raw materials,
components, subassemblies, finished goods · BOM/routings/work orders/production · capacity,
schedule adherence, downtime, yield, scrap, rework · inventory position/availability/safety
stock/E&O · warehouse receipts/movements/picks/packs/shipments · transportation/carrier/freight
· DCs/dealers/retailers/customers/channels · returns/warranty/repair/reverse logistics · product/
battery-platform/tool-family/kit/accessory compatibility · cost/PPV/landed cost/working capital ·
control tower / exceptions / recommended actions.

## Snapshot semantics (foundational)

A **snapshot** is an immutable record of what was known/expected/possessed at a cutoff time.
A snapshot is *"what was believed at the time"*; an **actual transaction** is *"what occurred."*
A current snapshot must never silently overwrite a historical one — that destroys the ability to
measure plan accuracy, stability, and decision quality.

Milwaukee uses a **Monday–Sunday planning week**; the Monday-morning snapshot represents the
prior end-of-day state; snapshot version identity is at **SKU × organization × week** grain.

Distinguish these dates: **snapshot date** (when captured) · **target date/week** (future period
planned) · **actual-event date** (when a receipt/shipment/adjustment happened) · **comparison
date** (cycle performance is evaluated against).

Snapshot types: plan-vintage · inventory · order (open PO/SO/WO/transfer) · supplier-commit ·
exception · decision · live-plan. (Actual transactions are events, not snapshots.)

## Week-over-week means several different things — name it

| Comparison | Business question |
|---|---|
| Plan vs plan | How did the expectation for the *same* target week change between snapshots? |
| Plan vs actual | Did what happened match the previously frozen expectation? |
| Actual vs actual | Is operational performance improving week to week? |
| Current plan vs prior plan | What changed across the whole forward horizon? |
| Target vs actual | Did performance meet the approved goal? |
| Confirmed vs requested | Did the supplier commit to what Milwaukee requested? |

**Same-bucket comparison** (real plan movement): same target week across different snapshot dates.
**Rolling-week comparison** (different target weeks) is NOT a plan change — don't label it one
unless the periods are truly comparable.

## Plan vs actual — compatible semantics per measure

| Measure | Planned value | Actual value |
|---|---|---|
| PO receipts | Qty expected in target week | Qualifying receipt txns that week |
| Receipt timing | Expected receipt week/date | Actual receipt week/date |
| Customer shipments | Planned shipments for target week | Actual shipped fulfillment qty |
| Ending inventory | Prior projected ending PAB | Actual on-hand at agreed week-end cutoff |
| Supplier commitment | Requested qty/date | Supplier-confirmed qty/date |
| Demand | Previously frozen demand plan | Agreed actual-demand signal |

## Gap / variance vocabulary (use precisely)

| Term | Meaning |
|---|---|
| Variance | Signed difference `Actual − Reference` |
| Absolute variance | Magnitude, ignoring direction |
| Percent variance | Difference relative to reference |
| Gap to target | Amount still needed to reach a desired target |
| Shortfall | Amount below a minimum / higher-is-better target |
| Excess | Amount above a maximum / inventory target |
| Attainment | `Actual / Target` (percentage of target achieved) |
| Deviation | Distance from an exact target |
| Miss to plan | Business-friendly unfavorable plan variance |
| Within tolerance / Off target | Inside / outside an approved range |
| At risk | Not yet missed, but projected to breach |
| Breach | A hard constraint/threshold violated |

**Direction matters — never equate positive variance with "good."** Classify by the metric's
desired direction:
- Higher-is-better (fill rate, on-time %, forecast accuracy): `shortfall = max(0, Target − Actual)`.
- Lower-is-better (forecast error, late orders, excess, expedite cost): `overage = max(0, Actual − Target)`.
- Exact target (target ending inventory, planned receipt qty): report signed variance AND
  `|Actual − Target|`; direction still matters (below = service risk, above = working-capital/E&O).
- Target range: `shortfall = max(0, Lower − Actual)`, `excess = max(0, Actual − Upper)` — good for
  safety stock/coverage so planners don't react to harmless noise.

Percentage-point vs percent: 85% vs 78% is **7 percentage points**, not "7%."

## Goal-status vocabulary (five states)

On target · Within tolerance · At risk · Target missed · Critical breach. Use **at risk** for
projected future misses; use **target missed** only after the performance period is complete.

## Safety-stock gap

```
Safety-stock gap = PAB − Safety Stock
Shortfall units  = max(0, Safety Stock − PAB)
```
Negative gap = PAB below safety stock; increasingly negative = worsening shortage risk. Present
usefully: *"500 units below safety stock beginning week 36; estimated duration: three weeks,"*
not a bare `-500`.

## Plan stability (plan nervousness)

Measure: absolute & percent plan change by target week; number of revisions to the same target
period; directional reversals; changes inside the frozen zone; requested-vs-confirmed movement;
POs pulled in then pushed out; post-freeze allocation changes; expedite actions from late
changes. Evaluate by horizon: frozen/immediate · near-term execution · tactical · long-term. A
big change far out may be fine; a small change inside the supplier/execution fence may be
critical. Requirements call for frozen-zone violations, post-freeze change tracking, and decision
fences to prevent allocation churn.

## Dashboard presentation convention

Per important KPI aim to show: `Actual | Plan | Target | Variance | Gap | Attainment` and
`Status | Prior week | Trend | Forecast | Root cause`. Visual rules: neutral colors for ordinary
plan movement; green only when direction is genuinely favorable; amber for at-risk/warning; red
for missed/breach; arrows labeled with meaning ("improving"/"worsening"), not just up/down;
tooltips showing snapshot date, target period, formula, grain, cutoff.

## Analytical modeling discipline

Establish business process, grain, keys, and history *before* creating facts/dimensions — don't
create dims/facts just because sources have dim-like/fact-like names. For each fact document:
exact grain; additivity; business & surrogate keys; event time vs processing time; currency &
UoM handling; late-arriving dims/facts; corrections/cancellations/deletes; required SCD behavior;
source-of-truth & reconciliation totals; intended metrics & consumers.

Candidate facts: inventory periodic snapshot; inventory movement; PO line; supplier shipment/ASN
line; receipt line; work-order operation; production output; quality inspection; sales-order
line; order-fulfillment accumulating snapshot; shipment line; forecast snapshot; demand history;
return/warranty claim; repair event; supplier scorecard snapshot. Conformed dims: date, time,
product, SKU, component, facility, warehouse, storage location, supplier, customer, channel,
geography, carrier, employee, reason code, order status, org hierarchy.

Semantic layer: don't let each dashboard/Genie redefine inventory/backlog/on-time/forecast
accuracy — put reusable definitions in governed views or UC Metric Views. E.g. "inventory
availability" must state: on-hand vs ATP; inclusion of quality-hold/blocked stock; treatment of
inbound supply; facility/network scope; UoM; as-of timestamp; product supersession; whether
backorders/allocations reduce availability.

## Project priorities (P1–P4) — provisional posture

| Priority | Likely initial posture |
|---|---|
| **P1 Actuals (Supply Plan)** | Profile with notebooks/SQL; build aligned Silver & Gold; orchestrate with a Job; dashboard + companion Genie; consider SDP after incremental behavior & semantics validate |
| **P2 Supply Exceptions** | Versioned deterministic rules; append-only evidence; Job or pipeline per cadence; dashboard first; Lakebase/App when case disposition begins |
| **P3 Demand Events App** | Databricks App + Lakebase for edits, locking, approvals; Delta for publication history; Job/pipeline for validated publication |
| **P4 Demand Exceptions** | Discover real rules first; preserve forecast vintage; deterministic baseline; add ML only when it demonstrably improves decisions |

Provisional — final decisions must reflect actual Milwaukee data, resources, operating model, and
constraints. P1 Actuals does **not** need an ML model just because forecasting is planned
elsewhere; forecasting belongs where prediction changes a decision and beats an accepted baseline.

## Control tower — actionable, not a one-way dashboard

The product is a **planner workbench** implementing a closed loop:

```
Detect → Explain → Simulate → Propose → Review → Approve/deny/edit
      → Execute or publish → Verify → Measure outcome → Improve
```

Surfaces: control tower (attention now) · exception queue · investigation (actual-vs-plan root
cause) · scenario studio · action workbench · event manager · search workspace · outcome view.

**Lakebase = transactional action-control plane; Delta = analytical history.**

```
UC + Delta (plan snapshots, actuals, forecasts/events, exception evals, context, outcomes)
      → FastAPI policy & orchestration
      → Lakebase (work queues, saved searches, drafts/overrides, comments, record locks,
                  approval workflow, action commands, idempotency, external status, audit)
      → Oracle Fusion / SCC / WMS / TMS / notifications
      → Verification & outcome publication back to Delta (sandbox_operations.po_management)
```

## Writeback command pattern (e.g. "change PO qty 10 → 20")

Implement as a governed **command**, not a direct table edit. Planner may accept, change to a
permitted value, pick a reason code, enter a required comment, choose date/supplier/DC, save
draft, submit, approve/deny if authorized, convert to a rebalance/transfer, or add to a bulk
release group. Write an immutable command + audit event in Lakebase:

```
action_request(action_request_id, action_type, status[DRAFT/SUBMITTED/APPROVED/EXECUTING/
  SUCCEEDED/FAILED], business_key, proposed_quantity, original_quantity, reason_code,
  planner_comment, source_exception_id, policy_version, requested_by, requested_at,
  record_version, idempotency_key, external_correlation_id)
action_audit_event(audit_event_id, action_request_id, event_type[CREATED/EDITED/APPROVED/DENIED/
  SENT/VERIFIED], actor, actor_identity_type, before_state, after_state, occurred_at, trace_id)
```

The UI reflects the Lakebase transaction immediately; it does NOT claim Oracle changed until the
external call is verified. A background action service/Job then: validate latest record version +
rules + policy + approval → write outbox record → call approved Oracle API → record request/
response correlation IDs → retry only when contract + idempotency make retry safe → read back /
await confirmation → mark SUCCEEDED/FAILED/VERIFICATION_PENDING → publish outcome to Delta →
recompute affected views/exceptions. This avoids the duplicate-order/duplicate-alert trap of a
web request making a non-idempotent external call that times out and retries.

## Writeback taxonomy (classify before implementing)

| Type | Example | Lakebase | Delta | Operational system |
|---|---|---|---|---|
| Personal workflow | Bookmark exception | Primary | Optional history | None |
| Collaborative workflow | Assign planner, comment | Primary | Auditable copy | None |
| Planner input | Demand event / forecast override | Draft/lock/audit | Published history | Export/API to Oracle |
| Recommendation disposition | Accept/deny/revise | Primary | Decision-learning history | Optional follow-on |
| Transaction request | PO expedite / qty change | Command+approval+idempotency | Command/outcome history | Execute after approval |
| External notification | Alert supplier owner | Command/status/audit | Notification analytics | Send email/Teams/webhook |
| Exception resolution | Mark resolved w/ reason | Primary | Outcome metric | Optional source action |
| Master-data request | Fix MOQ/lead-time | Ticket/workflow | Quality-trend analysis | Master-data workflow |
| Scenario | Save simulation | Scenario metadata/inputs | Scenario snapshots/results | None unless promoted |

Also consider Lakebase search (BM25) for finding exceptions/POs/suppliers/SKUs/events/comments —
with follow-on actions on click — as an alternative to Vector Search where the target is
structured operational records rather than narrative knowledge. (Search & sync mechanics:
`fit-for-purpose-decisions.md`.)

## Two closed loops

- **Operational loop:** planner action → Lakebase transaction → App reflects draft/approved/
  executing state → external system confirms → impacted exception re-evaluates → queue/trend
  refresh.
- **Analytical loop:** Lakebase action/outcome → Delta action-history projection → updated facts/
  forecast/plan snapshots → metric recomputation → dashboard/Agent use the new evidence → MLflow
  captures recommendation & outcome → future quality improves.

Product-specific decisions to settle deliberately: synchronous vs Oracle-batch plan updates;
approved simulation vs published plan vs confirmed Oracle state; incremental exception
recomputation; real-time vs hourly/daily metric refresh; stale-data behavior during outages.

## Impact states (don't claim improvement early)

Distinguish **proposed → approved → executed → verified → realized** impact. Do not claim a
business improvement until confirmed by read-back or downstream actuals. A trace/transaction that
"succeeded" is not proof the external action committed or that the outcome improved.

## Nervous-system model & hybrid intelligence

The initiatives form one supply-chain "nervous system": **Actuals = memory** (planned vs
occurred); **Exceptions = perception** (what needs attention); **Demand Events = new signals**
(what may alter future demand); **Red Keychain = decision support**; **Lakebase = operational
memory** (cases, approvals, feedback, action state); **authorized integrations = the hands**.

Keep deterministic logic separate from LLM explanation:

```
trusted data → deterministic exception rule → ranked exception → validated recommendation/scenario
  → agent explanation → planner review → typed action proposal → approval → trusted execution
  → verification
```

The LLM never invents variance thresholds, MOQ rules, lead-time policies, plan versions, supplier
constraints, approval requirements, or PO changes — those come from governed data, versioned
rules, validated models, and authorized tools. (Full deterministic-vs-AI split:
`fit-for-purpose-decisions.md`.)

## Assistant mode separation (not one giant agent)

The capabilities have fundamentally different interaction patterns — Actuals is read/analytical;
Demand Events is transactional/stateful/write-heavy; Red Keychain is exception-driven with
controlled actions. Support distinct bounded modes, each with its own latency/state/data/authz/
evaluation/failure profile:

- **Analyst** — what happened?
- **Investigator** — why did it happen?
- **Planner** — what should change?
- **Workflow assistant** — create & validate an event.
- **Decision assistant** — recommend an action.
- **Execution assistant** — prepare, approve, execute, verify an authorized action.

## Feedback quality (a rejected recommendation isn't necessarily wrong)

Planners know constraints the platform may not. Capture structured rejection reasons — supplier
constraint not represented, promotion not loaded, transition rule missing, MOQ/truckload
constraint, customer commitment, data-quality issue, arrived too late, planner preference, system
limitation, valid-but-deferred — to turn tribal knowledge into candidate rules/features/DQ
requirements, rather than treating every click as an ML label.
