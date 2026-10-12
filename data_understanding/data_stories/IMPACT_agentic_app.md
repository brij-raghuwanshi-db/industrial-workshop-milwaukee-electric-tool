# Record-impact assessment — if we build the agentic AI app (all P1–P4 features)

**As-of 2026-08-30.** "If I build an agentic app with all the discussed features, which RECORDS get impacted —
good vs adverse?" Answered against the project's non-negotiable write boundary + the traced findings.

## The architecture that bounds all impact (why this is answerable)
- **`prod_edw` + `prod_operations` = READ-ONLY, always.** The app READS them; it can NEVER INSERT/UPDATE/
  DELETE/MERGE there. → **No prod EDW record can be directly harmed by the app.** This is the single biggest
  protection and it's architectural, not a promise.
- **App WRITES go only to `sandbox_operations.po_management` (derived Delta) + Lakebase (transactional state).**
  Those are NEW records the app owns.
- **External-system writeback (Oracle Fusion / Demand Planning Cloud / SCC / WMS / TMS)** goes through a
  separate, typed, approved, auditable action path — never a direct prod-schema write.
So the impact map has three zones: **READ (leveraged), WRITE-OWN (created), WRITE-EXTERNAL (real-world risk).**

## Zone 1 — Records impacted in a GOOD way (net new / enriched, low risk)

| Record class | Where | Good impact |
|---|---|---|
| Derived analytics (actuals_weekly_summary, plan_vs_actual, supply_exceptions, plan_accuracy, variance_summary) | sandbox_operations.po_management | Single source of truth for plan-vs-actual; replaces manual Excel reconciliation. Pure additive. |
| Exception cases + lifecycle (exception_case, priority scores, disposition, root-cause) | Lakebase | Exceptions get *tracked, assigned, resolved* — accountability where none existed. |
| Action & audit history (action_request, action_audit_event, approval, outcome history) | Lakebase + sandbox | Every decision becomes **traceable and reversible** — new capability, big governance win. |
| Demand events (event_draft, event_lock, comments, field-level audit) | Lakebase | Replaces the Excel event process with locking + audit; concurrent planners no longer clobber. |
| Published event output (expansion_dims/loads *equivalents*) | sandbox_operations.po_management | Governed, reproducible output vs ad-hoc spreadsheets. |
| QA / reconciliation evidence | sandbox | Proof the numbers tie out; raises data trust. |

**Also good (read-only leverage, no record changed):** all `prod_edw` facts/dims — value extracted, nothing
altered. The 20_supply_daily daily-snapshot history becomes an asset (multi-vintage "was-green-now-red").

## Zone 2 — Records impacted ADVERSELY (the real risk surface)

### 2a. External / downstream records — the ONLY place real-world harm lands
- **Oracle Demand Planning Cloud (P3 events):** if a bad event goes **Active**, the **daily truncate-and-reload
  before 5PM pickup** publishes it into the downstream demand plan. Adverse: a wrong/duplicate/mis-disaggregated
  event corrupts the corporate demand forecast — and truncate/reload means a bad run can wipe/replace **all**
  active events at once (blast radius = every active event, not one).
- **Oracle Fusion / SCC / WMS / TMS (ordering):** PO create/cancel/pull-in, supplier-forecast publish. **These
  are OUT of P2 scope (evidence-only)** — but if the ordering program (Red Keychain) wires them, a bad action
  changes a REAL purchase order or supplier commitment. Highest-severity adverse surface. Bulk actions (B.4)
  multiply it — one wrong "apply to selected" hits many POs.

### 2b. App-owned records that can be WRONG (sandbox/Lakebase) → drive bad decisions/actions
Even though these are "safe" schemas, wrong content here becomes wrong recommendations and (via 2a) wrong
external actions. Every traced data-trap is an adverse-impact vector if the agent computes on it blindly:
- **Semi-additive on-hand summed over dates** → inventory overstated 5.48× → false "healthy" → missed stockout.
- **Ranking by raw unit-miss** → agent escalates a **$0.0134 carbide part** as the top crisis (70× priority flip);
  real A-item shortages buried.
