# Demand Events — Live Source Data Profile

**Profiled:** this session, live at source. **Profile:** `mke-rsc` · **Warehouse:** `7bd33a82f4e92206`.
**Scope:** every source table named in `customer_requirements/01_Requirements.md`. All **READ-ONLY** (`prod_edw`).
**Evidence:** [V] = directly queried this session.

## Sources covered (all 6 from the requirements doc)

| # | Table (requirements doc) | Role | Status |
|---|---|---|---|
| 1 | `prod_edw.staging_flat_files.expansion_dims` | Event header source + schema ref | ✅ profiled |
| 2 | `prod_edw.staging_flat_files.expansion_loads` | Event value grid source + seed | ✅ profiled |
| 3 | `prod_edw.dimension.dg5_customer_scd1` | Customer 6-level hierarchy | ✅ profiled |
| 4 | `prod_edw.dimension.items_scd1` | Item validation | ✅ profiled |
| 5 | `prod_edw.fact.10_demand_daily` | Disaggregation base measures | ✅ profiled |
| 6 | `prod_edw.dimension.inventory_organization_scd1` (org 2012/2120) | Org auto-populate | ✅ profiled |

---

## 1–2. expansion_dims / expansion_loads (the existing events)

**Schemas** match the requirements doc exactly (dims: 10 cols; loads: 11 cols incl. `expansion_name, item_number, customer, variable, load_value`). [V]

**Volumes (expansion_loads):** 8,088,876 rows · **1,462 distinct events** (`file_name`) · 15,170 items · **53 customers**. [V]

**load_value distribution:** [V]
- positive: 627,139 · **negative: 6,883 (min −8,640)** · zero: 7,108,197 (**~88%**) · blank: 346,611 (~4%).
- max: 19,060,445.
- → **Negatives are real** (reduce-the-forecast events, e.g. Oracle-cutover push-pull). **The grid is very sparse** — store only non-zero cells.

**Every large event is single-customer** (top 8 events all `customers = 1`, all `EXP008xx Oracle_…`). [V]
→ Confirms the business's #1 pain: "one customer per file." Multi-customer per event is the core enhancement.

**`variable` (month bucket) has MIXED formats:** [V]
- 8,080,739 rows ISO timestamp (`2027-02-01 00:00:00`) — good.
- **8,137 rows are Excel serial integers** (`45748`, `45809`) leaking from source files.
- → **Data-quality rule required on read**: detect 5-digit serials, convert `1899-12-30 + n days`, normalize all to first-of-month.

**Identity columns:** `file_name` = `"EXP001442 TOL THD Stor…"` (EXP ID + human name). `expansion_name` = clean name. `run_id`, `record_source` (`0expansion_loads.parquet`), `load_date` are ingestion audit. [V]

---

## Traced ONE event end-to-end: `EXP001442` (TOL THD 2026 HDC, Home Depot) [V]

**Header (expansion_dims):** multiple rows, one per store-tranche via `file_index`:

| file_index | number_of_expansion_stores | ship_month | set_month |
|---|---|---|---|
| 0 | 22 | June 2026 | July 2026 |
| 1 | 42 | July 2026 | August 2026 |
| 2 | 9 | August 2026 | September 2026 |
| 3 | 28 | September 2026 | October 2026 |

**Values (expansion_loads):** item 2438-20 / HOME DEPOT / 2026-05-01 appears **multiple times at 75** each — the grid is **NOT pre-aggregated**; it's one row per store-tranche.
→ **Modeling decision:** an "event" = a set of sub-loads (tranches); the app must aggregate tranches to the mkedg5 × item × month output grain, and decide whether to preserve tranches or collapse on import.

---

## 4. items_scd1 — item validation ⚠️ MAJOR FINDING

**Cardinality:** 300,013 rows / 300,007 distinct `item_id` → **status is item-level, not org-level.** [V]

