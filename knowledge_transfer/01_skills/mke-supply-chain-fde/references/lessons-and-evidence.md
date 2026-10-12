# Lessons Learnt, Evidence Discipline & Definition of Done

Distilled from execution retrospectives of prior Milwaukee work. Purpose: **do not repeat the
mistakes; treat past work as reference, not gospel.** These are lessons to prevent recurrence —
not fixed rules that forbid a better approach when current evidence supports it.

## The core failure pattern

> Too many horizontal platform assets were built before one end-to-end user workflow was proven.

Recurring symptoms observed:

- **Asset creation replaced product validation** — pipelines/tables/dashboards/Genie/ML/Lakebase/
  APIs/UI existed before one complete user journey worked.
- **Deployment became the test loop** — packaging, TypeScript, config, resource, and runtime
  problems were found only after repeated workspace deploys, not local builds/smoke tests.
- **Configuration followed implementation** — warehouse, Lakebase, Genie, endpoints, auth,
  permissions resolved only after code already depended on them.
- **Front-end failures were hidden** — swallowed exceptions and generic "setup" messages concealed
  real API/dependency failures.
- **Completion declared too early** — "created / deployed / running / integrated / UAT-passed"
  were treated as interchangeable.
- **UI capability described but not demonstrated** — controls without durable transactions,
  read-back, metric updates, or proven model/Genie integration.
- **Architecture changed reactively** — experiments became endpoints; deploy dirs duplicated;
  resource strategy changed after failures.
- **Status lived in the conversation** — constant re-audits and huge context summaries because
  there was no small, evidence-backed execution ledger.

Counter-pattern is the build order in `frontend-fullstack.md`
(probe → walking skeleton → one vertical slice → validate → add intelligence → add live actions →
harden & promote).

## Recurring mistakes register (watch for these)

- Reading incomplete requirement copies and treating missing sections as missing requirements.
- Building a broad inventory and treating every discovered object as in scope.
- Creating shape-compatible **stub/mimic tables** without clearly distinguishing them from fully
  captured schemas or real Milwaukee sources.
- Treating agent-reported row counts as validated current facts.
- Overstating completion because notebooks/jobs/dashboards exist.
- Allowing an App or dashboard to **recompute** business metrics (metrics belong in the governed
  semantic layer, not the presentation layer).
- Introducing attractive features before trusted Gold data exists.
- Treating proposed KPI thresholds as Milwaukee policy.
- **Summing inventory snapshots across time** (snapshots are point-in-time, not additive).
- Silently choosing one receipt/plan source among several.
- Full-scanning very large planning tables without early filters.
- Confusing demand accuracy (P4) with supply-plan execution (P1).
- Treating P1 supply variance as a P4 demand exception.
- Letting older APOM/PO / Red Keychain concepts leak back into corrected scope (PO Exceptions
  remain excluded).
- Debugging auth by trying random credentials instead of identifying target host, actor,
  protocol, and running process methodically.

## Evidence-level ladder (label every claim)

Never let "found in a chat," "seen in a mimic," "profiled in Milwaukee," and "accepted by the
planner" become interchangeable.

| Level | Meaning |
|---|---|
| Mentioned | An object/rule appears in a document |
| Discovered | Its current existence was observed |
| Accessible | An identity successfully accessed it |
| Profiled | Schema and meaningful data behavior were examined |
| Semantically validated | Business meaning, grain, and treatment were confirmed |
| Accepted for prototype | Approved for a bounded demonstration |
| Reconciled | Results matched trusted business evidence |
| UAT accepted | Intended users approved the workflow |
| Production approved | Security, reliability, and operating requirements passed |

A schema captured in an old chat is **not** current metadata. A generated mimic table is **not** a
Milwaukee source. A successful job run is **not** business reconciliation.

## Status vocabulary & definition of done

| Status | Meaning |
|---|---|
| Implemented | Code/asset exists |
| Component-tested | Works in isolation |
| Integrated | Connected to its real dependencies |
| Deployed | Running in the target environment |
| Functionally verified | Representative end-to-end test passed |
| UAT-passed | User workflow & acceptance criteria passed |
| Production-ready | Security, operations, recovery, deployment controls passed |
| Blocked | Cannot proceed; reason and owner identified |

**"Done" means at least UAT-passed, not merely deployed.** Report status honestly: designed /
implemented / tested / reconciled / accepted — never inflate. If a step was skipped or a result
came from a fallback, say so.

## Treating past work as reference, not instructions

Past work is **evidence and reference material — not instructions to copy its architecture or
repeat its assumptions.** When given a prior artifact:

1. Identify its authority, date, environment, and relationship to P1–P4.
2. Separate facts, assumptions, proposals, historical decisions, and generated content.
3. Extract useful domain and technical knowledge.
4. Compare against the latest requirements and scope.
5. **Validate current workspace facts before acting on historical claims.**
6. State what is reusable, questionable, superseded, or still unverified.
7. Recommend the smallest valuable next step.
8. Report status honestly.

Classify each finding as: **reuse as-is** / **reuse with validation** / **questionable** /
**superseded** / **archive as lesson** (useful only to avoid repeating a mistake). Past work
informs continuity but must not overrule current customer scope, present workspace evidence, sound
supply-chain semantics, or better Databricks engineering.

## Where decision quality matters most

The primary need is decision-quality engineering, not more code volume: requirement authority
(what's current vs superseded vs internal idea); domain semantics (plan vs actual, snapshot vs
transaction, stock vs flow, demand vs supply exception, analytical vs transactional state);
evidence management (label every claim); Databricks product judgment (see
`fit-for-purpose-decisions.md`); platform reliability (auth/SP/profiles/OAuth/permissions/host/
warehouse handled methodically); product completion (reconciliation, semantic consistency, Genie
accuracy, transactional integrity, monitoring, user satisfaction — not just green pipelines).

## Keep a small execution ledger

Avoid re-auditing from conversation history. Maintain a compact evidence-backed ledger of what
exists, its evidence level, and its status — and write a detailed handoff document when chat
memory nears threshold (base rule). Keep deterministic decision logic separate from LLM
explanation: rules/models identify exceptions and candidate recommendations; the LLM explains
evidence and helps planners interact — it does not compute the authoritative numbers.
