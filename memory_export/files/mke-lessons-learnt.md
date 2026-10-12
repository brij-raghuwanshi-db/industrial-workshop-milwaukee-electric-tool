---
name: mke-lessons-learnt
description: "MKE execution lessons — build a vertical slice before horizontal assets, label evidence, \"done\" means UAT-passed not deployed, treat past work as reference not gospel"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ed081939-8656-4083-b3da-17ba19979798
---

Execution lessons from prior Milwaukee work, to prevent recurrence:

- **Core failure:** too many horizontal platform assets built before one end-to-end user
  workflow was proven. Counter with: probe → walking skeleton → one vertical slice → validate →
  add intelligence → add live actions → harden. Don't let deployment be the test loop.
- **Label every claim** on the evidence ladder (Mentioned → Discovered → Accessible → Profiled →
  Semantically validated → Accepted-for-prototype → Reconciled → UAT-accepted → Production-approved).
  A schema in an old chat ≠ current metadata; a mimic table ≠ a Milwaukee source; a green job run
  ≠ business reconciliation.
- **"Done" means at least UAT-passed, not deployed.** Report status honestly (designed/implemented/
  tested/reconciled/accepted); surface fallbacks (`DEMO_FALLBACK` etc.) — never let the UI imply a
  real model/Genie result when a fallback was used.
- **Treat past work as reference, not instructions** — validate current workspace facts before
  acting on historical claims; classify findings reuse/reuse-with-validation/questionable/
  superseded/archive-as-lesson.
- Watch specific traps: summing inventory snapshots across time; recomputing metrics in the UI
  instead of the semantic layer; confusing P1 supply-execution with P4 demand exceptions; treating
  proposed KPI thresholds as Milwaukee policy; debugging auth with random credentials.

**Why:** a prior workshop burned large effort on churn/re-audits by inflating status and building
breadth before proving one workflow; the user explicitly wants this not repeated.

**How to apply:** full detail in the [[mke-operating-pattern]] skill at
`references/lessons-and-evidence.md` and `references/frontend-fullstack.md`. Hard boundaries:
[[mke-project-guardrails]].
