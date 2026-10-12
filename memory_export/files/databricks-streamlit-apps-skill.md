---
name: databricks-streamlit-apps-skill
description: Project skill for building Streamlit apps on Databricks Apps from scratch (fastpath + templates + symptom-fix register)
metadata: 
  node_type: memory
  type: reference
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

`.claude/skills/databricks-streamlit-apps/` — a build-from-scratch fastpath skill for Streamlit on
Databricks Apps, distilled from the real `mke-po-actions-st` build. Load it for ANY Streamlit (or
non-AppKit Python) Databricks App work; it complements the plugin skills (databricks-core / -apps /
-lakebase / -genie-agents), doesn't replace them.

Structure: SKILL.md (iron rules + 8-step loop + reference routing), 7 references (architecture,
project-structure, lakebase-connectivity, integrations, ui-patterns, deploy, symptom-fix), and a
complete copyable `templates/` app (app.yaml, databricks.yml, requirements.txt, .gitignore, app.py,
lib/{config,lakebase,warehouse,serving,identity}.py, pages/1_Example.py).

Highest-value load-bearing rules it encodes: shell-wrap the app.yaml command (`bash -c`) or
`${DATABRICKS_APP_PORT}` is literal and the app crashes; Lakebase password = a refreshing OAuth token;
declare resources with permissions for SP auto-grant; sync.exclude the venv from deploy #1; rules-first
LLM-as-enhancement; `st.rerun` is the live cascade; `LIKE … INCLUDING ALL` forks a Lakebase schema.
The `symptom-fix.md` register is the turn-by-turn debugging of the real build. See [[mke-genie-app-enablement]].
