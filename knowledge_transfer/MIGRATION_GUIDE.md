# Migration Guide — installing this knowledge into a new project

Follow in order. Steps 1–2 are the "best path" (skills + operating pattern) and apply to **any**
Databricks project; steps 3–4 seed project context and are only needed if continuing/branching MKE work.

## 0. Prerequisites (on the target machine)
- Databricks CLI ≥ v1.14 authenticated to the target workspace (`databricks auth login --profile <name>`).
  Never auto-select a profile — always pass `--profile <name>`.
- Claude Code with the Databricks plugin skills (`claude plugin install databricks@claude-plugins-official`)
  — this bundle's skills *complement* those; they don't replace them.

## 1. Install the skills (🟢 portable — do this first)
Copy the skills you want into the target project's **`.claude/skills/`** (that path is what auto-loads them):
```bash
mkdir -p <target>/.claude/skills
cp -R 01_skills/databricks-streamlit-apps     <target>/.claude/skills/
cp -R 01_skills/databricks-agentic-ops-app    <target>/.claude/skills/
cp -R 01_skills/lakeview-dashboard-fastpath   <target>/.claude/skills/
# mke-supply-chain-fde is 🟡 — see step 3 before copying (it encodes MKE guardrails/domain)
```
Verify: start Claude Code in `<target>`; the skills should appear in the available-skills list. Each
`SKILL.md` has a `description` that tells the agent when to auto-invoke it.

**What each buys you:**
- `databricks-streamlit-apps` → the whole Streamlit-on-Apps recipe (shell-wrap command, Lakebase OAuth
  token mint, SP catalog grants, `st.dataframe` click trap, deploy) + a copyable `templates/` app.
- `databricks-agentic-ops-app` → the governed agentic-cockpit architecture (two-plane, one writable
  table, HITL gate, live cascade, MLflow tracing, degrade-don't-loop).
- `lakeview-dashboard-fastpath` → build an AI/BI dashboard in one clean pass (the iron rules + skeleton).

## 2. Adopt the operating pattern (🟢 read, then encode)
Read `03_operating_pattern/` — business-outcome-first, fit-for-purpose, workspace-first, and the base
write-boundary rule. These are the *why* behind the skills. To make them binding on the new project, put
the non-negotiables into the target's root `CLAUDE.md` (see the template in `03_operating_pattern/README.md`).

## 3. Seed project memory (🟡/🔵 — adapt or skip)
`02_memory/` holds 20 durable facts. For a NEW non-MKE project, take only the 🟢 ones (tooling/skill
install, prefer-latest) and write your own access/guardrail facts. For CONTINUING MKE work, seed them
all into the target memory store (see `02_memory/README.md` for the split + how to re-import).

## 4. Carry the decision trail (🔵 reference)
`04_worklog_history/` is the audit trail — how decisions were actually made across ~35 phases. Keep it
as reference; adopt the **practice** (append every accepted change to a `WORKLOG.md`, back it up) rather
than the content.

## The "best path" in one paragraph
Discover with `databricks-core` → decide the data plane (warehouse for OLAP, Lakebase for OLTP/writes) →
scaffold from the skill templates → author the data layer first and verify every SQL against the real
backend before any UI → deploy with a shell-wrapped command + `sync.exclude` + declared resource
permissions → grant the app SP on the catalog it reads → verify live as the SP, degrade gracefully where
access is pending. Deterministic answer first, LLM as enhancement. Log every accepted step. That loop —
encoded in the skills here — is the transferable asset.
