---
name: dashboard-action-not-state
description: "Operational dashboards must show change+verb+$, not levels; levels read as 'just another chart'"
metadata:
  type: feedback
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

A dashboard tile that shows a **level/state** ("13,146 items red", "$1bn at risk", "242k item-weeks
off-plan") reads to an operator as *"okay, just another chart"* — because the number barely moves week to
week, so there's no trigger to act. The MKE planner said exactly this looking at the Rung-2 overview.

**The fix (now a design rule for operational pages):** open with **what CHANGED** since last period + a
**VERB** (what to do) + the **$** (why it matters) + a **systemic flag** (fix this order vs fix the source).
- Delta, not level: "2,243 items newly RED = $23.7M NEW exposure this week (1,486 recovered)" — not
  "13,146 red".
- Ranked action list with a verb: item · $ at risk · EXPEDITE / DEFER-CANCEL / FIX-SUPPLIER / REVIEW ·
  systemic-vs-one-off · planner. That IS a planner's Monday to-do, top-down by $.
- Levels & analytics become the drill-down "why" behind the action surface, not the front door.

**Why:** built as page "0 · Monday Cockpit" (first page of the Rung-2 dashboard) after the user challenged
"what's my next action from this? currently nothing." Verified the delta signal exists: WoW newly-red count/$,
resolved, escalations, stockout-$ swing all compute from the two latest `week_start` snapshots; the verb comes
from the same band logic used for exceptions; the systemic flag from p1flow chronic_pct_late≥60.

**How to apply:** for any operational/Monday-style dashboard or the future App, lead with an action surface
(change + verb + $), not a state summary. Pairs with the FVA finding (planning worse than naive) and the
org-aware thresholds. Roadmap context: Dashboard (done) → stable SDP+Job pipeline → App (clickable actions,
Lakebase, simulated writeback — no real Oracle). See [[mke-genie-app-enablement]], [[mke-worklog-practice]],
[[mke-order-lifecycle-flow-slice]].
