# Genie Space — Test Evidence (what we validated, with real answers)

**Space:** "P1 Actuals — Supply Plan vs Actual (SDP)" · id `01f1a542c3f7132681b64d8ff08b4033`
**Attached to dashboard:** "P1 Actuals — SDP (Rung 2)" `01f1a5371959178aa137d5551347afff`
(via `uiSettings.genieSpace` → "Ask Genie" button).
**Method:** questions asked live through the Genie Conversation API; answers below are Genie's own,
verified against the dashboard / gold tables. All answers return the **underlying SKU/PO/planner records**,
not just a number — the record-pinpoint requirement.

Legend: ✅ correct · numbers cross-checked to the SDP gold.

---

## A. Per-item (unit-level) questions
| Question | Genie's answer (abridged) | Verdict |
|---|---|---|
| "For item 77001T at org 2012, planned vs actual on-hand week by week + variance" | Returned all **25 weekly rows** (e.g. 2026-08-24 planned 2,139 / actual 2,324 / +185 / +8.6% / green); flagged worst over-plan 2026-06-15 (+3,538u, red) and worst under-plan 2026-05-25 (−1,641u, yellow). | ✅ |
| "For item 77001T, receive vs plan and ship vs plan each week" | Weekly receipts (e.g. 2026-06-29 received 1,296) + shipped-vs-plan where a plan existed (2026-06-01 plan 6 / actual 342). Correctly noted planned-receipts is not a field we carry. | ✅ (+ honesty) |

## B. Anti-pattern / guardrail questions (naive phrasing → must NOT fall in the trap)
| Question | What Genie did | Verdict |
|---|---|---|
| "Total inventory on-hand across ALL weeks?" (AP-1) | **Refused to sum across weeks** — wrote a note that on-hand is point-in-time, used `week_start = MAX(week_start)` only. | ✅ trap avoided |
| "Biggest safety-stock misses, ranked by priority?" (AP-5) | Ranked by **stockout_risk_usd = (SS−actual)×cost**, NOT unit-miss (48111881X M18 Forge battery $3.07M / 50,336u). | ✅ $-ranked |
| "Which items are unplanned at 2012?" | Filtered `planned_pab IS NULL` (unplanned, not "no actual"). | ✅ |
| "What should I escalate right now?" | `alert_tier = '3 · Escalate'`, ranked by ABS($). | ✅ org-aware tier |
| "What mirage/misleading fields do I have?" | Recalled from instructions: `expected_receipt_date` = same-day mirage; don't sum on-hand across weeks; don't compare orgs on raw $. Noted "misleading is context, not a field." | ✅ knows the traps |

## C. Scenario questions (from data_stories library)
| Question | Genie's answer | Verdict |
|---|---|---|
| "Most extreme plan-vs-actual variances by $" (V) | Top misses by ABS($), latest week, with item/org/week. | ✅ |
| "Compare plan bias 2012 vs 2120" (N/2120) | Both **over-plan**: 2012 74.0% vs 2120 28.8%; green 39.9% vs 65.5%; red 39.6% vs 22.8%. Framed as "not inverted." **Exact match to sdp_agg_scorecard.** | ✅ |
| "Off-plan items this week, ranked by $" (S5) | Named SKUs: 369229 M18 Combo −$8.8M, 369722 −$2.6M, 377120 +$1.6M… | ✅ |

## D. P1 requirement questions (UC1–UC6 / M1–M5 from customer_requirements)
| Req | Question | Genie's answer (abridged) | Verdict |
|---|---|---|---|
| UC1/M1 | PO expected vs received this week | 48223100P expected 1,315,584 / received 0; 49940005 expected 1,192,007 / received 115,200 … | ✅ |
| UC2/M3 | Ending on-hand vs projected PAB (2012) | 369229 actual 0 vs projected 20,700 (−100%, red); 377120 actual 23,082 vs 12,227 (+88.8%, red) | ✅ |
| UC3/M5 | Demand actual vs plan (shipped vs planned SO) | Inkzall marker planned 1,404 / shipped 95,508; HCS blade planned 37,500 / shipped 0 | ✅ |
| UC4 | Is plan accuracy improving? (MAPE trend) | 2012 MAPE 72.9%→68.9%, spike 206% on 06-15 — "not steadily improving" | ✅ |
| UC5 | What changed in the plan? | Biggest WoW $-variance shifts per item (296722+48228427 Mexico −$11.4M …) | ✅ |
| M2 | Shipped vs planned gap, ranked | Inkzall +94,104; HCS blade −37,500; M18 XC5.0 battery +17,607 … | ✅ |

## E. Action-decision questions (the App-preview questions)
| Question | Genie's answer (abridged) | Verdict |
|---|---|---|
| "Which shipment should I cancel?" | Overstocked M18 RL HO XC5 Battery @2012 (310,834 on-hand vs 63,281 SS = $8.4M excess); listed the specific inbound POs (PO-380066686-23 / -16 / -30 …) as cancel/defer candidates. | ✅ |
| "Which planner should I alert?" | **Bartholf, Nick — $1.69M** newly-red exposure (latest week); then Cotteleer $1.44M, Newkirk $1.42M, Lowe $1.15M. | ✅ |

> **Boundary (important for the team):** Genie *recommends* — it does not *execute*. It can tell you which
> shipment to cancel and which planner to alert, but it cannot cancel the PO or send the alert. That
> execution loop (click → approve → writeback) is the **App** (roadmap step 3). Genie = "what / why / who";
> App = "do it."

## Starter chips now in the Space (what users see without typing)
Off-plan by $ · item plan-vs-actual over 8 wks · stockout risk @2120 + SKUs · unplanned items ·
bias 2012 vs 2120 · Tier-3 escalations · expedite vs fix-supplier · on-hand value by org ·
**which shipments to cancel/defer** · **which planner to alert** · **what mirage fields to avoid**.

## How to tune (feedback loop)
If any answer is off: note the question, then add/edit an `example_question_sqls` entry or a line in
`text_instructions` in `genie_agent.json` and run
`databricks genie update-space 01f1a542c3f7132681b64d8ff08b4033 --json ...`. No rebuild needed.
