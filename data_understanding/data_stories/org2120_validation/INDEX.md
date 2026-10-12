# Org 2120 (Mexico) Validation — Index

Answers the user's challenge: *"we can't blindly say all orgs behave the same — find new scenarios for the
new org, validate whether the identified scenarios apply, and derive learnings + data-model changes."*
Same rigor as the original org-2012 research; two logged subagents + independent re-verification of every
load-bearing number against the Rung-2 gold (READ-ONLY).

| File | What it holds |
|---|---|
| [A_scenario_validation_2120.md](A_scenario_validation_2120.md) | Do the ORIGINAL P1 scenarios apply to 2120? All 7 validated with side-by-side 2012-vs-2120 numbers; verdict that thresholds must be org-specific; the 9 queries. |
| [B_new_scenarios_2120.md](B_new_scenarios_2120.md) | NEW 2120-only patterns: planner concentration, 41% unique SKUs, net-receiving node, lean-yet-green, planned-pab completeness; ranked by distinctness; 15-query ledger; explicit false-alarm/non-finding list. |
| [C_synthesis_and_datamodel_changes.md](C_synthesis_and_datamodel_changes.md) | **Start here.** Consolidation + my re-verification table + the 5 concrete data-model/logic changes (org-aware `threshold_config`, percentile bands, directional bias, shared-SKU joins, planner-load & org-role attributes) + honest limits. |

**Bottom line:** the model's *logic* generalizes to 2120 unchanged (grain re-verified clean); its
*judgement* (bands, bias direction, cross-org comparison) does not — and must become org-aware. Three
findings (planner concentration, unique-SKU footprint, sourcing/flow role) are genuinely new, visible only
once 2120 was loaded.

**Post-verification correction:** the initial "2120 is a transfer-fed hub" reading was **refuted** by the
network tables — 2120 is a **directly-sourced (Buy/Make) leaf with zero transfers**; **2012** is the
transfer hub. This opened a newly-explored data area (physical flow / hops / freight cost) captured in
[D_network_flow_tables.md](D_network_flow_tables.md).
