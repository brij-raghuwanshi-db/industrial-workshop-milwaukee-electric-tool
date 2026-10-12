# 02_memory — durable facts (seed a new project's memory)

20 memory files + `MEMORY_INDEX.md` (the index). Each file is one fact with frontmatter
(`name`, `description`, `type`). Types: **reference** (how things are), **feedback** (how the user wants
work done), **project** (ongoing work/decisions).

## Migrate-by-tag

### 🟢 PORTABLE — reuse on any Databricks project (generic tooling/working-style)
- `databricks-agent-skills-install` — skills install + the two update channels (plugin is authoritative).
- `prefer-latest-databricks-skills` — always use the live in-session plugin version.
- `mke-worklog-practice` — append the decision trail to `WORKLOG.md` after every accepted change.
- `mke-lessons-learnt` — vertical slice before horizontal; label evidence; done = UAT-passed not deployed.
- `dashboard-action-not-state` — operational surfaces show change+verb+$, not levels.
- `lakeview-dashboard-widget-binding` — copy working widget JSON; don't hand-invent (empty-tile trap).

### 🟡 ADAPT — same shape, swap the values
- `mke-rsc-workspace-access` — how to reach the workspace (profile/host) → replace with target's.
- `databricks-v2-mcp-connection`, `mcp-servers-status` → re-probe on the target.
- `mke-workspace-dev-location` → set to the target's dev path + writable schema.
- `mke-project-guardrails` — the read-only-prod / sandbox-writes / simulate-external boundary → the
  *principle* is universal; the schema names are MKE's.
- `mke-operating-pattern` — the working stance (mirrors `03_operating_pattern/`).

### 🔵 MKE-SPECIFIC — only for continuing MKE work
- `mke-project-scope-sources`, `mke-data-profiling-facts`, `mke-orgs-are-not-interchangeable`,
  `mke-order-lifecycle-flow-slice`, `mke-sdp-pipeline`, `mke-genie-space-built`,
  `mke-genie-app-enablement`, `databricks-streamlit-apps-skill` (pointer to the skill).

## How to re-seed into a target project's memory store
The live store lives at `~/.claude/projects/<url-encoded-project-path>/memory/`. To seed:
1. Copy the chosen `.md` files into that folder (keep the frontmatter).
2. Add a one-line pointer per file to that folder's `MEMORY.md` index (see `MEMORY_INDEX.md` here for the
   exact one-line format).
3. Fix any `[[cross-links]]` that point at memories you didn't carry over.
For a fresh non-MKE project, take the 🟢 set and write your own 🟡 access/guardrail facts.
