<div align="center">

# 🆔 Scenario → Real-ID Catalog

### ≥50 distinct live business IDs for every scenario identified across all activities — with the exact successful query for each

**Source:** live READ-ONLY extraction on Databricks profile **`mke-rsc`**, warehouse `7bd33a82f4e92206` (2026-09-03).
**ID column:** `prod_edw.dimension.items_scd1.item` (Milwaukee selling SKU) — except V8 which uses the governed `fact_forecast_accuracy.selling_item_number`.
**Guardrail:** every query is READ-ONLY against `prod_edw` / `prod_operations`. No writes. Latest supply snapshot; forward window to 2026-11-30 unless noted.

> **Update 2026-09-03:** V17 (N3 Returns/warranty) — **previously believed unreachable** (thought to live only in JDE/AX staging keyed on `tool_nbr`) — was found to have a **governed, item-keyed conformed fact** (`prod_edw.fact.warranty_transaction.item_bigint_key`). It now has 60 real IDs like every other scenario. **All 26 scenarios now resolve to real EDW SKUs.**

</div>

---

## Scoreboard — 26 scenarios, all ≥50 IDs

| # | Scenario | Maps to | Req | # IDs | Source |
|---|----------|---------|-----|:-----:|--------|
| V1 | Watchlist / top-missing items | Act 1 | R3, R4, C.5·1 | **60** | `20_supply_daily` |
| V2 | Hard projected stockout (PAB<0) | Act 4 | R6, R7, D, PAB recursion | **60** | `20_supply_daily` |
| V3 | Demand surprise / consumption | Act 2 | R14, R15, R16, D | **60** | `10_demand_daily` |
| V4 | Supply / PO slip | Act 5 | C.5·5, Pareto-supply, R27 | **60** | `purchase_orders` |
| V4b | Who-moved-it (supplier-initiated) | Act 5 | C.5·5 attribution | **60** | `purchase_order_change_orders` |
| V5 | Holds / fulfillment blocks | Act 6 | C.2·3, Pareto-tail | **60** | `sales_fulfillment_hold_transactions` |
| V6 | Cross-org rebalance | Act 7 | R5, C.4 | **60** | `transfer_orders` |
| V7 | Excess / overstock (E&O) | Scenario 1 | DK-17 excess, S1 | **60** | `20_supply_daily` |
| V8 | Forecast bias (governed) | Scenario 5 / DK-7 | D, R15, C.6 | **60** | `fact_forecast_accuracy` |
| V9 | Forward risk (coming-risk) | Gap 1 | G1, DK-9 | **60** | `20_supply_daily` |
| V10 | Chronic (repeat offender) | V10 / Gap 5 | G5, temporal_class | **60** | `20_supply_daily` |
| V11 | Convergence (multi-cause) | DK-13 | DK-13 convergence | **60** | `20_supply_daily ∩ purchase_orders` |
| V12 | Do-nothing / false-alarm | DK-14 | DK-14 action-verdict | **60** | `20_supply_daily` |
| V13 | Recoverability (committed loss) | DK-15 | DK-15 recoverability | **60** | `20_supply_daily + dim_series_ext_vw` |
| V15 | Lifecycle — transition / NPD | N1 / DK | N1, lifecycle_class | **60** | `items_scd1` |
| V16 | Over-forecast → excess driver | N2 | N2 | **60** | `10_demand_daily` |
| V17 | Returns / warranty / reverse logistics | N3 | N3, DK reverse-logistics | **60** | `fact.warranty_transaction` |
| V18 | Found-inventory / phantom heal | N4 | N4, S10 | **60** | `inventory_material_transaction` |
| V19 | Non-standard demand channels | N5 | N5 | **60** | `10_demand_daily + dg5_customer_scd1` |
| V20 | Component / multi-org items | N6 | N6 | **60** | `20_supply_daily` |
| V21 | Recovery velocity (slow release) | N7 | N7 | **60** | `sales_fulfillment_hold_transactions` |
| V22 | Criticality — A-class ABC | DK-16 | DK-16 criticality_class | **60** | `dim_series_ext_vw` |
| V23 | Dormant / obsolescence (E&O) | DK-17 | DK-17 dormant_flag | **60** | `10_demand_daily` |
| V24 | Intermittent demand | DK-18 | DK-18 demand_class | **60** | `10_demand_daily` |
| V25 | Parameter / SS review candidate | DK-19 | DK-19 proposal-queue | **60** | `dim_series_ext_vw` |
| V26 | Intentional-hold (managed SS) | DK-20 | DK-20 intentional_hold | **60** | `dim_series_ext_vw` |

> Every count is distinct real IDs returned by the query shown in that scenario's section. `LIMIT 60`; all returned the full 60.


---

## V1 · Watchlist / top-missing items

