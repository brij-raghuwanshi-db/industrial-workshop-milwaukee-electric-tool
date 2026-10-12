# 03_operating_pattern — the "how to work on Databricks" foundation

The docs the whole project ran on. **Read these first** — they are the *why* behind every skill in
`01_skills/`. All 🟢 PORTABLE (they're stance, not MKE facts), except where a doc uses supply-chain
examples — the principle generalizes.

| File | Tag | What it establishes |
|------|-----|---------------------|
| `000_base_rule.md` | 🟢 | The base rule set — the non-negotiable floor for how the machine is directed. Start here. |
| `Is there a better way to direct a machine to do th.md` | 🟢 | The origin question — how to direct an agent well; the thinking that produced the operating pattern. |
| `Databricks-Centric Development Operating Pattern.md` | 🟢 | The core stance: business-outcome-first (not language/product-first), reuse Databricks-managed/declarative capabilities before custom, choose fit-for-purpose on evidence. |
| `Workspace-First Databricks Development and Bundle Promotion.md` | 🟢 | Explore in the workspace; promote to Git/DABs/CI-CD only when an asset becomes reusable/scheduled/shared/governed/SLA-backed. |
| `MLflow and Databricks AI Engineering Playbook for Supply Chain.md` | 🟢/🟡 | MLflow + GenAI engineering playbook (tracing, eval, agents). The MLflow craft is portable; the supply-chain examples are illustrative. |

## The distilled non-negotiables (put these in the target's root `CLAUDE.md`)
```
- Business-outcome-first: open with the workload, grain, consumers, freshness, source-of-truth, and
  whether it's one-time / reusable / production — not "Python or SQL?".
- Reuse Databricks-managed & declarative capabilities before building custom. Minimum sufficient
  architecture; don't overengineer, don't leave production-bound work as an unmanaged notebook.
- Workspace-first, promotion-ready: explore in place; promote to Git/DABs/CI-CD only when the asset
  earns it (reusable/scheduled/shared/governed/SLA-backed).
- Data-write boundary: production schemas are READ-ONLY; all writes go to an approved sandbox schema +
  the app's OLTP store; external-system writeback is a separately-approved, typed, auditable path —
  never a direct prod write. (Adapt the schema names to the target project.)
- Challenge yourself: state assumptions, weigh alternatives, name what you did NOT pick, and separate
  general industry patterns from facts verified against the actual systems.
- Handoff on threshold: when chat memory nears its limit, write a detailed handoff first.
```
These are the same rules that made this project reproducible. The skills operationalize them; this
folder is the charter.