**item_status distribution (top):** Obsolete 69,273 · Reserved 64,518 · OB 53,473 · ShipSO 50,346 · EnterInv 37,084 · DiscExtrnl 11,358 · **PurchPlan 8,727** · … [V]

**⚠️ The requirements' primary validation rule fails against a real, valid event:**
For `EXP001442` (24 items): dash-normalized join (`REPLACE(item_number,'-','')`) matched **24/24 (100%)** — the join works. But the item statuses are: **ShipSO = 22, DiscExtrnl = 2, PurchPlan = 0.** [V]

→ **`item_status='PurchPlan'` would flag 100% of a legitimate Home Depot expansion.** This directly resolves **open-item #1** with evidence: the doc's "Status 20 = PurchPlan" rule is wrong (or incomplete) for events. Events carry **sellable/shippable** SKUs (`ShipSO`), not purchase-planning SKUs. **Validation must be a non-blocking warning anyway** (per requirements §4.2), which is fortunate — but the *criterion itself must be reconfirmed with analytics engineering* before we hardcode it. Likely correct set is broader (e.g. ShipSO + others), or the rule differs for events vs the P1/P4 supply context where PurchPlan applied.

---

## 3. dg5_customer_scd1 — customer hierarchy [V]

Full 6-level hierarchy real and populated. Examples:
- `3RD PARTY → DOM → THD → THD → THD → HOME DEPOT`
- `3RD PARTY → DOM → OTD → HDW → FARM → RURAL_KING`
- `3RD PARTY → DOM → OTD → HDW → HDW → ACE`
- `3RD PARTY → LAG → LAG → THD MEX → THD MEX → THD MEX` (Mexico/THD MEX → org 2120)

Columns: `mkedg0…mkedg5` + `customer`, `dg_code`, `dg5_customer_bigint_key`. Output grain = **mkedg5**.
→ Note `mkedg0` has case variants (`3RD PARTY` vs `3rd Party`) — normalize case when grouping for disaggregation.

---

## 5. 10_demand_daily — disaggregation base measures [V]

Confirmed measure columns exist (all DOUBLE):
- **`planner_baseline`** ✅ (the doc's `planner_baseline_forecast` name is wrong) + `planner_baseline_amount`, `planner_baseline_adj`, `planner_baseline_ovrd`, `live_planner_baseline_forecast`.
- **`working_final_forecast`** ✅ + `_amount`.
- Event columns already in the fact: **`expansions_loadin`, `expansions_runrate`, `non_repeating_events`** + `_by_org`, `_override` variants, and **`frozen_*`** equivalents.
- Many candidate disaggregation bases (open-item #3): `final_demand_forecast`, `total_statistical_forecast`, `customer_forecast`, `baseline_statistical_forecast`, etc.
- `_amount` suffix = the **dollar** counterpart → supports the **$-input path** ($ disaggregated then converted to units).

→ Disaggregation default = `planner_baseline`; the app already has its own event columns in the fact, so published events round-trip back into the demand fact via the existing integration.

---

## 6. inventory_organization_scd1 — orgs [V]

- `2012` = **2012 Olive Branch** (US default).
- `2120` = **2120 Mexico** (Mexico/THD MEX override).
- Column is **`organization_code`** (not `org_code`); also has `organization_name`, `designated_org_code`, `forecasted_organization`, `ship_from_org`.

---

## Net implications for the build

1. **Validation rule is the top open risk** — `PurchPlan` flags valid events. Reconfirm the real criterion (§16.3) before hardcoding; keep it non-blocking regardless.
2. **`variable` needs a normalize-on-read DQ step** (Excel serials + ISO → first-of-month).
3. **Store sparse** (non-zero cells only); support **negatives**.
4. **Event = multi-tranche** (`file_index`); decide preserve vs collapse on import.
5. **Multi-customer per event** is the core enhancement — today's events are single-customer.
6. **Dash-normalize** item join (100% match on the traced event) + **case-normalize** hierarchy.
7. All facts confirm: **read `prod_edw`, write only `sandbox_operations.po_management` + Lakebase.**
