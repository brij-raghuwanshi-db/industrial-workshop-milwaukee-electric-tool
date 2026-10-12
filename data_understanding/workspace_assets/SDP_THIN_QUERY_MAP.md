# Thin-query rewrite map — cloned dashboard datasets → sdp_* serving tables

Each live dashboard dataset (aggregates 590k gold rows) is replaced by a THIN query over a
pre-aggregated `sdp_agg_*` serving table. Same output columns, same param behaviour, but the live
scan drops to tens–hundreds of rows. Where a live tile computes a week-windowed AVERAGE, the serving
table stores ADDITIVE COMPONENTS (sum + count) and the thin query reconstructs the exact average.

Legend: [P] param preserved (org_f / wk / sku). [WHOLE] whole-window agg, no week param.

| # | dataset | live source (rows scanned) | THIN sdp source (rows) | rewrite notes |
|---|---|---|---|---|
| ds_pva | 590k | plan_vs_actual | KEEP raw over sdp_plan_vs_actual (row-level tile; still filters, no agg) | derived cols identical; [P] org_f auto |
| ds_week | 590k GROUP BY wk | sdp_agg_week_org | SUM red/green, SUM net$, AVG bias = SUM(avg_bias*items?)… NO: bias is AVG-of-pct → store not exact; use pre-stored avg_bias_pct per wk×org then re-AVG weighted by items | [P] org_f via array_contains |
| ds_abc | 590k | sdp_agg_abc | SELECT * (whole) | [WHOLE] |
| ds_topexc | 590k WHERE red/yellow | sdp_exceptions | SELECT ... ORDER BY abs_var_dollar LIMIT 25 | rows already filtered to red/yellow |
| ds_orgcmp | 590k | sdp_agg_orgcmp | SELECT * | [WHOLE] |
| ds_planner | 590k | sdp_agg_planner | SELECT ... ORDER BY total_abs_dollar LIMIT 15 | [WHOLE] |
| ds_tier | 590k | sdp_agg_tier | SELECT * | [WHOLE] |
| ds_imbalance | 590k self-join | KEEP over sdp_plan_vs_actual (needs item-level cross-org row match at one week) | small after WHERE; acceptable |
| ds_scorecard | 590k | sdp_agg_scorecard | SELECT * | [WHOLE] |
| ds_scale_ctx | 590k | sdp_agg_scale_ctx | SELECT * | [WHOLE] |
| ds_varpct_long | 590k ×4 | sdp_agg_varpct_long | SELECT * | [WHOLE] percentiles pre-agg |
| ds_sku_share_long | 590k | sdp_agg_sku_share | SELECT * | [WHOLE] |
| ds_planner_conc | 590k | sdp_agg_planner_conc | SELECT * | [WHOLE] |
| ds_exc_queue | 590k+p1flow | sdp_exceptions WHERE worst_rn=1 | chronic already joined; ORDER BY abs_var_dollar LIMIT 500 | [P] wk optional |
| ds_exc_pareto | 590k WHERE wk | sdp_agg_exc_pareto | SUM items, SUM $ GROUP BY type WHERE week in [wk] | [P] wk via BETWEEN on week_start |
| ds_accuracy_split | 590k WHERE wk | sdp_agg_accuracy_split | SUM n GROUP BY org,wk,dir WHERE wk | [P] wk + org_f |
| ds_sla | 590k WHERE wk | sdp_agg_sla_ow | reconstruct: mape=SUM(sum_abs_var_pct)/SUM(cnt_mape); within15=100*SUM(within15_num)/SUM(cnt_total); stockout=SUM(stockout_items) — over picked weeks | [P] wk+org_f. EXACT via components |
| ds_abc_median | 590k WHERE wk | sdp_agg_abc_median | SELECT * (percentile → whole-window; wk param dropped w/ note) | [P] org_f only; wk not additive |
| ds_money_risk | 590k | sdp_agg_money_ow | SUM stockout$, SUM excess$ GROUP BY org (all weeks) | [WHOLE]; [P] org_f |
| ds_plan_evolution | planned_weekly | sdp_agg_plan_evolution | SELECT * | [WHOLE] |
| ds_plan_change_items | planned_weekly | sdp_agg_plan_change_items | ORDER BY abs_change LIMIT 100 | already row-filtered |
| ds_mom | 590k | sdp_agg_mom | SELECT * | [WHOLE] |
| ds_po_timing | p1flow_gold | sdp_agg_po_timing | SELECT * | [WHOLE] |
| ds_rootcause_dc | 590k WHERE wk | sdp_agg_rootcause_dc | SUM item_weeks, SUM $ GROUP BY org,cause WHERE wk | [P] wk+org_f |
| ds_rootcause_plant | table | sdp_rootcause_plant | SELECT * | [WHOLE] |
| ds_fva | 590k window | sdp_agg_fva | SELECT * | [WHOLE]; [P] org_f. NOTE: LAG done in MV, org_f filters post-agg (per-org rows) |
| ds_bias_persist | 590k | sdp_agg_bias_persist | SELECT * | [WHOLE]; [P] org_f |
| ds_acc_leadtime | p1flow_po | sdp_agg_acc_leadtime | SELECT * | [WHOLE]; [P] org_f (org col present) |
| ds_mape_trend | 590k GROUP wk | sdp_agg_week_org | mape=sum_abs_var_pct/cnt_mape per wk×org; target 15 literal | [P] org_f. EXACT via components |
| ds_drill_sku | 590k WHERE sku | KEEP over sdp_plan_vs_actual (CLUSTER BY item_id → prunes to one sku) | [P] sku+wk. clustered so scan tiny |
| ds_plan_nervous | planned_weekly | sdp_agg_plan_nervous | SELECT * | [WHOLE] |
| ds_plan_converge | planned_weekly | sdp_agg_plan_converge | SELECT * | [WHOLE] |
| ds_drill_field | 590k | KEEP over sdp_plan_vs_actual (row-level drill; filters, small after sku/org) | [P] |
| ds_cockpit_change | 590k WoW | sdp_agg_transitions | SUM newly_red, SUM newly_red*dollar, resolved, is_red, escalation GROUP BY org for latest wk in window | [P] wk+org_f. transitions pre-computed |
| ds_cockpit_actions | 590k WoW+p1flow | sdp_agg_transitions WHERE newly_red=1 latest wk | action pre-computed; ORDER BY dollar LIMIT 200 | [P] |
| ds_cockpit_kpi | 590k WoW | sdp_agg_transitions + sdp_agg_money_ow | swing=this-prior stockout$ (from money_ow 2 weeks); %systemic from transitions | [P] |
| ds_cp_trend | 590k | sdp_agg_transitions | SUM newly_red, $ GROUP BY wk,org | [P] |
| ds_cp_planner | 590k WoW | sdp_agg_transitions WHERE newly_red latest wk | GROUP BY planner ORDER BY $ LIMIT 15 | [P] |
| ds_cp_actionmix_wk | 590k+p1flow | sdp_agg_transitions WHERE newly_red | SUM dollar GROUP BY wk,action,org | [P] |
| ds_cp_aging | 590k | KEEP over sdp_plan_vs_actual (needs per-item red streak over recent weeks) | small; [P] org_f |
| ds_drill_onhand_long | 590k UNION | KEEP over sdp_plan_vs_actual (long-format for one sku) | [P] filters to sku |
| ds_drill_flows_long | 590k UNION | KEEP over sdp_plan_vs_actual | [P] filters to sku |

## Fidelity rule applied (the important part)
- Week-windowed AVERAGES (ds_sla MAPE, ds_mape_trend) are NOT pre-divided in the serving table.
  We store `sum_abs_var_pct` + `cnt_mape` per org×week; thin query does SUM/SUM over the picked
  weeks → identical number to the live AVG. Percentile tiles (abc_median, varpct) can't be made
  additive, so they're whole-window in the serving MV (documented; wk param dropped for those two).
- ds_week avg_bias_pct: stored per-week already; a whole-window re-display weights by items — the
  live tile shows PER-WEEK avg (its GROUP BY is week), so per-week stored avg_bias_pct is EXACT.

## Datasets kept as raw over sdp_plan_vs_actual (still fast — filter, don't aggregate base)
ds_pva, ds_imbalance, ds_drill_sku, ds_drill_field, ds_cp_aging, ds_drill_onhand_long,
ds_drill_flows_long. These are row-level/drill tiles whose live query already FILTERS (sku/org/one
week) rather than scanning all 590k for an aggregate. sdp_plan_vs_actual is CLUSTER BY item_id so
sku-drills prune. Perf-gate check: confirm each returns ≤ few hundred rows at default params.
