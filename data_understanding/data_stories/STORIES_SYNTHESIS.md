# Data Stories — Synthesis (journeys walked, both polarities, hidden patterns)

**As-of:** 2026-08-30 · READ-ONLY · workspace `mke-rsc`. Every claim below is backed by a live query in
the linked S/G/P file. Hero anchor for P1/P2: **item_bigint_key 3879620845706693458 = item_id 48111850,
"M18 XC5.0 BATTERY"** (chosen on cross-table richness — see `S0_hero_item_discovery.md`).

## The single most consequential finding
`prod_edw.fact.purchase_receipt_line` (clean EDW keys, item_bigint_key + PO number/line +
received/accepted qty + receipt dates; 2.72M rows, 3 yrs) is a **far better P1 receipt source** than the
doc-named raw-Oracle `receiving_receipt_transactions` (which has no item column). **The crosswalk "blocker"
dissolves.** Details: `KEY_FINDING_receipt_source.md`.

## Scenarios walked (each printed real rows + narrated + tagged ✅/⚠️ end-user lens)

| # | Scenario | Priority | Anchor (discovered) | Verdict |
|---|---|---|---|---|
| S1 | Receipt attainment | P1 | M18 battery + PO 480002236 | receipt bridge WORKS via purchase_receipt_line; small POs on-time/in-full, 2,176 order in-flight |
| S2 | Ending on-hand & why it moved | P1 | M18 battery @ Olive Branch | demand spike −32K on 8/27, transfer +87K arrived 8/28 (1 day late); 5 variance categories populated |
| S3 | Shipment attainment | P1 | M18 battery | ~27K units/wk steady; 87%-null shipped_quantity gotcha proven (14.8% non-null at item grain) |
| S5 | Stockout / SS breach priority | P2 | carbide cylinder 88930100 @ Grenada | ranking works, BUT raw unit-miss over-ranks a $0.0134 part → ~$235K not "$3.5B"; needs $×ABC weighting |
| S6 | DC imbalance / rebalance | P2 | glove 48228902WM | 869K @ Olive vs 393K @ Byhalia; 129 transfers/mo prove rebalance is real; Byhalia has no SS threshold |
| S7 | Demand event journey | P3 | event "Oracle_Phase 2_THD" | round-trip WORKS into 10_demand_daily; item match is a DASH-normalization (98.7% vs 4.8%), customer 1:1 |
| S9 | Forecast drift | P4 | M12 battery 2PK @ Home Depot | +184K (+23,016%) demand-driven baseline revision; frozen_* cols NULL → use process_date deltas |

## Positive vs negative polarity — every signal cuts both ways
> The user asked for good-for-business AND red-flag scenarios. Most S-stories above are red flags; the
> green counterparts are in `G_positive_scenarios.md`. The core principle: **the same column is the signal
> for both poles** — health is the middle band, and BOTH tails are exceptions.

| Signal (table.column) | 🟢 Green / good | 🔴 Red / bad |
|---|---|---|
| `20_supply_daily.projected_available_balance` vs `safety_stock` | PAB comfortably 1.1–2× SS (healthy buffer) — G2 | PAB < SS = stockout risk (S5); **PAB ≫ 3× SS = excess / tied-up working capital** (both tails bad) |
| `purchase_receipt_line.received_quantity` vs PO `ordered_quantity` + `expected_receipt_date` | received == ordered, on/before promised (G1) | short/late/over receipt (S1 in-flight risk); PO past-due (0 received past promised) |
| `sales_order_line_transactions.shipped_quantity` vs `order_quantity` | shipped==ordered, Invoiced/Closed (G4) | short-ship, backorder, or forecast with zero actual (dead SKU) |
| `10_demand_daily.working_final_forecast` vs prior snapshot | flat = stable, trustworthy plan (G3) | large drift = volatility/nervousness (S9); persistent one-sided drift = bias |
| `inventory_days_on_hand.on_hand_qty` across orgs | balanced to demand share | one DC long + one short = imbalance (S6) |

## Hidden / non-obvious patterns (usually missed by standard reporting)
> Discovered by query in `P_hidden_patterns.md` — patterns invisible on a single-snapshot dashboard.
> (Filled in when P agent completes.)

## What this buys us for the build
- **P1**: use `purchase_receipt_line` for receipts; plan-vs-actual on the hero item is fully traceable; the
  on-hand↔movement tie-out needs inter-org netting (S2 gotcha).
- **P2**: prioritization must be unit-miss **× applied_standard_cost, stratified by ABC and org-role** (S5);
  rebalance-vs-order is a real, evidenced decision (S6).
- **P3**: item validation = dash-normalized join to items_scd1; customer maps 1:1; event round-trips into
  the demand fact (S7).
