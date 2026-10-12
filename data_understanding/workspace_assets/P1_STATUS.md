# P1 "Actuals Supply Plan" — Status Scorecard (post-SDP pipeline)

Honest mapping of the requirement doc (`customer_requirements/Actuals_Supply_Plan_Requirements.md`)
to what is built. **The SDP pipeline neither adds nor drops a calculation** vs the live dashboard —
it re-expresses the same source reads declaratively and pre-aggregates for scale. "Open" items here
are the SAME ones that were open before this pass.

Legend: ✅ done & verified · 🟡 partial (carried-forward, same as pre-SDP) · ⬜ not started (out of this pass)

## 2.1 Snapshot Capture
| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| 2.1.1 | Weekly snapshot cadence | ✅ | Lakeflow Job `p1_actuals_weekly_sdp`, Mondays 07:57 CT (before 8AM S4), paused until go-live. |
| 2.1.2 | On-hand snapshot | ✅ | `sdp_actuals_weekly` point-in-time on-hand (semi-additive, never summed across dates). |
| 2.1.3 | Planned PO snapshot | ✅ | `sdp_planned_weekly.planned_pab` + PO stages from lead-time source. |
| 2.1.4 | Planned customer-order snapshot | ✅ | `planned_sales_orders` in silver. |
| 2.1.5 | Historical retention | ✅ | Delta MVs retained; incremental appends weekly (SDP-managed). Backfill widen 4mo→180d = 1-line change. |
| 2.1.6 | Snapshot metadata | ✅ | `_load_ts` on silver; SDP run_id per update in pipeline event log. |

## 2.2 Connect to Existing Snapshot Process
| 2.2.1 | Integration w/ existing framework | ✅ | Reads `prod_edw.fact.20_supply_daily` (the existing snapshot); Lakeflow pipeline+job = managed scheduling. |
| 2.2.2 | Historical supply-plan access | ✅ | prior-week baseline join in `sdp_plan_vs_actual`. |
| 2.2.3 | Consistent grain (SKU/Org/Week) | ✅ | gold grain = item×org×week; DQ-verified rows==distinct. |
| 2.2.4 | Snapshot versioning | 🟡 | snapshot_week carried; explicit version-compare UI not built (same as pre-SDP). |

## 2.3 Compare Actuals to Prior Plan
| 2.3.1 | Week-over-week | ✅ | prior-week baseline + cockpit newly-red (WoW status transition). |
| 2.3.2 | Month-over-month | ✅ | `sdp_agg_mom`. |
| 2.3.3 | PO receipt vs plan | ✅ | actual_po_received vs plan; PO timing `sdp_agg_po_timing`. |
| 2.3.4 | Sales order vs plan | ✅ | shipped_variance_abs. |
| 2.3.5 | On-hand vs plan | ✅ | onhand_variance_abs/pct/dollar (the central metric). |
| 2.3.6 | Variance abs & % | ✅ | both computed in gold. |
| 2.3.7 | Root-cause categorization | ✅ | `sdp_agg_rootcause_dc` (6-cat DC signal attribution) + `sdp_rootcause_plant` (5-cat plant ledger, labelled upstream tier, not summable w/ DC). Residual cut 80%→41%. |

## 2.4 Compare Live Plan to History
| 2.4.1 | Current plan vs historical actuals | ✅ | plan evolution + overlay tiles. |
| 2.4.2 | Plan accuracy trending | ✅ | FVA (`sdp_agg_fva`) + MAPE trend (`sdp_agg_week_org`). |
| 2.4.3 | Bias detection | ✅ | `sdp_agg_bias_persist` (persistently over/under), `sdp_agg_abc`. |

## 5.2 Metrics (M1–M5)
| M1 PO receipts | ✅ | M2 Sales shipped | ✅ | M3 Ending on-hand | ✅ (central) |
| M4 PO timing (weeks early/late) | ✅ `sdp_po_stages`/order_stage_gold | M5 Demand vs plan | 🟡 partial (planned SO vs shipped; no separate demand-signal split — same as pre-SDP) |

## O6/O8 KPIs & thresholds
| On-Hand MAPE <15% | ✅ computed | PO on-time rate | ✅ (pct_late→on-time) | PO qty-accuracy % | 🟡 not a named KPI | Demand accuracy % | 🟡 not a named KPI |
| Alert tiers 15/30/50% + $50K/$200K | ✅ `alert_tier` exact | **ABC-tiered thresholds (A 10/20/40, C 25/50/75)** | 🟡 flat thresholds today — carried-forward gap, same as pre-SDP |

## 7 Technical
| T1 weekly pipeline | ✅ Job | T2 idempotent | ✅ MV recompute is idempotent | T3 late data | 🟡 weekly re-materialize catches it; no explicit late-window | T4 point-in-time align | ✅ Monday snapshot |
| T5 data validation | ✅ SDP EXPECT (4 constraints, 0 violations) | T6 alert on failure | ✅ Job on_failure email | T7 backfill | ✅ full-refresh backfills the window |

## 7.2 Performance (P5/P6 — the point of the SDP pass)
| P5 single-SKU < 5s | ✅ sku-drill scans 32 rows (clustered by item_id) | P6 category summary < 30s | ✅ aggregate tiles read 2–160-row serving MVs (was 590k live). |

## What this pass did NOT do (explicitly out of scope)
- Full 126-org network (stays 2012+2120; widen = param change). 
- 180-day backfill (verify-then-widen: 4mo now, flip pd_lo after equivalence — user decision).
- The App (roadmap step 3): clickable approve/reject/expedite, Lakebase real-time state,
  SIMULATED writeback (no real Oracle — guardrail).
- S1–S4 success criteria (adoption/time-saved/parallel-run) — human/calendar.
- Named KPIs PO-qty-accuracy% & demand-accuracy%, and ABC-tiered thresholds — carried-forward
  gaps identical to the pre-SDP dashboard (NOT introduced by this pass).

## Deliverables of this pass
- SDP pipeline `p1_actuals_sdp` (35 MVs: 4 silver + 3 gold + 28 serving) — id b6f16cf7-…
- Weekly Job `p1_actuals_weekly_sdp` (paused) — id 418760739520160
- Clone dashboard "P1 Actuals — SDP (Rung 2)" — id 01f1a5371959178aa137d5551347afff (thin queries)
- Original dashboard 01f1a50aed891d5c85b5e64b2c3c5d5b + rung2_*/p1flow_* tables: UNCHANGED (safety net)
- Evidence: SDP_VERIFICATION_LOG.md (all test queries+results), SDP_THIN_QUERY_MAP.md