- **Maps to:** Act 1 — requirements **R3, R4, C.5·1**
- **Predicate / logic:** PAB<safety_stock, latest snapshot
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND s.projected_available_balance < s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-25-1252, 48-27-0180, 48-32-4171, 48-32-4579, 48-32-4815, 48-40-0720, 48-62-4082, 48-73-1321, 48-73-1410, 49-16-W247
49-57-5166, 49-66-6122, 49-66-6624, 49-90-1979, 50-44-0260, 604BL-XL, 606B-XL, 77-0204, 3401-20, M650K-3632
49-66-6157T, 49-66-6204T, 49-66-6262T, 48-47-5711, CPPLH2001, CPPL2201, BLO1436, F452G-XLD, 48-89-2217T, 2772A-21J
2821-21J, 2161-21J, PN0006103, PN0006130, PN0006141, 48-22-7718V, 45-34-1047T, 45-34-9086T, 49-94-0613, 2779-750CUZ
45-34-2122T, 45-34-2124T, 45-34-4000T, 45-34-9052T, 45-34-9053T, 45-34-9101T, 48-73-7920V, 2941-21Z, 48-73-5021BY, 48-73-5071BY
2123-21HDJ, 49-66-6654, 49-66-6672, 2971-20M, 48-89-4870K, 49-90-1976, 48-22-3260X, 51-16-2651ZX, 48-81-4780, 48-81-7760
```

---

## V2 · Hard projected stockout (PAB<0)

- **Maps to:** Act 4 — requirements **R6, R7, D, PAB recursion**
- **Predicate / logic:** PAB<0
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND s.projected_available_balance < 0 AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-39-0601, 48-39-0616, 48-62-4074, 48-62-4082, 48-73-1221, 48-73-1232, 48-73-1321, 48-73-1501, 49-16-2650, 49-57-5166
49-59-2200P, 49-90-1979, 49-93-7025, 602HV-XL, 606B-XL, 83-3, MLBX78, TBRG-B, 3401-20, 204-SS
58-10-7021, M650K-3632, 48-32-4089ZA, M102B-L-W, BLO1436, F452G-XLD, 2772A-21J, 2161-21J, 3632-21PO, MT210X
PN0004637, 48-22-7718V, 2941-21Z, 48-73-5021BY, 3650-21PMAN, 48-73-5071BY, 2971-20M, 49-90-1976, 2118-20, 3651-21XCW
MT203H, 51-16-2651ZX, 48-81-4780, 48-81-7760, FG58-28-0696, 58-31-8235, 48-22-9486T, 48-32-4289, 48-22-8933V, 48-73-1097
48-73-1331, 48-73-3151P, 48-73-5072, 48-89-4632, 49-16-U001C, 49-22-4036, 49-66-5124, 49-66-6376, 49-66-6642, 49-94-4510
```

---

## V3 · Demand surprise / consumption

- **Maps to:** Act 2 — requirements **R14, R15, R16, D**
- **Predicate / logic:** SUM ship>1.5×SUM fcst Jan–Sep26
- **Primary source:** `10_demand_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,SUM(d.shipments_history) act,SUM(d.final_demand_forecast) fc FROM prod_edw.fact.`10_demand_daily` d JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`) L ON d.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key=i.item_bigint_key WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan') AND d.date_key BETWEEN 20260101 AND 20260901 AND i.item IS NOT NULL GROUP BY i.item) t WHERE fc>0 AND act>1.5*fc AND act>0 LIMIT 60
```

**IDs:**

```
48-32-4145, 48-32-4171, 48-32-4191, 48-32-4846, 48-32-4020, 48-32-4142, 48-25-5143, 48-32-4118, 48-39-0551, 48-32-4194
48-20-9130, 48-32-4786, 48-32-4112, 48-62-4061, 48-62-4098, 48-66-6503, 48-25-5420, 48-25-5220, 48-25-5235, 48-32-4862
48-52-1305, 48-25-5240, 48-32-4025, 48-40-4355, 48-25-5550, 48-32-4189, 48-32-4244, 48-32-4397, 48-44-0155, 48-32-4671
48-32-4832, 48-62-3010, 48-28-1000, 48-32-4431, 48-32-4687, 48-32-4711, 48-32-4195, 48-32-4135, 48-25-5335, 48-32-5720
48-32-4597, 48-32-5020, 48-40-4108, 48-32-4394, 48-32-4115, 48-44-0270, 48-20-9111, 48-32-4442, 48-32-4614, 48-32-4163
48-32-4172, 48-25-5325, 48-32-4801, 48-32-4182, 48-62-4062, 48-89-2214, 48-28-6880, 48-32-4734, 48-32-4847, 48-32-4155
```

---

## V4 · Supply / PO slip

- **Maps to:** Act 5 — requirements **C.5·5, Pareto-supply, R27**
- **Predicate / logic:** promised>original promised
- **Primary source:** `purchase_orders`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.purchase_orders po JOIN prod_edw.dimension.items_scd1 i ON po.item_bigint_key=i.item_bigint_key WHERE po.promised_delivery_date_key>po.original_promised_delivery_date_key AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
49-56-9639, 48-47-5711, 49-90-0910, 58-68-8112, M300N-L9-J, 48-17-0025, 49-22-2731, 49-57-5166, 58-22-0312, 58-46-3880
58-46-4726, 14-46-0507, 49-16-2764, 58-10-1307, 58-46-3330, 58-38-0222, 58-42-2008, 58-68-0124, 52-76-6672, 77-1002T
58-46-4769, 49-66-4502, 58-68-4592, 58-46-1707, 58-14-0525, 58-22-1080, 48-20-5005, 58-10-1504, 48-85-1101, 58-46-1346
58-46-3138, 58-46-3125, 48-20-3986, 10-97-1082, 48-32-4678, 48-32-4660, 10-05-5077, 52-76-0169, 58-10-0411, 48-73-2241
58-08-4814, 2132-ST, 58-42-0111, 34-40-0045, 48-73-1331C, 2738-ST, 49-22-1113R, 49-56-9100E, 49-93-9104, 58-09-1515
58-46-4124, 51-16-2451C, 58-46-4831, 10-20-6570, 2572B-21, 58-31-0682, 58-50-0090, 52-80-0147, 58-38-0224, 58-46-1865
```

---

## V4b · Who-moved-it (supplier-initiated)

