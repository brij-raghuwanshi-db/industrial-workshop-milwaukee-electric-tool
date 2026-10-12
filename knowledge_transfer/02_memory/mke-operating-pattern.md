---
name: mke-operating-pattern
description: "How the user wants Databricks development done on the MKE project — business-outcome-first, fit-for-purpose, workspace-first; encoded in the mke-supply-chain-fde skill"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ed081939-8656-4083-b3da-17ba19979798
---

For the Milwaukee supply-chain project the user expects a senior Databricks FDE/architect
operating stance, not from-scratch coding:

- **Business-outcome-first, not language-first or product-first.** Start from workload/grain/
  consumers/freshness/source-of-truth and whether work is one-time/reusable/production — not
  "Python, PySpark, or SQL?"
- **Databricks-native, pipeline-first, but minimum sufficient** — reuse managed/declarative
  capabilities; choose products fit-for-purpose on evidence (SDP vs Job vs notebook, Lakebase vs
  Delta, Federation vs ingestion, Metric Views), never by fashion or familiarity.
- **Workspace-first, promotion-ready** — explore in place; promote to Git/DABs/CI-CD only when
  reusable/scheduled/shared/governed/SLA-backed/production-impacting.
- **Know the gotchas** for everything used; distinguish general patterns from Milwaukee-verified
  facts; label recommendations Validated/Preferred-with-assumptions/Prototype/Blocked/Rejected.

**Why:** the user codified this across the `development_pattern/` discussions and is frustrated
when work drifts back to generic-developer habits — it costs time.

**How to apply:** the [[mke-supply-chain-fde]] skill at `.claude/skills/mke-supply-chain-fde/`
encodes the full pattern — lean `SKILL.md` core plus on-demand `references/` (fit-for-purpose,
dimensional modeling, Databricks execution craft, workspace promotion, supply-chain domain,
platform gotchas, frontend/full-stack, MLflow/AI, governance/quality, tooling currency, lessons,
project scope). Use its own "when to go deep" index rather than a fixed list here — the reference
set grows. Load it for MKE work. Authoritative scope: [[mke-project-scope-sources]]. Hard
boundaries: [[mke-project-guardrails]].
