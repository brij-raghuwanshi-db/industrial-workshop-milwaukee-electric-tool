---
name: mke-genie-space-built
description: "MKE P1 Genie Space built on sdp_* tables; answers pinpoint the underlying SKU records; id 01f1a542c3f7132681b64d8ff08b4033"
metadata:
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

The Genie Agent for MKE P1 is BUILT (roadmap: it came before the App, at the user's request). It's a
**Genie Space** (not a custom agent) — "P1 Actuals — Supply Plan vs Actual (SDP)", id
**`01f1a542c3f7132681b64d8ff08b4033`**, warehouse 7bd33a82f4e92206, under
`/Workspace/Users/brijendra.raghuwanshi@databricks.com/genie_spaces`. Definition on disk:
`data_understanding/workspace_assets/genie_agent.json` (5 tables, 8 sample Qs, 15 example SQLs, 1 merged
text_instructions). Regenerate/iterate via `databricks genie update-space <id> --json ...`.

Grounded on 5 `sdp_*` tables (fact + key serving): sdp_plan_vs_actual (item×org×week fact — the record-level
answers), sdp_agg_scorecard, sdp_exceptions, sdp_order_stage_gold, sdp_rootcause_plant.

**Hard requirement the user set: answers must PINPOINT the exact records.** Implemented as (a) a text rule
"ALWAYS SHOW THE RECORDS BEHIND A NUMBER" and (b) every example SQL returns item_id/item_description/
organization_code/week_start ranked by $ (LIMIT 50-100). Ground record-level questions on the FACT, not the
pre-agg serving tables (those lose item keys). Verified live: off-plan-by-$ returned named SKUs; the
"on-hand value by org" guardrail correctly used MAX(week_start) (no cross-week sum → avoided the 5.48× trap);
bias 2012 vs 2120 = 74.0% vs 28.8% (exact scorecard match, framed as both-over-plan not "inverted").

Built by RETARGETING the pre-written [[mke-genie-app-enablement]] assets (GENIE_ENABLEMENT_NOTE Parts C/D
rules + GENIE_QUESTION_BANK 7 parts incl. plan-vs-actual + guardrails) from rung2_/ds_/p1flow_ to sdp_*.
Space-JSON gotchas: 32-hex ids unique across all 3 lists; tables + example_sqls sorted; text_instructions
exactly ONE merged item; text fields are arrays. Next roadmap step: the App (Lakebase actions, simulated
writeback — no real Oracle per [[mke-project-guardrails]]). See [[mke-sdp-pipeline]], [[dashboard-action-not-state]].