- **Maps to:** Act 5 — requirements **C.5·5 attribution**
- **Predicate / logic:** change_order_originator_type=SUPPLIER
- **Primary source:** `purchase_order_change_orders`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.purchase_order_change_orders co JOIN prod_edw.fact.purchase_orders po ON co.source_bigint_key=po.source_bigint_key JOIN prod_edw.dimension.items_scd1 i ON po.item_bigint_key=i.item_bigint_key WHERE co.change_order_originator_type='SUPPLIER' AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
3651-21XCW, MR023339, 06-82-8995, 49-66-6227T, 31-107T, 40-50-8937, 31-44-0408, PN0010630, 14-32-0012, 0852-20
48-89-2207, 43-35-0925, 634A00274, 49-94-0013, 49-56-9639, 31-15-0066, 2882-22, 28-28-1700, 48-73-2052, 30-75-0150
77-0204, STLHDL-S, 28-50-4139, 50-59-1812W3, 14-20-1204, 2533-21, 18-07-0176, 58-15-0426-02, 14-46-0709, MR104374
32-30-8001, 14-46-0290, 48-40-0720, 58-95-0075-02, 48-22-6105D, 48-73-8922V, 48-32-4788, 58-12-0763, 2677-04, 28-06-0012
48-32-5033, 05-81-5465, 58-10-1310, 48-20-9006Y, 964M00012, 42-06-0013, 49-68-9842, 48-41-0720, 48-22-8901F, 28-50-0027
48-11-2422, 48-20-7411, 2160-21J, 48-22-8436, PN0003608, 49-16-KITC, 14-38-0095, 3404-W3497, 49-56-7010, 48-73-8512X
```

---

## V5 · Holds / fulfillment blocks

- **Maps to:** Act 6 — requirements **C.2·3, Pareto-tail**
- **Predicate / logic:** hold_apply_date_key>=Aug26
- **Primary source:** `sales_fulfillment_hold_transactions`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.sales_fulfillment_hold_transactions h JOIN prod_edw.dimension.items_scd1 i ON h.item_bigint_key=i.item_bigint_key WHERE h.hold_apply_date_key>=20260801 AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
49-90-0910, 48-47-5711, 49-56-9639, 415B-LD, 44-10-0062, 34-60-0051, 48-00-5227, 49-66-6713T, 48-73-1362, 49-56-9649CA
48-20-6713T, 2672-20Z, 48-73-2241, 49-93-9104, RK58-28-0052U, 49-56-9100E, 49-16-B500, 48-22-8902WM, 48-89-2218T, 2585-ST
0910-20Y, 49-57-5115, 49-56-9605CA, 2845-20, 49-66-6512T, 48-62-4000, 48-22-8439, 48-73-1206C, F200U-21XL, 49-25-2202
49-08-5265, 48-00-5262PC, 42-86-0010, 49-94-0533, 23-66-1100, 48-22-9052, 49-66-6515, 48-00-5563, 2557-20, 48-73-1302
6232-21, 48-22-8690, 48-62-4005, M300B-212X, 48-22-8392R, 48-59-1881, 43-24-9116T, 49-22-1110W, 48-73-1351, 45-88-1515
43-24-9304, 48-73-1096, 2954-20, 48-22-9487T, 0818-20, 48-73-6966, 605GN-LD, 44-60-0850, 48-73-2501, E105.48
```

---

## V6 · Cross-org rebalance

- **Maps to:** Act 7 — requirements **R5, C.4**
- **Predicate / logic:** open transfer, src<>dest
- **Primary source:** `transfer_orders`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.transfer_orders t JOIN prod_edw.dimension.items_scd1 i ON t.item_bigint_key=i.item_bigint_key WHERE t.status='Open' AND t.source_inventory_organization_bigint_key<>t.destination_inventory_organization_bigint_key AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-32-4662CA, 14-29-3874, 18-01-2120, 42-14-0017, 05-74-0028, 49-66-6144, 02-04-0019, M200B-XLREC, 45-88-1140, 49-94-0501
14-50-0060, 48-66-3280, 14-05-0015, 49-94-0647, 23-81-0510, 2633-20, 49-25-2060, 48-22-2604P, 14-30-0123, 43-44-4001
48-22-6826, 48-22-6537, 44-20-0200, MXF302-2HDZ, F251G-MD, 31-44-0149, M552G-L, 22-64-1422, 42-66-0100, 49-12-KITA
48-22-8924, 48-22-9065, M200B-M9, 38-50-6020, 48-89-9224, 31-12-0041, 43-82-0205, 45-96-9514, 14-46-3413, 48-73-7024M
14-20-0328, 43-44-1200, 14-46-9498, 44-52-0605, 44-66-0011, 05-81-9045, 48-22-8823, 31-01-1910, M200R-XL9, 14-30-2890
48-20-5428, 28-14-1030, 31-05-0140, 34-40-8005, 28-14-0085, 44-60-0855, 28-35-0110, 14-20-2020, 23-26-0031, 49-90-2400
```

---

## V7 · Excess / overstock (E&O)

- **Maps to:** Scenario 1 — requirements **DK-17 excess, S1**
- **Predicate / logic:** PAB>3×SS
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND s.safety_stock>0 AND s.projected_available_balance>3*s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-22-8929, 48-27-1520, 48-32-4171, 48-32-4289, 48-32-4579, 48-32-4680, 48-32-4815, 48-36-1308, 48-37-5025R, 48-40-1026
48-44-0171, 48-53-4832, 48-53-4835, 48-55-1026, 48-62-4082, 48-73-1434, 48-73-1455, 48-73-5136, 48-73-7124E, 48-73-8435C
48-80-6401, 48-89-2326, 48-95-6070, 49-15-P750, 49-16-1609, 49-16-1663, 49-16-2634C, 49-16-2650, 49-16-2875, 49-16-5102
49-16-U01AC, 49-56-0024, 49-56-9825, 49-57-0626, 49-57-5371, 49-66-0502, 49-66-4516, 49-66-5144, 49-66-6404, 49-66-6734
49-90-1979, 51-57-8580, 51-57-8701, 51-57-8725, 52-76-2782, 52-76-4972, 58-08-2055, 58-08-5908, 58-10-0338, 58-42-9850
58-68-8112, 603GN-MD, STLHDL-S, TI14SC, 43-76-0900, 49-90-0910, 58-10-9170, 58-10-9171, 14-46-0709, 43-34-2735
```

---

## V8 · Forecast bias (governed)

