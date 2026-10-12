# 01_skills — reusable agent skills

Four skills. Install by copying into the target's `.claude/skills/` (the auto-load path). Each is a
`SKILL.md` (entry + iron rules + routing) plus a `references/` tree and, where relevant, `templates/`.

| Skill | Tag | Files | Migrate when | What it teaches |
|-------|-----|-------|--------------|-----------------|
| `databricks-streamlit-apps` | 🟢 PORTABLE | 20 | building any Streamlit app on Databricks Apps | Full recipe + copyable templates + symptom→fix register (shell-wrap command, Lakebase OAuth token mint via `POST /api/2.0/postgres/credentials`, SP catalog grants, `st.dataframe` click trap, deploy/verify). |
| `databricks-agentic-ops-app` | 🟢 PORTABLE | 12 | building a governed agentic cockpit app (AppKit/React) | Two-plane (OLAP truth + OLTP write surface), one writable table, HITL approval gate, live cascade, MLflow tracing, AI-Gateway governance, degrade-don't-loop. |
| `lakeview-dashboard-fastpath` | 🟢 PORTABLE | 2 | building an AI/BI (Lakeview) dashboard | The iron rules (don't hand-invent widget JSON; test the concatenated dataset query via CLI before publish), design-each-widget discipline, a known-good skeleton. |
| `mke-supply-chain-fde` | 🟡 ADAPT | 14 | continuing MKE work, or as a template for a project operating-skill | The project operating pattern: business-outcome-first, fit-for-purpose, workspace-first, the write-boundary guardrails, dimensional/transactional modeling, MLflow, frontend. Domain specifics (MKE tables/orgs) need generalizing for other projects. |

## How to adapt the 🟡 one
`mke-supply-chain-fde` is the best *shape* for a project-operating skill (it sits above the platform
skills and encodes "how we work here"). To reuse on another project: keep the structure + the generic
references (fit-for-purpose-decisions, workspace-first-promotion, governance-and-quality, execution-craft,
dimensional-modeling, mlflow, frontend); replace the domain files (supply-chain-domain, project-scope,
data-profiling, lessons) with the new project's facts.

## Provenance note
`databricks-agentic-ops-app` was the skill the apps were built *from*; `databricks-streamlit-apps` was
authored *from* shipping the Streamlit twin (its symptom→fix register is that build's real debugging).
Both complement — not replace — the `databricks-apps` / `databricks-lakebase` / `databricks-genie-agents`
plugin skills; keep those installed too.