- **Wrong source table / key** → receipts joined via raw-Oracle-id fail; shipped_quantity un-filtered
  understates fulfillment 6.7× → agent "sees" a shortfall that isn't there.
- **Phantom demand / forecast≫actual** acted on → agent orders/positions stock for demand that never comes.
- **Single-snapshot reads** → agent misses the emergent flip / past-due cluster forming.
- **Non-idempotent runs** → duplicate cases/actions (T2 explicitly requires idempotency).
- **frozen_* NULL** → P4 "since last freeze" silently empty → agent under-detects drift.

### 2c. Concurrency / autonomy collisions
- **event_lock / optimistic concurrency:** agent and a human editing the same event/case → lost updates if
  locking/versioning isn't enforced.
- **Autonomous typed actions** (activate event, dispose exception, bulk-dispose) without a human gate → the
  agent's mistake becomes a committed record change at machine speed and scale.

## Zone 3 — Records that are NEUTRAL-but-must-exist (the safety rails)
- **integration_outbox / integration_result:** every external action staged + result captured → replayable,
  reversible. **This is what makes 2a survivable.**
- **notification_delivery, idempotency records, saved_search:** operational plumbing; no business harm.

## Blast-radius ranking (worst → least)
1. **External writeback to Oracle/SCC/WMS** (real POs, published forecast) — governed action path + human
   approval + audit is mandatory; keep P2 evidence-only as scoped.
2. **P3 event publish (truncate/reload to Oracle Demand Planning)** — a bad Active event or a bad run corrupts
   the downstream plan wholesale. Gate activation; prefer incremental merge over blind truncate/reload; validate
   before 5PM pickup.
3. **Wrong recommendations from data-trap bugs** — mitigated by the AP anti-pattern guardrails baked into
   certified SQL/metric views (never let the agent hand-roll semi-additive sums or raw-magnitude ranking).
4. **Concurrency / duplicate records** — locking + optimistic concurrency + idempotency keys.
5. **Sandbox derived tables** — worst case is recompute; no external harm.
6. **prod_edw / prod_operations** — **architecturally cannot be written; ~zero direct adverse impact.**

## Guardrails that convert adverse → safe (design requirements)
- **Human-in-the-loop gate** on anything that leaves Databricks or flips a state (activate event, dispose,
  bulk action, external push). Agent proposes; person (or policy) approves.
- **Typed, audited, idempotent action path** (action_request → approval → integration_outbox → result) — no
  free-form writes; every action reversible and logged.
- **Certified metric views / SQL** so the agent consumes correct-by-construction measures (semi-additivity,
  RECEIVE-only, dash-normalized keys, cost×ABC×org-role ranking) — the AP anti-patterns become impossible-to-hit.
- **Validation before publish** (row counts, referential integrity, reconciliation) — blocks a bad
  truncate/reload from reaching the 5PM pickup.
- **Genie stays analytical / read-only** — it answers, it does not activate/edit/dispose; only typed App
  actions mutate state.
- **Scope discipline:** P2 = evidence-only (no PO writes); PO ordering actions belong to the separately-approved
  program, not the exception queue.

## One-paragraph answer
Because `prod_edw`/`prod_operations` are read-only by architecture, **no production EDW record can be directly
harmed** — the app only *reads* them. The **good** impact is a large body of **new** records the app owns
(derived plan-vs-actual analytics in sandbox, and exception/event/approval/audit state in Lakebase) that
replace manual Excel work and add traceability that didn't exist. The **adverse** impact concentrates in three
places: (1) **external writeback** to Oracle/SCC/WMS and the **P3 daily publish to Oracle Demand Planning**,
where a wrong or bulk action changes real business records — mitigated by a typed, approved, idempotent,
audited action path with a human gate; (2) **app-owned records computed on a data trap** (semi-additive sums,
raw-magnitude ranking, wrong source table, phantom demand), where the fix is certified metric views so the
agent can't hand-roll the mistake; and (3) **concurrency/autonomy collisions**, fixed by locking + idempotency.
Get those rails right and the adverse surface collapses to "recompute a sandbox table," while the upside —
governed, explainable, reversible planner decisions — is real.
