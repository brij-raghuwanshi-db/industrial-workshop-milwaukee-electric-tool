<div align="center">

# V8 · Forecast Bias / Accuracy (governed `fact_forecast_accuracy`) — Validation

</div>

**Claims (DK-7):** MKE's own governed accuracy fact carries **planner_bias vs system_bias** (a split we can't
derive empirically), + error/cost, lag-3, rolling-6. Prefer it over the empirical `10_demand_daily` computation.
**Source:** `prod_operations.demand.fact_forecast_accuracy` + `dg5_customer_scd1`.

---

## Test — planner vs system bias, 10 customers (governed fact)

| # | customer | planner_bias | system_bias | pos error | neg error | lag-3 fcst |
|---|---|---|---|---|---|---|
| 1 | ECOMM | −1,578,751 | −1,453,865 | 2,614,268 | 749 | 3,026,151 |
| 2 | CAN REGIONAL | +1,250,797 | +1,161,097 | 1,551,624 | 10,907,001 | 2,404,928 |
| 3 | CAN FIELD | −739,629 | −588,054 | 12,189,603 | 3,257,600 | 23,709,467 |
| 4 | NEFCO | +683,207 | +685,668 | 1,490,240 | 6,960,134 | 3,045,236 |
| 5 | HOME DEPOT | −587,166 | −581,035 | 114,773,976 | 69,867,811 | 424,490,334 |
| 6 | SIS COMP | −425,901 | −352,396 | 5,817,474 | 121,008,045 | 12,848,093 |
| 7 | **HDW FLD** | **−380,873** | **−246,844** | 3,113,106 | 1,972,703 | 8,052,525 |
| 8 | THD CAN | −376,708 | −300,468 | 11,452,599 | 7,237,057 | 26,766,400 |
| 9 | CONST_IND | +361,077 | +402,653 | 21,510,415 | 11,615,428 | 50,671,310 |
| 10 | ACE | −338,302 | −181,870 | 14,325,445 | 8,725,180 | 46,250,683 |

## 📖 The story the data tells

This is the screen that answers a question the planners *couldn't* answer before: **is the forecast miss the
model's fault or the human's?** The governed fact splits it, and the data tells a genuinely useful story.

For most customers planner and system bias move together (ECOMM both ~−1.5M, HOME DEPOT both ~−0.58M) — the
human is broadly trusting the model. But the interesting cases are where they **diverge**: `HDW FLD` has planner
bias −380,873 vs system bias −246,844, and `ACE` −338,302 vs −181,870 — meaning **the planner override is
*adding* roughly 130–155k of extra bias on top of the model.** That's the Forecast-Value-Added signal the
research pointed to: on these customers, the human touch is making the forecast *worse*, not better. Conversely,
where system bias ≈ planner bias, the override is neutral.

The direction also tells a story consistent with V3: most large biases are **negative** (under-forecast), echoing
the chronic under-forecasting that drives the supply team's shortages. But note **CAN REGIONAL and CONST_IND are
positive** (over-forecast) — so the bias isn't uniform; some Canadian/industrial customers are over-planned,
which ties to *excess* (V7), not shortage. The bias board is where the demand story splits into its two failure
modes.

## Verdict: ✅ works — governed fact is the right source; the planner-vs-system split is a genuine new capability

**What works ✅**
- The governed fact returns cleanly; **planner_bias and system_bias side-by-side** is the standout — impossible
  empirically, and directly answers the FVA "human or model?" question.
- Positive/negative error + lag-3 forecast populate well; sensible magnitudes.

**Data-quality findings**
- 🟡 **DQ-1 — bias columns are pre-aggregated sums, units unclear.** `planner_bias` is a signed unit total; to
  turn it into a *rate* (bias %) divide by the forecast base (`working_final_forecast_lag3_units`). Present as a
  % for comparability across customers of different size.
- 🟡 **DQ-2 — lag-3 only.** This fact is locked to lag-3 (DK-10); for lag-1/other-lag stories, fall back to the
  `10_demand_daily` self-join (V3). Label the lag on the screen.
- 🟢 **DQ-3 — no join surprises** — conforms to `dg5_customer_bigint_key`; clean.

## 🔍 Root causes

| Finding | Root cause |
|---|---|
| Planner bias > system bias on some (HDW FLD, ACE) | **planner overrides adding error** — the FVA failure mode; the human is over-adjusting a decent model forecast |
| Mostly negative bias | systematic under-forecast (consistent with V3) |
| Some positive (CAN REGIONAL, CONST_IND) | over-forecast segments → feed the excess/E&O side, not shortage |

## ✅ Recommendations & actions to take

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | **Use the governed `fact_forecast_accuracy`** as the bias source (not empirical) — it's authoritative + splits planner/system | build | 🔴 must |
| 2 | Present bias as a **% of forecast base** for cross-customer comparability (DQ-1) | build | 🟡 should |
| 3 | Add a **"planner override is hurting" flag** where `|planner_bias| > |system_bias|` (the FVA insight) | build | 🟡 should — high value |
| 4 | Label **lag-3**; offer lag-flex via V3 self-join when needed (DQ-2) | build | 🟡 should |
| 5 | Route positive-bias (over-forecast) customers to **excess/E&O (V7)**, negative-bias to **shortage/demand-handoff** | planner | 🟡 should |

---

## ✅ Logged successful query

```sql
-- V8: planner vs system bias by customer, governed fact (READ-ONLY).
SELECT c.mkedg5,
       ROUND(SUM(fa.planner_bias),0) planner_bias,
       ROUND(SUM(fa.system_bias),0)  system_bias,
       ROUND(SUM(fa.positive_error),0) pos_err,
       ROUND(SUM(fa.negative_error),0) neg_err,
       ROUND(SUM(fa.working_final_forecast_lag3_units),0) fcst_l3
FROM prod_operations.demand.fact_forecast_accuracy fa
JOIN prod_edw.dimension.dg5_customer_scd1 c ON fa.dg5_customer_bigint_key=c.dg5_customer_bigint_key
GROUP BY c.mkedg5
HAVING SUM(fa.working_final_forecast_lag3_units)>10000
ORDER BY ABS(SUM(fa.planner_bias)) DESC LIMIT 10;
```

**Note:** reason codes (`dim_forecast_accuracy_reason_codes`) are a **reference picklist**, not joinable here
(no FK on the fact) — surface as a UI vocabulary / `ai_classify` target (per join-doc hazard #11).
