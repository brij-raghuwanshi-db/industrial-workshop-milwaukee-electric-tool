# Dashboard claims → provenance queries

Every numeric claim in `MKE_supply_chain_story.html` paired with a **re-runnable READ-ONLY** query and the
returned value. Re-verified 2026-08-31 on profile `mke-rsc`. Nothing here writes; all `prod_edw` reads.
Figures explicitly marked **[illustrative]** carry no query (design targets, not measurements).

## KPI row (Story tab)
| Claim | Value | Query (READ-ONLY) |
|---|---|---|
| Plan fact rows / snapshots | 13.4B / 366 | `SELECT COUNT(*), COUNT(DISTINCT process_date) FROM prod_edw.fact.\`20_supply_daily\`` (13,453,838,582 / 366) |
| Items / PurchPlan ("Status 20") | 299,966 / 8,716 | `SELECT COUNT(*), SUM(CASE WHEN item_status='PurchPlan' THEN 1 ELSE 0 END) FROM prod_edw.dimension.items_scd1` |
| On-hand inventory value | $1.678B | `SELECT ROUND(SUM(on_hand_cost),0) FROM prod_edw.fact.inventory_days_on_hand WHERE date_key=20260829 AND on_hand_cost>0` |
| Past-due PO lines | 355,999 | `SELECT COUNT(*) FROM prod_edw.fact.purchase_orders WHERE order_status='OPEN' AND received_quantity=0 AND ordered_quantity>0 AND promised_delivery_date_key<20260829 AND promised_delivery_date_key>=20260101` |

## Story — hero battery (item 48111850 @ org 776578178872804310)
| Claim | Value | Query |
|---|---|---|
| On-hand trajectory (8/24→8/29) | 108,309→70,166→83,254 | `SELECT date_key,on_hand_qty FROM prod_edw.fact.inventory_days_on_hand WHERE item_bigint_key=3879620845706693458 AND inventory_organization_bigint_key=776578178872804310 AND date_key BETWEEN 20260824 AND 20260829 ORDER BY date_key` |
| **Semi-additive trap: 538,116 vs 83,254** | 6.5× | `SELECT ROUND(SUM(on_hand_qty),0) wrong, MAX_BY(on_hand_qty,date_key) right FROM prod_edw.fact.inventory_days_on_hand WHERE item_bigint_key=3879620845706693458 AND inventory_organization_bigint_key=776578178872804310 AND to_date(cast(date_key AS string),'yyyyMMdd') BETWEEN DATE'2026-08-24' AND DATE'2026-08-30'` → wrong 538,116 / right 83,254 |
| Plan projection for the week | 60,121 | plan PAB from `20_supply_daily` (process_date=20260829, date_key=20260831, hero item/org, '20 Global Supply Plan') |
| Org on-hand distribution | Olive Branch 83,254; OB-HD 63,273; Byhalia 9,168; 3PL CA 7,019; MX 2,077; Indy 1,950 | `SELECT inventory_organization_bigint_key, on_hand_qty FROM prod_edw.fact.inventory_days_on_hand WHERE item_bigint_key=3879620845706693458 AND date_key=20260829 ORDER BY on_hand_qty DESC` (join org dim for names) |
| Three traps: $0.0134 / PAB 151,929→−3,464 | see P2 & below | S5 enrichment + T snapshot-flip queries (data_stories/S5, T) |

## Business Questions tab
| Claim | Value | Query / source |
|---|---|---|
| Weekly shipped series (~24–57K) | 57,013 peak (wk 07-05) … 24,189 (08-23) | `SELECT date_trunc('week',fulfillment_timestamp) wk, SUM(shipped_quantity) FROM prod_edw.fact.sales_order_line_transactions WHERE item_bigint_key=3879620845706693458 AND order_type='Standard' AND sales_fulfillment_line_status IN ('Invoiced','Closed') AND shipped_quantity>0 AND fulfillment_timestamp>='2026-07-01' GROUP BY 1 ORDER BY 1` |
| PO fulfillment matrix (1.23M fully / 356K past-due / 27,683 partial / +23M over) | see values | the CASE-by-state query in `data_stories/R_received_notreceived.md` §R1 (READ-ONLY) |
| Forecast≫actual: Inkzall 269,548 vs 4,212 (+ others) | see values | the forecast-vs-actual query in `data_stories/V_extreme_variance.md` §V2 |
| Breach: 17.6M units = $0.0134 part → ~$235K | 88930100 @ 1019 | items+dim_series_ext_vw join in `data_stories/S5_stockout_priority.md` (RESOLVED ENRICHMENT) |
| Beyond: ~$4–5B overdue PO (deduped from $10.8B raw) | 166,547 distinct vs 378,884 raw lines | dedup query in `data_stories/LOSS_supply_chain_losses.md` §L2 — shows the SCD2 2.3× inflation |
| Beyond: phantom demand 8.4M units | top-25 pairs | query in `data_stories/P_hidden_patterns.md` Pattern 1 |

## P1 slice (proven live in the vertical-slice build, 2026-08-31)
| Claim | Value | Evidence |
|---|---|---|
| Gold received ties to raw (wk 08-10) | 382,144 = 382,144 | Recon A, `workspace_assets/P1_SLICE_BUILDLOG.md` |
| applied_standard_cost (hero, real A-item) | $26.9609/unit | `p1slice_planned_weekly` / dim_series_ext_vw |

## Illustrative figures (NO query — labeled as such in the HTML)
- **Pipeline tab → "How the architecture lifts the outcome"**: 15 min→30 sec, ~15 gotchas→0, many→0 wrong,
  manual→auto routing. These are **design targets from the pain journey**, not measurements. The HTML
  figcaption already says "illustrative targets."

## Reconciliation note
All headline KPIs and the semi-additive/receipt figures re-verified exact on 2026-08-31. If any future
re-run diverges (data refreshes daily), update BOTH this file and the corresponding value in the HTML —
they must stay in lockstep. The dashboard is only as trustworthy as this provenance.