- **Maps to:** Scenario 5 / DK-7 — requirements **D, R15, C.6**
- **Predicate / logic:** governed fact_forecast_accuracy Jan–Aug26
- **Primary source:** `fact_forecast_accuracy`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT selling_item_number FROM (SELECT selling_item_number,SUM(positive_error+negative_error) err,SUM(ABS(planner_bias)+ABS(system_bias)) bias FROM prod_operations.demand.fact_forecast_accuracy WHERE date_key BETWEEN 20260101 AND 20260831 AND selling_item_number IS NOT NULL GROUP BY selling_item_number) t WHERE bias>0 AND err>0 ORDER BY err DESC LIMIT 60
```

**IDs:**

```
48223100, 48228901W, 48228902W, 49940003, 48228903W, 48223104, 50021025, 48221505, 49940005, 48732010
48221725, 48111850, 48223170, 48112450, 48223180, 312867009, 48221503, 48017026, 48221825, LRHANDLE
49940103, 48223106, LRBDYSM, 48223105, 48017787, 48223209, 48111865, 48221950, 48228902, 48551034
312867024, 48221500, 48017788, 48111852, 48111881, 48112442, 48111862, 48223115, 369722, 49940503
48324023, 48228902E, 48111813, 48221706, 49940107, 48894670, 48221501, 48894631, 48221025M, 48324537
48228901, 48221905, 295320, MLSQ070, 49221110, 349722, 48732015, 301720, 48325031, 48228903
```

---

## V9 · Forward risk (coming-risk)

- **Maps to:** Gap 1 — requirements **G1, DK-9**
- **Predicate / logic:** healthy now, crosses SS later
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,MIN(CASE WHEN s.projected_available_balance<s.safety_stock THEN s.date_key END) fb FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND i.item IS NOT NULL GROUP BY i.item) t WHERE fb IS NOT NULL AND fb>20260908 LIMIT 60
```

**IDs:**

```
48-32-4171, 48-32-4579, 48-32-4815, 48-73-1410, 48-73-1501, 49-66-6624, 50-42-0120, 50-44-0260, 3401-20, 43-34-2735
M701B-21L, 49-66-6157T, 49-66-6204T, 49-66-6262T, 48-47-5711, CPPLH2001, CPPL2201, BLO1436, 2821-21J, 48-73-7920V
2123-21HDJ, 49-66-6654, 49-66-6672, 48-89-4870K, 48-22-3260X, 48-81-4780, 48-81-7760, 48-22-3079T, 43-40-8113, 14-73-0515
23-66-5027, 2533-21, 28-25-0010, 32-30-8001, 415G-S, 44-40-0035, 45-06-0020, 45-96-9315, 48-13-5540, 48-20-9046
48-89-2325CAN, 48-22-9508, 48-27-0007, 48-41-0720, 49-66-6538, 52-76-0093, 52-80-0606, 603BL-3X, 48-40-1048, 49-90-2023Y
PN0005818, 48-73-7153EM, 49-66-6511T, 48-73-7942V, 48-73-8912V, 49-56-9210T, 49-16-2820V, 49-66-6674, 351E-2X, 48-81-5080
```

---

## V10 · Chronic (repeat offender)

- **Maps to:** V10 / Gap 5 — requirements **G5, temporal_class**
- **Predicate / logic:** ≥6 forward weeks below SS
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,SUM(CASE WHEN s.projected_available_balance<s.safety_stock THEN 1 ELSE 0 END) bw FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND i.item IS NOT NULL GROUP BY i.item) t WHERE bw>=6 LIMIT 60
```

**IDs:**

```
48-27-0180, 48-32-4815, 48-40-0720, 48-73-1321, 48-73-1410, 49-16-W247, 49-57-5166, 49-66-6624, 49-90-1979, 604BL-XL
606B-XL, 77-0204, 3401-20, 31-44-0408, M701B-21L, 42-70-8100, CPPLH2001, F452G-XLD, 2772A-21J, 2161-21J
48-22-7718V, 45-34-1047T, 45-34-9086T, 2779-750CUZ, 45-34-2122T, 45-34-2124T, 45-34-4000T, 45-34-9052T, 45-34-9053T, 45-34-9101T
2941-21Z, 5268-21J, 2123-21HDJ, 49-66-6654, 2971-20M, 48-89-4870K, 28-28-1200, 48-22-3260X, 51-16-2651ZX, 48-81-4780
48-81-7760, 48-22-3079T, 43-40-8113, 0820-20, 0852-20, 0960-20, 14-20-9225, 14-32-0012, 14-46-0290, 14-73-0515
18-07-0176, 22-130, 22-68-0019, 23-66-5027, 2446-20, 2476-20, 2533-21, 28-20-0023, 28-28-1700, 28-35-0085
```

---

## V11 · Convergence (multi-cause)

- **Maps to:** DK-13 — requirements **DK-13 convergence**
- **Predicate / logic:** below SS ∩ PO slip
- **Primary source:** `20_supply_daily ∩ purchase_orders`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key JOIN prod_edw.fact.purchase_orders po ON po.item_bigint_key=i.item_bigint_key AND po.promised_delivery_date_key>po.original_promised_delivery_date_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND s.projected_available_balance<s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-22-9508, 48-22-9408, 48-22-9529, 48-22-9125, 48-22-8949B, 48-22-9038, 48-22-9314, 48-22-9504, 48-22-9429, 48-22-9004
48-22-9013, 48-22-9315, 48-22-8922, 48-22-9519, 48-22-9051, 48-22-9031, 48-22-9019, 48-22-8927, 48-22-9130, 48-22-9311
48-22-9012, 48-22-9020, 48-22-9032, 48-22-9016, 48-22-9044, 48-22-9481, 48-22-9150, 48-22-9214, 48-22-9482, 48-22-9030
48-22-9212, 48-22-9023, 48-22-9411, 48-22-9484, 48-22-9000, 48-22-9037, 48-22-9080, 48-22-8904, 48-22-9018, 48-22-9215
48-22-9513, 48-22-9029, 48-22-9320, 48-22-9036, 48-22-8928, 48-22-9485, 48-22-9511, 48-22-8902H, 48-22-9214T, 48-22-9407
48-22-9088, 48-22-8904X, 48-22-9151, 48-22-9034, 48-22-9486, 48-22-9215T, 48-22-8910, 48-22-8920, 48-22-9017, 48-22-9404
```

---

## V12 · Do-nothing / false-alarm

