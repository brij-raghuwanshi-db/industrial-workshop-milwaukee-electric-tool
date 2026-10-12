# V — Extreme variance: "too much variance" + forecasted-X-but-actual-Y

**As-of 2026-08-30 · READ-ONLY · profile mke-rsc.** Real numbers. Two cuts the user asked for:
(1) the biggest plan-vs-actual ON-HAND variances; (2) demand FORECAST vs ACTUAL shipped.

## V1 — Largest plan-vs-actual ON-HAND variance (the "too much variance" tail)
Compared plan PAB (20_supply_daily, snapshot 20260829, week 20260824, 20 Global) vs actual on_hand
(inventory_days_on_hand, 20260829), same item×org. Top absolute gaps:

| item_id | description | ABC | org | planned PAB | actual OH | variance | var% |
|---|---|---|---|--:|--:|--:|--:|
| 88930100 | CARBIDE CYLINDER MS12 | D | 1019 Grenada (plant) | 34.99M | **87.99M** | **+53.0M** | +151% |
| 88930110 | CARBIDE CYLINDER MS10 | D | 1019 (plant) | 11.75M | 19.12M | +7.37M | +63% |
| 48223100P | INKZALL BLACK MARKER (36) | **A** | 2013 OB-Home Depot | 1.58M | 0.73M | **−849,600** | −54% |
| PN0013905 | COIL STOCK | — | 8000 (supplier inv) | 34,284 | 555,186 | +520,902 | **+1,519%** |
| 48223100P | INKZALL BLACK MARKER (36) | **A** | 2012 Olive Branch | 1.32M | 0.68M | −634,176 | −48% |

**Reading it (honest):** the biggest RAW variances are **low-value components/coil-stock at plants (1019)
and supplier-inventory orgs (8000)** — same lesson as S5: raw magnitude over-weights cheap parts and
non-DC orgs. The variances that a planner should ACT on are the **A-items at real DCs**: Inkzall Marker is
**~48–54% BELOW plan at both Olive Branch and its Home Depot DC** — a genuine finished-goods shortfall vs
plan. ✅ this ranking, once weighted by cost×ABC×org-role, is the P1 variance exception list.

> Grain caveat: PAB summed over the week's rows (series/order_type split); on_hand is point-in-time at
> week-end. Directional variance, not a signed audit. Alert tiers (Monitor >15% / Alert >30% / Escalate
> >50%) apply — most rows here are Escalate-tier by %.

## V2 — Demand FORECAST vs ACTUAL shipped (forecasted X, happened Y)
Forecast (10_demand_daily working_final_forecast, snapshot 20260727, target week 07/27–08/03) vs actual
shipped that week (sales_order_line_transactions, Standard, Invoiced/Closed). Biggest misses:

| item_id | description | ABC | forecast (wk) | actual shipped (wk) | miss |
|---|---|---|--:|--:|--:|
| 48223100 | INKZALL BLACK MARKER (36) | A | 269,548 | 4,212 | **−265,336** |
| 48221725 | 25' COMPACT TAPE (5) | A | 129,493 | **0** | −129,493 |
| 48223104 | 4PK INKZALL MARKER | A | 149,467 | 23,173 | −126,294 |
| 48221950 | 50PC UTILITY BLADES | A | 138,814 | 15,347 | −123,467 |
| 48228911/12 | CUT-1 WINTER GLOVES M/L | A | 107,820 each | **0** | −107,820 each |
| 48228902W | DUMP BIN CUT-1 GLOVES L | A | 103,600 | **0** | −103,600 |

**Reading it:** forecast **massively exceeds** actual for these A-items — several forecast 100K+ and shipped
**zero** that week. This is the **phantom-demand pattern (P-file)** seen as a plan-vs-actual miss: either the
forecast is inflated / mis-timed, or demand is lumpy (winter gloves in a July week = seasonality). Either
way it's a **P4 exception** (forecast not tracking actual) and a **P1 demand-variance** driver. ✅ answers
"what did we forecast that didn't happen?"

> Grain caveat: forecast summed across customers at product grain; actual at item grain for the same Monday
> week. Winter gloves forecast in late July strongly suggests a seasonal/timing mismatch, not pure error —
> the P4 rule must be seasonality-aware before flagging.

## What both cuts confirm
- **Weight by cost × ABC × org-role** before ranking any variance — raw magnitude points at penny components
  and non-DC orgs (recurring lesson across S5, V1).
- The **forecast>>actual** gap and the **phantom-demand** finding are the same phenomenon from two angles —
  a strong candidate for the first P4 rule (with seasonality guard).
- These are the "not happy" plan-vs-actual stories in real data, and they cluster on **A-items where it
  matters** once you filter the noise.
