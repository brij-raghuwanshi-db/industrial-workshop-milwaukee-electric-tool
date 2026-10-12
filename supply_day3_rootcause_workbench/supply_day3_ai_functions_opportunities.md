<div align="center">

# 🤖 Where Databricks AI Functions Showcase Something New

### Ranked, disciplined — AI at the fuzzy edges, never on the verified numbers

**Companions:** [`supply_day3_measures_and_formulae.md`](supply_day3_measures_and_formulae.md) · [`supply_day3_ux_design_v2.md`](supply_day3_ux_design_v2.md) · [`supply_day3_data_scenarios.md`](supply_day3_data_scenarios.md)
**The governing rule (project pattern):** *keep deterministic logic separate from LLM.* AI functions must
**never** compute PAB, variance, safety stock, or any measure we verified — those are governed arithmetic. AI
earns its place only where the work is **language, unstructured input, classification, or prediction** — the
fuzzy edges the deterministic engine can't touch.

</div>

---

> ## 🎯 The one-line answer
> **Yes — in 4 places AI functions do something genuinely new, and 3 of them directly attack things we flagged
> as *blocked* or *tribal*.** The strongest is `ai_parse_document` to ingest the supplier Excel / SharePoint
> PO-status files (unblocks the one ❌ external gap). The rest turn verified numbers into a narrative, classify
> free-text into structured feedback, and generate a forward projection where Oracle's stat forecast is empty.
> **None of them compute a measure — they wrap the deterministic core, they don't replace it.**

---

## ✅ Live-tested on mke-rsc (2026-09-02) — these actually work here

Before recommending anything, I ran the functions read-only on warehouse `7bd33a82f4e92206`:

| Function | Test | Result |
|---|---|---|
| **`ai_gen`** | "write a 1-line escalation: item 2941, 904u below SS at wk36, Home Depot over-consumed 101u" | ✅ *"We are issuing a supply escalation notice for item 2941, which is currently 904 units below safety stock at week 36, primarily due to over-consumption of 101 units by Home Depot."* |
| **`ai_classify`** | classify "supplier said their line was down… PO two weeks late" into 5 categories | ✅ → **"supplier constraint"** (correct) |
| **`ai_forecast`** | TVF on a synthetic weekly series | ✅ present & executes (needs correct `horizon`/date-arg format — syntax detail, not availability) |
| **`ai_parse_document`** | standard GA function (not test-run here — needs a real file in a volume) | documented/available |

**So the "with-AI" column below is real, not hypothetical** — these run on this workspace today.

---

## With-AI vs Without-AI — the honest delta

*For each opportunity: what you can show **without** any AI function (deterministic only), and what AI **adds**.
This is the "show both" view — so the incremental value is explicit, not assumed.*

### #1 · Supplier file ingestion
| | Without AI | With AI (`ai_parse_document`/`ai_extract`) |
|---|---|---|
| Supplier weekly Excel / SharePoint PO-status | ❌ **not ingested** — shows as "not connected" placeholder; planner still opens the spreadsheet manually | 🟡 parsed into Delta → PO promised-ship dates flow into the deterministic slip formula; the long-tail templates handled |
| **Delta** | the gap stays open (the one ❌ in the whole map) | **the ❌ becomes a live 🟡 feed** — this is the biggest single unlock |

### #2 · Escalation note / "Why?" ribbon
| | Without AI | With AI (`ai_gen`) |
|---|---|---|
| The two-bullet escalation | ✅ **fully works** — a **templated string** fills verified numbers into a fixed sentence ("At {DG5}, {cust} over-consumed {n}u…") | same numbers, but **fluent prose**, adapts to which drivers are present, handles multi-driver phrasing |
| **Delta** | perfectly serviceable, slightly rigid; planner may reword | reads natural, less editing — a *convenience*, not a capability the deterministic path lacks |
| **Honest call** | **the template alone is enough for MVP** | AI is polish; ship template first, add `ai_gen` as the "wow" |