- **Maps to:** DK-14 — requirements **DK-14 action-verdict**
- **Predicate / logic:** below SS but min PAB>=0 (cushion dip)
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,SUM(CASE WHEN s.projected_available_balance<s.safety_stock THEN 1 ELSE 0 END) b,MIN(s.projected_available_balance) mp FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND i.item IS NOT NULL GROUP BY i.item) t WHERE b>=1 AND mp>=0 LIMIT 60
```

**IDs:**

```
48-25-1252, 48-27-0180, 48-32-4171, 48-32-4579, 48-32-4680, 48-32-4815, 48-40-0720, 48-73-1410, 48-89-2207, 49-16-W247
49-66-6122, 49-66-6624, 50-42-0120, 50-44-0260, 604BL-XL, 77-0204, 43-34-2735, M701B-21L, 49-66-6157T, 49-66-6204T
49-66-6262T, CPPLH2001, CPPL2201, 48-89-2217T, 2821-21J, PN0006103, PN0006130, PN0006141, 45-34-1047T, 45-34-9086T
49-94-0613, 2779-750CUZ, 45-34-2122T, 45-34-2124T, 45-34-4000T, 45-34-9052T, 45-34-9053T, 45-34-9101T, 48-73-7920V, 2123-21HDJ
49-66-6654, 49-66-6672, 48-89-4870K, 48-22-3260X, 48-22-3079T, 02-40-0518, 43-40-8113, 06-82-8995, 0852-20, 0960-20
14-02-0115, 14-02-0140, 14-46-0290, 14-46-6050, 14-73-0515, 18-07-0176, 22-130, 2476-20, 2533-21, 28-25-0010
```

---

## V13 · Recoverability (committed loss)

- **Maps to:** DK-15 — requirements **DK-15 recoverability**
- **Predicate / logic:** complete_lead_time>days-to-first-stockout
- **Primary source:** `20_supply_daily + dim_series_ext_vw`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,MAX(x.complete_lead_time) lt,DATEDIFF(to_date(CAST(MIN(CASE WHEN s.projected_available_balance<0 THEN s.date_key END) AS STRING),'yyyyMMdd'),to_date(CAST(L.pd AS STRING),'yyyyMMdd')) dc FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key JOIN prod_operations.edw_extension.dim_series_ext_vw x ON s.series_bigint_key=x.series_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND i.item IS NOT NULL GROUP BY i.item,L.pd) t WHERE dc IS NOT NULL AND lt IS NOT NULL AND lt>dc LIMIT 60
```

**IDs:**

```
48-22-8903P, 48-25-5120, 48-32-4196, 48-32-4396, 48-32-4408, 48-39-0506, 48-73-1107, 48-73-7151H, 48-89-2313, 49-12-U600C
49-16-2689, 49-16-2738, 49-36-2789, 49-59-2089, 49-59-4138, 49-66-6119, 50-39-1500, 52-80-0151, 52-80-2825B, 6370-21
70-01-1161, 3033-20, 48-73-8511, 312B-LY, 605B-MDY, M551R-XLD, 48-59-1881SC, 45-34-1123, 48-20-8899Y, M100R-3X-W
49-10-9001N, 48-90-6024T, 48-22-2464T, 48-11-2450C, 45-34-9083T, 14-20-0390, 14-46-0369, 48-73-2516, 48-73-5021BY, 14-46-3029
M100B-212X-J, 49-56-9607CA, 48-39-0511B, 48-39-0521BA, PN0016235, 14-46-2042, 14-46-0930, 48-81-6780, 48-81-7040, 06-82-7784
14-29-0135, 14-48-0085, 18-50-0120, 23-45-2674, 23-66-0011, 2520-ST, 2666-20, 2758-20, 28-50-0113, 2912-ST
```

---

## V15 · Lifecycle — transition / NPD

- **Maps to:** N1 / DK — requirements **N1, lifecycle_class**
- **Predicate / logic:** transition_sku_flag/is_npd_item boolean true + below SS
- **Primary source:** `items_scd1`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item
 FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd
 JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key
 WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130
   AND (i.transition_sku_flag=true OR i.is_npd_item=true)
   AND s.projected_available_balance < s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-25-1252, 48-32-4171, 48-32-4579, 48-32-4815, 48-40-0720, 48-73-1410, 49-66-6122, 49-66-6624, 49-90-1979, 606B-XL
77-0204, M650K-3632, 49-66-6157T, 49-66-6204T, 49-66-6262T, F452G-XLD, 48-89-2217T, 2772A-21J, 2821-21J, 2161-21J
48-22-7718V, 45-34-1047T, 45-34-9086T, 49-94-0613, 2779-750CUZ, 45-34-2122T, 45-34-2124T, 45-34-4000T, 45-34-9052T, 45-34-9053T
45-34-9101T, 48-73-7920V, 2941-21Z, 2123-21HDJ, 49-66-6654, 49-66-6672, 2971-20M, 48-89-4870K, 49-90-1976, 48-22-3260X
48-81-4780, 48-81-7760, 48-22-3079T, 48-00-5561, 48-20-8882, 48-32-4788, 48-32-5033, 48-73-5072, 48-89-2338, 49-16-KITC
49-16-U001C, 49-66-6376, 49-66-6538, 49-66-6642, 504B-LXL, 603B-S, MLBX24, 45-34-1077, 49-66-6212T, 48-20-9006Y
```

---

## V16 · Over-forecast → excess driver

- **Maps to:** N2 — requirements **N2**
- **Predicate / logic:** SUM fcst>1.5×SUM actual
- **Primary source:** `10_demand_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,SUM(d.final_demand_forecast) fc,SUM(d.shipments_history) act FROM prod_edw.fact.`10_demand_daily` d JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`) L ON d.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key=i.item_bigint_key WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan') AND d.date_key BETWEEN 20260101 AND 20260901 AND i.item IS NOT NULL GROUP BY i.item) t WHERE act>0 AND fc>1.5*act LIMIT 60
```

**IDs:**

```
603G-S, 606B-XL, M300N-21S, M701B-21L, F452G-XLD, M200N-203X, 3632-21PO, F550N-XL, 49-16-3055, M600B-21L
2118-20, 504B-LXL, 606BL-XLD, M102G-21XL, M300N-21XL, M850G-4032, M250B-M, M101C-3X-W, 2736-STR, 351E-2X
3450-STR, P326-2967, F102B-21XL, M102G-212X, M102G-213X, 3841-20, M100G-20M, M101C-M-W, M200G-212X, M200U-202X
49-90-2035Y, M552G-XL, 3060-STR, 49-90-1955, M300G-21S, M753BD, 2835-21HD, U2000RB-1, M200B-202X, 604E-3X
F102B-LREC, M754E-SM, 2940-STR, 2667-STR, F300B-20L, F300B-20XL, 2525-ST, M700B-21S, 3693-ST, M100G-S-W
M102G-L-W, F552G-XS, F251B-MD, 49-90-2929, 3044-20, 2865-STR, 49-90-1992, 49-90-2325, 3006-ST, M651B-3430
```

