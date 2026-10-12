# 04_worklog_history — the decision trail

The durable, phase-by-phase record of how this project was actually built — every accepted change, why,
and what was learned. 🔵 MKE-SPECIFIC as *content*, but 🟢 PORTABLE as a *practice*.

| File | What it is |
|------|-----------|
| `WORKLOG_current.md` | The full, current WORKLOG (~35 phases end-to-end) — the authoritative history. |
| `WORKLOG_20260831_032855.md` | Earliest milestone snapshot (early build — dashboard + rung2/p1flow). |
| `WORKLOG_20260831_055919.md` | Midpoint snapshot (redesign + cockpit + SDP era). |
| `WORKLOG_20260901_072433.md` | Late snapshot (apps deployed, skill authored). |

(The live project keeps 32 timestamped snapshots in `backups/`; these three are representative milestones
— carry the full set only if you need the complete audit history.)

## The transferable part: the PRACTICE (adopt this on any project)
1. Keep a single `WORKLOG.md` at the project root. After **every accepted piece of work**, append a
   phase entry: **the ask → what was built → bugs hit & fixed → what was learned → what's still open.**
   Chat isn't durable; this is.
2. Timestamp-backup it after each append (`cp WORKLOG.md backups/WORKLOG_$(date +%Y%m%d_%H%M%S).md`).
3. Write learnings as reusable rules, not just narration — that's what later became the skills in
   `01_skills/` and the memories in `02_memory/`. The WORKLOG is the raw ore; skills/memory are the refined metal.

## How to read it for a fast onboarding
`WORKLOG_current.md` reads top-to-bottom as the project story. Skim the **"Learned"** bullet at the end of
each phase — those are the distilled lessons (dollars-not-units, state-vs-change, vertical-slice-first,
orgs-not-interchangeable, rules-first-LLM-as-enhancement, shell-wrap-the-Streamlit-command, new-app=new-SP,
`st.dataframe`-has-no-row-click, …). Most already made it into a skill or memory; the WORKLOG shows the
context they were earned in.
