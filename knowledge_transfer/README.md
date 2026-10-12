# Knowledge Transfer Bundle — MKE Supply Chain on Databricks

Everything reusable that came out of this project, packaged to **migrate into a new project,
workspace, or team**. Skills, memories, the operating pattern, and the decision trail — organized
into four sub-sections, each with its own README and a portable-vs-project-specific tag.

> **The goal:** a new agent (or engineer) picks this up and reproduces the *best path* — the way of
> working and the hard-won build recipes — without re-living the mistakes. Read `MIGRATION_GUIDE.md`
> first for the install order.

## What's inside

| Section | What it is | Migrate as |
|---------|-----------|-----------|
| **`01_skills/`** | 4 reusable agent skills (fastpaths + templates + symptom→fix registers) | drop into `.claude/skills/` (auto-load) |
| **`02_memory/`** | 20 durable facts + index — access, guardrails, domain, build knowledge | seed a new project's memory store |
| **`03_operating_pattern/`** | The foundational "how to work on Databricks" docs the whole project ran on | read first; they justify the skills |
| **`04_worklog_history/`** | The decision trail — current WORKLOG + milestone snapshots | reference / audit; shows how decisions were made |

## Portability legend (used throughout)
- 🟢 **PORTABLE** — reusable on ANY Databricks project as-is (generic craft/platform knowledge).
- 🟡 **ADAPT** — reusable pattern, but has MKE-specific values (ids, table names, org codes) to swap.
- 🔵 **MKE-SPECIFIC** — this project's facts/scope; migrate only if continuing MKE work.

## The two headline skills (the "best path" this project produced)
1. **`databricks-streamlit-apps`** 🟢 — build a Streamlit app on Databricks Apps from scratch, right the
   first time. Fastpath + copyable templates + a symptom→fix register drawn from a real deployment.
2. **`databricks-agentic-ops-app`** 🟢 — build a governed, agentic operational-cockpit app (AppKit/React +
   Lakebase + warehouse + Genie + streaming agent). The see→ask-why→act→cascade→audit pattern.

Plus `lakeview-dashboard-fastpath` 🟢 (AI/BI dashboards) and `mke-supply-chain-fde` 🟡 (the project
operating pattern — generalize the domain specifics).

## Provenance
Exported from `mke_rsc_isaac` on 2026-09-01. Sources: `.claude/skills/` (live skills),
`memory_export/` (memory + the agentic-ops skill), `development_pattern/`, and `backups/` (WORKLOG
snapshots). The live originals remain in place; this bundle is a self-contained, portable copy.