---

## V17 · Returns / warranty / reverse logistics

- **Maps to:** N3 — requirements **N3, DK reverse-logistics**
- **Predicate / logic:** warranty transactions since Jan 2026, item-keyed via conformed fact
- **Primary source:** `fact.warranty_transaction`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item
FROM prod_edw.fact.warranty_transaction w
JOIN prod_edw.dimension.items_scd1 i ON w.item_bigint_key=i.item_bigint_key
WHERE w.posting_date_key>=20260101 AND i.item IS NOT NULL
LIMIT 60
```

**IDs:**

```
2446-20, 0721-20, 6536-21, 2982-20, 2657-20, 2845-20, 2967-20, 2602-20, 2519-20, 2105
2787-20, 2127-20, 2780-20, 49-16-2721, 2954-20, 2559-20, 2828-20, 48-11-2131, 3974-20, 48-11-2460
5374-20, 3107-6, 2775B-211, 3674-20, 2505-20, MXF220-2HD, 2726-20, 2887-20, 2906-20, 6177-20
2114-21, 2820-20PS, 2560-20, 3601-20, 2762-20, 2563-20, 3020-20, 2115-21, 2764-20, MXF302-2HD
2881-20, 2011R, 6161-33, 48-11-2425, 2930-20, 49-24-2310, 6146-33, 2836-20, 6470-21, 2758-20
2113-21, 6143-31, 2903-20, 6086-30, 3049-20, 6124-31, 2488-20, 6161-31, 6141-59, 2974-20
```

---

## V18 · Found-inventory / phantom heal

- **Maps to:** N4 — requirements **N4, S10**
- **Predicate / logic:** positive adjustment txn since Jun26
- **Primary source:** `inventory_material_transaction`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.inventory_material_transaction t JOIN prod_edw.dimension.items_scd1 i ON t.item_bigint_key=i.item_bigint_key WHERE t.transaction_quantity>0 AND t.transaction_type_description IN ('Account Alias Receipt','Miscellaneous Receipt','Physical Inventory Adjustment','Cycle Count Adjustment') AND t.transaction_date_key>=20260601 AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-20-8036, 2865-20, 53-01-5293, 48-73-1079, 48-22-8436, 31-052, 14-34-0960, 48-22-4206, 14-30-3405, 48-89-2747
45-66-0018, 48-22-9340, 49-96-0600, 58-31-0628, 49-16-2669, PN0002695, 2267-20H, 22-16-0430, 10-05-6601, 48-32-4118
MR103749, 14-29-0023, 2205-20, 49-66-6272T, 34-40-1561, 48-73-2012V, 49-66-6348, 52-80-2829, 49-57-8643, 48-22-9504
48-22-1960, 48-32-5162CA, 06-82-0041, 45-88-7001, 58-09-4324, 48-22-9314, 48-73-2015V, 48-73-7151HM, MR104024, 58-68-1169
2657-99, 49-57-8323, 45-34-9063T, 49-66-6245T, 16-01-2503, 49-66-4703, 14-50-2430, 44-90-0108, 45-34-1062, 49-57-5141
48-89-2727T, 2354-STR, 2432-22YY, 53-01-6162, 48-32-4706, 49-57-5536, 2843-20, 49-66-6211, MR104546, 48-36-1109
```

---

## V19 · Non-standard demand channels

- **Maps to:** N5 — requirements **N5**
- **Predicate / logic:** shipments via non-standard mkedg5 channels
- **Primary source:** `10_demand_daily + dg5_customer_scd1`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`10_demand_daily` d JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`) L ON d.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key=i.item_bigint_key JOIN prod_edw.dimension.dg5_customer_scd1 g ON d.dg5_customer_bigint_key=g.dg5_customer_bigint_key WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan') AND g.mkedg5 IN ('SERVICE','NEFCO','ISN') AND d.shipments_history>0 AND d.date_key BETWEEN 20260101 AND 20260901 AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-25-1252, 48-27-0180, 48-27-1520, 48-32-4289, 48-32-4579, 48-32-4680, 48-32-4763, 48-32-4815, 48-36-1308, 48-39-0601
48-39-0616, 48-40-0720, 48-40-1026, 48-62-4082, 48-80-6401, 48-89-2207, 48-25-4125, 48-27-0007, 48-32-4191, 48-32-4715
48-32-4788, 48-32-4846, 48-32-4914, 48-32-5033, 48-36-1108, 48-41-0720, 48-52-1300, 48-62-4187, 48-20-9101, 48-20-9116
48-27-0190, 48-28-4006, 48-32-4020, 48-32-4090, 48-32-4142, 48-32-4485, 48-32-4502, 48-32-4682, 48-32-4760, 48-32-4810
48-32-5003, 48-32-9930, 48-40-0626, 48-80-5180, 48-89-2217, 48-20-9097, 48-25-4621, 48-25-5143, 48-25-5225, 48-27-0005
48-32-4515, 48-32-4571, 48-32-4573, 48-32-4578, 48-32-4660, 48-32-4678, 48-32-4771, 48-32-5700, 48-39-0561, 48-39-0635
```

---

## V20 · Component / multi-org items

- **Maps to:** N6 — requirements **N6**
- **Predicate / logic:** supply footprint on >=5 orgs
- **Primary source:** `20_supply_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,COUNT(DISTINCT s.inventory_organization_bigint_key) o FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND i.item IS NOT NULL GROUP BY i.item) t WHERE o>=5 LIMIT 60
```

**IDs:**