- **P4**: drift is detectable via process_date deltas today (frozen_* not yet populated); the "why" belongs
  in Lakebase audit, not the warehouse (S9).

## Additional scenario dimensions traced (all landed, query-backed)
- **Received/not-received matrix** (R): 1.23M PO lines fully received (🟢) vs **356K past-due-not-received** (🔴);
  over-received +23M units. #18 plan-vs-actual receipt variance lives here.
- **Extreme variance** (V): biggest plan-vs-actual on-hand gaps + **forecast≫actual** (Inkzall marker forecast
  269K, shipped 4K) — weight by cost×ABC×org-role.
- **Status transitions / workflow** (T): "on-track last week, now not" — Oct-5 week PAB **151,929 → −3,464**
  across snapshots; trigger→decision→Lakebase state; on-time/delayed/past-due (227-day overdue example).
- **Recoverable counterfactuals** (C): ~37% clearly recoverable; the ROI case for the queue (some anchors illustrative).
- **Rolling windows Mon–Sun** (RW): rolling-4wk smoothing, WoW ±138%, **weeks-of-cover flip 1.07→0.32→1.07**.
- **Logistics delays** (LG): items **99.99% dependent on in-transit stock** (75K transit / 6 on-hand); 41-day-late receipts.
- **Emergent** (EM): demand **+705,033%** (NPD launch), past-due cluster **46.5K lines (90% TTI)** forming this month.
- **Multi-org + weekly** (N): non-2012 orgs material (1019 Grenada 199M units); non-2012 breach (3PL, 6,681 miss);
  **clean weekly Mondays 6/6**; branches 3020–3025 = order-only (exclude from P1 weekly variance).
- **Location-role & persona** (O): plants hold 79.5% of units (components) vs DCs 75% of $ (finished goods);
  **same signal, different meaning + owner**; 69% of item×orgs have no named planner → route by role-team.
- **Hidden (P), anti-patterns (AP), blind-spot sweep (X), lineage (L)** — see INDEX.

## Priority tagging & the "Beyond P1–P4" bucket
- `PRIORITY_MAP.md` tags **every scenario to P1/P2/P3/P4** (● primary / ○ also) with a per-priority rollup.
- `BEYOND_P1P4_scenarios.md` groups signals that belong to **NO** priority into **P5/Beyond**, by owner:
  B1 sourcing/supply-risk · B2 ordering (excluded scope) · B3 inventory finance/working-capital ·
  B4 data governance (prerequisites, not scope) · B5 supplier quality/SRM · B6 forecasting-method/NPD.

## Traceability & temporal-state (the "where / what stage / how many at each stage" layer)
- **HOP product journey** (HOP): physical hop-chain supplier→plant→transit→DC→customer; node-to-node
  QUANTITY flows, outbound leg fully tracked (carrier/BOL); from→to works within an org not across; no serial/lot.
- **Point-in-time state** (STATE): where the product is + what stage as-of a date (169.5K on-hand / 721 in
  transit / 2,297 scheduled); replayable as a time-lapse — the temporal half of lineage.
- **Quantity-status breakdown** (QTY): ordered→received→open per PO line + split-delivery schedules +
  MULTI-SUPPLIER per item (item 49960060 = 6 suppliers; allocation_percent). "50 reached / 600 in progress /
  350 being made" as quantities, not units.
- **Geography** (GEO): region/state/country + country-of-origin present; NO lat/long (mapping needs geocode).

## Question-driven syntheses (asked during review)
- **CAUSES**: most common operational (supply-timing/logistics, demand≠forecast, wrong-place/excess) +
  analytical (grain/semi-additivity, raw-magnitude ranking, single-snapshot) root causes.
- **IMPACT**: if the agentic app is built — prod EDW unwritable (safe), new sandbox/Lakebase records (good),
  adverse surface = external writeback + P3 daily publish + data-trap recommendations; rails to make it safe.

## Files
INDEX (start) · PRIORITY_MAP · BEYOND_P1P4 · STORIES_CATALOG · KEY_FINDING receipt source ·
S0 discovery · S1 receipt · S2 on-hand · S3 shipment · S5 stockout · S6 imbalance · S7 event · S9 drift ·
G positive · R received/not-received · V extreme-variance · T transitions · C recoverable · RW rolling ·
LG logistics · EM emergent · N multi-org/weekly · O location/persona · P hidden · AP anti-patterns ·
X uncovered · L lineage · HOP journey · STATE point-in-time · QTY status breakdown · GEO geography ·
CAUSES root-causes · IMPACT agentic-app · FIN finance-data · LOSS supply-chain-losses ·
THE_SEARCH_PAIN_JOURNEY (the pain narrative).