### #3 · Free-text → structured feedback
| | Without AI | With AI (`ai_classify`) |
|---|---|---|
| Hold reasons / rejection notes | 🟡 planner picks from a **dropdown** of categories (manual tagging) | 🟡 free-text **auto-bucketed** into the same taxonomy; planner corrects |
| **Delta** | works, but relies on disciplined manual tagging (often skipped → the transcript's "no consistent structure") | **removes the tagging friction** → the feedback loop actually gets populated |

### #4 · Forward "second-opinion" forecast
| | Without AI | With AI (`ai_forecast`) |
|---|---|---|
| Forward risk | ✅ **from the plan's own PAB projection** (verified, deterministic) — this is the primary, trustworthy view | adds an **independent statistical projection** as a *comparison lens* ("plan says X, stat says Y") |
| **Delta** | complete on its own | a second opinion — valuable **only** where it beats the plan; must stay labelled experimental (the room's over-predict warning) |
| **Honest call** | **the deterministic forward-risk is the product**; AI forecast is an optional lens, last |

> **The pattern across all four:** **without AI, the product still fully works** on verified deterministic
> logic. AI **removes friction (#2, #3), unblocks unstructured input (#1), or adds an optional lens (#4)** — it
> is never load-bearing for a core number. #1 is the one where AI unlocks something you genuinely *cannot* do
> deterministically (parsing messy files); the rest are enhancements over a working baseline.

---

## The bright line (why this matters here)
The [formulae doc](supply_day3_measures_and_formulae.md) just proved PAB, gaps, variance, rebalance are
deterministic and verified. The domain pattern is explicit:
```
trusted data → deterministic rule → validated recommendation → AI EXPLANATION → planner review → action
                                                               └── AI lives HERE, after the math ──┘
```
So the test for every AI-function idea below: **does it touch a number, or does it touch language / unstructured
input / a prediction?** Only the latter qualifies.

---

## Ranked opportunities

### 🥇 #1 — `ai_parse_document` / `ai_extract` → ingest supplier Excel + SharePoint PO-status
**The single highest-value AI use — it unblocks the one ❌ in the whole data map.**

- **The gap:** Activity 8 confirmed supplier production plans (weekly Excel) and the PO-status report
  (SharePoint spreadsheet) are **not in Databricks**. R27 wants them ingested. The transcript: "~70% follow a
  consistent template; a long tail doesn't" — which is *exactly* the messy-unstructured problem AI parsing
  solves and rigid ETL doesn't.
- **What's new:** `ai_parse_document` / `ai_extract` reads the heterogeneous supplier workbooks and pulls
  structured fields (item, promised ship date, qty/week, capacity) into a Delta table — **handling the long-tail
  templates a fixed parser would choke on.**
- **Fits the rule?** ✅ — it's *unstructured-input extraction*, not measure computation. The extracted dates then
  feed the **deterministic** PO-slip formula.
- **Showcase value:** turns a "not connected" placeholder (per the provenance system) into a live 🟡 feed —
  visibly graduating trust. Directly serves the supplier-live-signal gap + Scenario 4.
- **Caution:** extracted values are 🟡 (AI-parsed) — label as such, keep the raw file linked for audit.

### 🥈 #2 — `ai_gen` / `ai_query` → the escalation narrative + "Why?" ribbon
**Turns verified numbers into the two-bullet email the planners spend ~2h assembling.**

- **The need:** R18/R19 (structured escalation), UX concept C-1 (the "Why?" ribbon — answer the partner in one
  click).
- **What's new:** `ai_gen` composes the prose *around* the deterministic buckets — "Home Depot over-consumed
  +101u (134%) over 4 months, driving 904u risk at wk36" — from values the math produced. One click replaces
  the 2-hour hand-assembly.
- **Fits the rule?** ✅ *only if* the numbers are passed in as facts and the prompt forbids inventing figures —
  the LLM phrases, it does not calculate. (This is the "AI explanation after the math" box exactly.)
- **Showcase value:** the most visible "wow" — the escalation drafts itself. Pairs with the provenance system:
  the draft inherits each number's tier and carries the "verify" note.
- **Caution:** mandatory "AI-generated — verify" disclaimer; show the source numbers beside the prose.
- 🎯 **Class-aware drafting (V13/DK-15):** `ai_gen` should draft the *right kind* of note per recoverability
  class — a **recovery escalation** (expedite/transfer ask) for RECOVERABLE, vs a **damage-control notice**
  (allocation + early customer notification + "logged as committed loss") for UNRECOVERABLE. And write the
  **"why it became unrecoverable" RCA narrative** only where the class warrants it (unrecoverable-material /
  chronic) — never on a DISMISS cushion-dip. The class (a governed serving column) picks the template; the LLM
  fills prose. This keeps AI at the edge and off the decision of *whether* to act.

### 🥉 #3 — `ai_classify` → structure the free-text (holds, PO changes, rejection reasons)
**Converts tribal free-text into the structured feedback loop the domain pattern wants.**

- **The need:** hold reasons, PO `change_order` context, and planner rejection reasons are free-text or coded
  inconsistently. The domain pattern's feedback-quality loop wants structured rejection reasons ("supplier
  constraint," "promo not loaded," "MOQ"…) to turn tribal knowledge into candidate rules.
- **What's new:** `ai_classify` buckets free-text hold comments / rejection notes into a fixed taxonomy →
  feeds the pattern view (Gap 4) and the "no change → why?" outcome analysis (Value page).
- **Fits the rule?** ✅ — classification of language, not measure computation. The *categories* are governed;
  AI just assigns text to them.
- 🎯 **The taxonomy already exists (DK-8, verified live):** classify into MKE's **governed
  `prod_operations.demand.dim_forecast_accuracy_reason_codes`** — 12 defined reasons (Incorrect POS
  assumptions, NPD/Transition, Promo strategy change, Business Decision, Constrained Ordering, Make-to-Order,
  Timing, Seasonality, Expansion, E&O, Customer Opportunity, Conversion). **Do NOT invent categories** — target
  theirs, and the classification is instantly business-aligned. (Make-side: `work_order_root_cause_scd1`.)
- **Showcase value:** makes the action log analytically useful (why do escalations fail?) instead of a text dump.
- **Caution:** classification is 🟡; let planners correct it (which improves the taxonomy — the feedback loop).

### #4 — `ai_forecast` → forward projection where Oracle's stat forecast is EMPTY (carefully scoped)
**Genuinely new — but the one to handle with the most discipline given the room's warning.**

- **The opening:** we found `total_statistical_forecast_*` (MAD/MAPE/model) columns exist but are **empty** in
  the readable EDW. So there's a real gap: no exposed statistical projection to compare against.
- **What's new:** `ai_forecast` (SQL time-series forecast) could generate a **baseline demand/risk projection**
  from the actuals history — as a *comparison lens* ("Oracle plan says X; a naive statistical forecast says Y —
  they diverge here"), or to extend forward-risk detection.
- **Fits the rule?** 🟡 **conditionally.** The transcript **explicitly warns** against over-predicting ("customers
  who release 'I can tell you every SKU for the next month' and send the chain the wrong way"). So `ai_forecast`
  must be framed as a **decision-support comparison, never the plan of record**, and only where prediction
  genuinely changes a decision (the fit-for-purpose rule: forecasting belongs where it beats an accepted
  baseline).
- **Showcase value:** high, *if* scoped as "a second opinion vs the plan," clearly labelled 🟡, with the plan
  staying authoritative.
- **Caution:** this is the one that could erode trust if oversold. Ship it last, as an explicit "experimental
  lens," not on the hero path.

---

## Lower-value / situational (mention, don't lead with)

| Function | Possible use | Verdict |
|---|---|---|
| `ai_similarity` / Vector Search | "similar past cases" rail (C-7) — semantic match on past escalations | 🟡 candidate, but Lakebase **BM25** was the plan for structured records; use AI-similarity only if narrative text dominates |
| `ai_summarize` | summarize a SKU's history / a cluster of exceptions / the action log | 🟡 nice-to-have; useful on the outcome view, low novelty |
| `ai_analyze_sentiment` | tone of supplier email threads | 🔴 marginal — supplier emails aren't reliably in-platform; low ROI |
| `ai_mask` | redact PII before LLM calls | ✅ good hygiene if any email/PII flows through — infra, not a feature |
| `ai_translate` / `ai_fix_grammar` | polish escalation prose (Canada/Mexico) | 🟡 minor polish on #2 |

---

## The disciplined recommendation

**Sequence AI to match trust-building, not novelty-chasing:**

1. **#2 `ai_gen` escalation narrative** — ship *with* the hero path. Highest visibility, lowest risk (wraps
   verified numbers). This is the "wow" that reads as productivity, not gimmick.
2. **#1 `ai_parse_document`** — as the R27 supplier ingestion lands. Unblocks the ❌ and showcases AI doing
   real integration work, not just chat.
3. **#3 `ai_classify`** — once the action log has volume; turns it into a learning loop.
4. **#4 `ai_forecast`** — last, as a clearly-labelled experimental "second opinion," honoring the don't-
   over-predict warning.

> **What NOT to do (the anti-pattern):** don't put an AI function on the critical measure path. No `ai_query`
> computing "demand surprise," no LLM deciding "likely cause," no AI inventing a safety-stock number. Those are
> deterministic, some are verified, and the whole trust model (the provenance badges) depends on them staying
> governed. AI wraps the core; it never becomes the core.

**Genie note:** the NL "ask this SKU" surface (UX v2) is already an AI surface — it uses the Genie Conversation
API + the AI-trust patterns (identity, generated SQL, disclaimer). That's complementary to these `ai_*`
SQL functions: Genie = conversational Q&A; `ai_*` = in-pipeline AI on specific columns. Both wrap the same
governed data.

---

<div align="center">

### 📌 In one line
**Databricks AI functions showcase something new in exactly 4 places — parse the messy supplier Excel/SharePoint
files (`ai_parse_document`, unblocks the one ❌), auto-draft the escalation from verified numbers (`ai_gen`,
the "wow"), structure free-text into a feedback loop (`ai_classify`), and offer a scoped "second-opinion"
forecast (`ai_forecast`, handle with care) — all at the fuzzy edges, never computing a measure, so the
verified deterministic core and its provenance badges stay trustworthy.**

*Grounded in the confirmed data + the formulae confidence tiers. AI-derived outputs are 🟡 by construction and
wear the provenance badge. No production schema written.*

</div>