```
49-16-2650, 22-06-0605, 14-30-0161, 48-13-1503, 48-73-1321, 45-88-0128, 48-22-8428, 48-73-2052, 14-46-9960, 28-50-4139
06-82-8995, 2533-21, 2882-22, 32-30-8001, 42-42-0051, 44-90-0014, 45-76-0027, 48-00-5232, 48-22-8339, 48-32-4815
48-44-0171, 49-22-2731, 42-25-2595, 43-34-2735, 48-22-3079T, 06-82-0027, 14-48-0095, 22-32-0420, 48-20-5235, 48-73-1221
48-22-8393R, 48-32-4680, MT205, 3401-20, 2160-0, 0852-20, 22-130, 43-56-2550, 48-73-1410, 48-73-8435C
06-10-0025, 14-30-2008, 14-34-0034, 14-46-0259, 28-28-1700, 28-35-0127, 31-12-0098, 31-53-0011, 48-00-5561, 2579-20Y
06-65-0096, 23-66-2840, 2865-20, 42-25-0002, 44-40-0035, 44-76-0050, 48-20-9046, 48-13-5540, 48-32-4579, 507BL-SM
```

---

## V21 · Recovery velocity (slow release)

- **Maps to:** N7 — requirements **N7**
- **Predicate / logic:** hold_lag_hours>168h
- **Primary source:** `sales_fulfillment_hold_transactions`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.sales_fulfillment_hold_transactions h JOIN prod_edw.dimension.items_scd1 i ON h.item_bigint_key=i.item_bigint_key WHERE h.hold_lag_hours>168 AND h.hold_apply_date_key>=20260101 AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
49-90-2023Y, 48-22-5001E, 49-22-1110, 48-22-2923, 2791, 48-89-9244, 48-73-8523HX, 1140, 48-20-3916, 2909-20
650.24V, 48-22-5603, 500M.24, 48-08-1095, 48-73-8521HX, 44-10-5264, 2807-20J, 49-56-5140, 48-20-7311, 2788-22HDZ
31-44-2854, MT555X, 48-22-3510D, 48-32-4408, 650.72V, 49-90-2014J, 48-22-4540, 48-22-1525V, 296, 0880-20
105, 77-063T, 44-06-0201, MT216X, 27030, 48-73-8522HX, 50-02-1015, 14-20-6550, 18-07-5316, EM70.10
2828-21E, 48-22-2917, 4274-21Z, 14-29-0115, 48-22-1502, 48-22-3910, 48-22-1521V, 48-22-3209, MLIBM48, 352R-S
FG58-28-3237, 49-90-1900, 48-22-6100V, 48-22-1500, 100, 48-22-6240, FG58-28-2923, 49-90-2026, 48-22-1905, 48-22-6910
```

---

## V22 · Criticality — A-class ABC

- **Maps to:** DK-16 — requirements **DK-16 criticality_class**
- **Predicate / logic:** inventory_abc_class=A + below SS
- **Primary source:** `dim_series_ext_vw`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key JOIN prod_operations.edw_extension.dim_series_ext_vw x ON s.series_bigint_key=x.series_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND upper(x.inventory_abc_class)='A' AND s.projected_available_balance<s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
50-44-0260, BLO1436, 51-16-2651ZX, PN0005818, 51-11-1822, 6PCTSPH120B, 14-46-0533T, BCO2238, BCO2223, 3974WM
51-16-2659X5, 58-33-1000, 14-46-0531T, PN0005654, BCO2296, 8PCTSPH, 3973WM, 58-15-0542, 58-33-0987, PN0005819
3975WM, 2580WM, BCO2351, 51-16-2455C, 58-09-1057, 45-52-1091C, 52-76-2446, 51-16-2456M, 58-10-2003, 50-56-9103
PN0005661, BCO2222, 51-16-2455M, 51-16-2652ZX, 58-33-0480, 58-68-1767, 51-16-2659X4, BLO2019, DIVIDER12, PN0005830
9PCTSPH, 58-39-2900, 51-16-2658R, 51-16-2670, 51-16-2452M, 51-16-2655BX, 51-16-2659X6, PN0014724, 50-32-5156CA, 58-22-2462
51-16-2656X, 51-16-2657X, 51-16-2654, 6PCTSPH60B, 58-10-0263, 58-10-1014, 51-16-2656RX, 51-16-2650X, 51162651RX, 51-16-2456Z
```

---

## V23 · Dormant / obsolescence (E&O)

- **Maps to:** DK-17 — requirements **DK-17 dormant_flag**
- **Predicate / logic:** 0 ship Mar–Sep26, >0 before
- **Primary source:** `10_demand_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,SUM(CASE WHEN d.date_key BETWEEN 20260301 AND 20260901 THEN d.shipments_history ELSE 0 END) r,SUM(CASE WHEN d.date_key BETWEEN 20250101 AND 20260228 THEN d.shipments_history ELSE 0 END) p FROM prod_edw.fact.`10_demand_daily` d JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`) L ON d.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key=i.item_bigint_key WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan') AND i.item IS NOT NULL GROUP BY i.item) t WHERE r=0 AND p>0 LIMIT 60
```

**IDs:**

```
48-32-4020, 48-32-4029, 48-32-4073, 48-62-1915, 48-40-4168, 48-52-1600, 48-32-4280, 48-62-3025, 48-32-4019, 48-40-4116
48-62-3020, 48-42-5220, 48-42-5421, 48-32-4282, 48-32-5721, 48-89-1561, 48-32-3065, 48-32-5158, 48-62-3090, 48-36-1061
48-32-5722, 48-62-2065, 48-32-5022, 48-32-4204, 48-32-4196, 48-32-4490, 48-32-4222, 48-32-5720, 48-42-0200, 48-62-6024
48-32-5023, 48-40-4108, 48-32-4489, 48-42-5101, 48-42-5200, 48-40-4150, 48-32-4028, 48-30-1520, 48-32-5032, 48-42-5640
48-32-5021, 48-52-1700, 48-32-4281, 48-32-4203, 48-52-1400, 48-32-4026, 48-32-4731, 48-52-1650, 48-40-4015, 48-32-4005
48-32-4263, 48-41-0713, 48-89-0026, 48-40-4105, 48-62-3065, 48-40-4140, 48-62-6048, 48-25-1371, 48-89-2521, 49-10-9122
```

---

## V24 · Intermittent demand

- **Maps to:** DK-18 — requirements **DK-18 demand_class**
- **Predicate / logic:** active<30% of >=12 months
- **Primary source:** `10_demand_daily`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT item FROM (SELECT i.item,COUNT(DISTINCT CASE WHEN d.shipments_history>0 THEN d.date_key END) a,COUNT(DISTINCT d.date_key) tt FROM prod_edw.fact.`10_demand_daily` d JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`10_demand_daily`) L ON d.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON d.product_bigint_key=i.item_bigint_key WHERE d.plan_name IN ('10 TOL Demand Plan','10 PRT Demand Plan','10 ACC Demand Plan','10 HND Demand Plan','10 QP Demand Plan') AND d.date_key BETWEEN 20240101 AND 20260901 AND i.item IS NOT NULL GROUP BY i.item) t WHERE tt>=12 AND a>0 AND a<0.3*tt LIMIT 60
```

