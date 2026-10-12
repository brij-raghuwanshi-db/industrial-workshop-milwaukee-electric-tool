<div align="center">

# 📁 Supply Root-Cause Workbench — Document Set

### Day-3 supply-planning breakout → requirements → data → design → scenarios

All artifacts from the Day-3 supply-planning working session and the analysis/design that followed.
Read-only analysis against Databricks profile `mke-rsc`; no production schema written.

</div>

---

## Read in this order

| # | Document | What it is | Provenance |
|---|---|---|---|
| 0 | [`supply_day3_discussion.md`](supply_day3_discussion.md) | **Source** — raw transcript of the Day-3 breakout | verbatim |
| 1 | [`supply_day3_requirements.md`](supply_day3_requirements.md) | Requirements extracted from the transcript (Parts A–J) **+ Part K data-discovered candidates** | transcript + data |
| 2 | [`supply_day3_data_mapping.md`](supply_day3_data_mapping.md) | Which workspace tables back each requirement (9 activities) | live-verified |
| 3 | [`supply_day3_capability_map.md`](supply_day3_capability_map.md) | What each visual makes the user *able to do* + 10 capability gaps | analysis |
| 4 | [`supply_day3_gap_tables.md`](supply_day3_gap_tables.md) | Which tables close each capability gap | live-verified |
| 5 | [`supply_day3_ux_design.md`](supply_day3_ux_design.md) | UX v1 — the shortage workbench (5 screens + Value page) | design |
| 6 | [`supply_day3_ux_design_v2.md`](supply_day3_ux_design_v2.md) | UX v2 — anticipate + decide upgrades (once gaps sourced) | design |
| 7 | [`supply_day3_ux_design_v3_scenarios.md`](supply_day3_ux_design_v3_scenarios.md) | UX v3 — six scenario lenses (nervous system) | design |
| 8 | [`supply_day3_data_architecture_adr.md`](supply_day3_data_architecture_adr.md) | ADR — thin serving layer vs raw vs big model | decision |
| 9 | [`supply_day3_joins_er_diagram.md`](supply_day3_joins_er_diagram.md) | Join model + ER diagram + exact join keys | live-verified |
| 10 | [`supply_day3_data_scenarios.md`](supply_day3_data_scenarios.md) | Six data-discovered scenarios beyond the transcript | live-probed |
| 11 | [`supply_day3_measures_and_formulae.md`](supply_day3_measures_and_formulae.md) | Every measure's formula + confidence (verified/inferred/blocked); variance family; simulation; **statistical formulae**; the show-everything-with-distinctions provenance system | live-tested + ASCM-anchored |
| 12 | [`supply_day3_ai_functions_opportunities.md`](supply_day3_ai_functions_opportunities.md) | Where Databricks AI functions add something new — ranked, disciplined (AI at the edges, never on verified numbers) | design |
| 13 | [`supply_day3_scenario_id_catalog.md`](supply_day3_scenario_id_catalog.md) | **≥50 real business IDs per scenario** (26 scenarios · 1,560 IDs) with the exact successful READ-ONLY query + scenario→requirement mapping for each | live-extracted |

## 🖥 Clickable visual spec
[`prototype/index.html`](prototype/index.html) — HTML workbench of the designed product (trials, drawers, ledger). Open in a browser; no warehouse. Seeded from validated Day-3 IDs.

## 🎬 Start here for the narrative
[`supply_day3_day_in_the_life.md`](supply_day3_day_in_the_life.md) — a full "day in the life" of planner *Leo*
using the built app, hour by hour, with **real validated examples** (3697-22 $6.98M, Techtronic 3,035 SKUs,
$372.5M unrecoverable, Home Depot 251 vs 150…) and **full per-screen UI mockups**. The best single read for
"what does this actually do for someone."

## The classifier layer (validation V10–V13 → DK-13/14/15)
The deepest finding across the validation isn't a new measure — it's a **Classify stage** between Detect and
Explain. Every flag is tagged by **severity · temporal class (acute/chronic/nervous) · convergence · recoverability
(winnable vs committed loss) · action-verdict (ACT/WATCH/DISMISS)**, pre-computed as serving columns, and those
tags **gate RCA depth**. Net (live): a 10,700-flag alarm → a ~3,634-ACT, recoverability-aware worklist. See
`validation/` (V10–V13), requirements Part K (DK-13/14/15), and the ADR §7.1a serving schema.

## The one-line story
The planners described a **shortage-triage** workflow ("we're short — how did we get here?"). The analysis
confirmed **every screen's data is present today**, surfaced **10 capability gaps** (all sourceable), and then
probing the data revealed the shortage story is one lens of a much bigger picture — **$452M excess, 1,646
transfer-before-buy opportunities, chronic forecast bias, and supplier-slip concentration.** The recommended
build is a thin serving layer, slice-first, shipping the shortage lens to earn trust then widening to a
control-tower.

## Guardrails (project rules)
`prod_edw` / `prod_operations` = **READ-ONLY**. Derived/serving tables → `sandbox_operations.po_management`.
Transactional app state → **Lakebase**. No external-system writeback except via an approved, typed, auditable path.

*Full decision trail: see the Day-3 entries in the project [`WORKLOG.md`](../WORKLOG.md).*