**IDs:**

```
48-62-2057, 48-32-4490C, 48-62-4074, 49-22-1110V, 48-20-4075, 49-10-9208Q, 48-22-2434, 48-73-5332C, 58-28-7098, MLIB48
FG58-28-3187, FG58-28-7776, FG58-28-1428, 48-73-1501, MLBX78, FG58-28-7812, FG58-28-2897, FG58-28-0664, 48-73-7124E, FG58-28-3291
48-20-8823, 05-55-3120, 05-81-0076, 05-86-0016, 06-54-0120, 06-65-0096, 06-65-1280, 06-75-5825, 06-82-0091, 06-82-1085
06-97-0455, 12-20-2447, 12-20-5379, 14-04-0005, 14-09-0100, 14-12-0115, 14-29-0101, 14-30-2409, 14-34-6255, 14-38-0061
14-46-1017, 14-46-8605, 44-04-2120, 44-60-0041, 44-60-5379, 44-60-5420, 44-66-0141, 44-68-0015, 45-08-0013, 05-74-0625
05-81-0530, 06-65-0006, 06-75-0006, 06-81-0028, 12-99-1300, 14-34-0270, 14-46-0401, 44-20-0026, 44-60-0142, 14-02-0115
```

---

## V25 · Parameter / SS review candidate

- **Maps to:** DK-19 — requirements **DK-19 proposal-queue**
- **Predicate / logic:** safety_stock_managed_flag=Yes + below SS
- **Primary source:** `dim_series_ext_vw`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key JOIN prod_operations.edw_extension.dim_series_ext_vw x ON s.series_bigint_key=x.series_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND x.safety_stock_managed_flag='Yes' AND s.projected_available_balance<s.safety_stock AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
49-66-6262T, 48-32-4680, 48-27-0180, 50-44-0260, 48-32-4579, 48-25-1252, 48-32-4171, M650K-3632, 49-94-0613, 3401-20
48-32-4815, 603B-S, 49-66-6212T, 58-22-6108, 52-76-0093, 49-66-4703FL, 507B-LXLQ, 2438-22XYY, 48-81-5080, 48-73-5072
48-11-2450C, 603BL-3X, 48-22-8901F, 48-32-4832ZZ, 48-32-5033, 49-94-0107, 48-32-4788, 48-73-2014TW, 45-88-0015, 52-80-0606
48-81-7060, 51-11-1822, 48-73-2101, 48-20-9057Y, 48-22-9008, 45-96-0024, 48-73-2502, 48-73-1108, 48-32-5003, 48-22-8371R
3494-22, 48-32-4810, 49-66-6370T, 415R-LP, 48-73-5165, 48-32-4502, 48-73-5161, 605G-MDQ, M650G-3230D, 48-27-0190
14-46-0533T, 49-66-6607T, 48-73-5123, 49-16-1212, 48-22-0160, 49-66-4502, 603E-2X, 51-36-7100, 58-08-3120, 48-81-7740
```

---

## V26 · Intentional-hold (managed SS)

- **Maps to:** DK-20 — requirements **DK-20 intentional_hold**
- **Predicate / logic:** safety_stock_managed_flag=Yes
- **Primary source:** `dim_series_ext_vw`
- **IDs returned:** 60 (distinct, live)

**Successful query (READ-ONLY):**

```sql
SELECT DISTINCT i.item FROM prod_edw.fact.`20_supply_daily` s JOIN (SELECT MAX(process_date) pd FROM prod_edw.fact.`20_supply_daily`) L ON s.process_date=L.pd JOIN prod_edw.dimension.items_scd1 i ON s.product_bigint_key=i.item_bigint_key JOIN prod_operations.edw_extension.dim_series_ext_vw x ON s.series_bigint_key=x.series_bigint_key WHERE s.plan_name='20 Global Supply Plan' AND s.date_key BETWEEN L.pd AND 20261130 AND x.safety_stock_managed_flag='Yes' AND i.item IS NOT NULL LIMIT 60
```

**IDs:**

```
48-22-8929, 48-25-1252, 48-27-0180, 48-27-1520, 48-32-4171, 48-32-4289, 48-32-4437J, 48-32-4579, 48-32-4680, 48-32-4763
48-32-4815, 48-36-1308, 48-39-0601, 48-39-0616, 48-40-0720, 48-44-0171, 48-55-1026, 48-55-1212, 48-62-4082, 48-25-4125
48-32-4191, 48-32-4413J, 48-32-4461J, 48-32-4788, 48-32-4846, 48-32-4914, 48-32-5033, 48-41-0720, 48-44-0151, 48-55-0123
48-62-4187, 48-66-1270, 48-66-3160, 48-73-1097, 48-22-9008, 48-22-9408, 48-27-0190, 48-28-4006, 48-32-4020, 48-32-4090
48-32-4485, 48-32-4502, 48-32-4682, 48-32-4685J, 48-32-4760, 48-32-4810, 48-32-5003, 48-40-0620P, 48-40-0626, 48-53-2410
48-53-2833, 48-55-2730, 48-55-2765, 48-55-3566, 48-59-0090, 48-73-1108, 48-73-1131, 48-22-9225, 48-25-4621, 48-32-4073
```

---
