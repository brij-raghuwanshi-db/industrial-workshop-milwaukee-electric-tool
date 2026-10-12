# Newly-explored: physical-flow / network tables (hops, routes, transfer $, sourcing, freight)

**Date:** 2026-08-31 · **READ-ONLY** metadata + probe queries on `prod_operations` / `prod_edw`.
Triggered by the user's push: *"maybe there are hops or routes... maybe they're spending double... find
through the data and metadata, maybe there are tables we have not explored."* There were. This note records
what exists, what's verified populated for our two orgs, and the corrected 2120 sourcing story.

## Corrected finding first (important)
My earlier claim "**2120 is a net-receiving node fed by transfer from 2012**" is **WRONG** — refuted here:
- `manufacturing_sc.fact_transfer_order_receipt`: **2120 = 0 lines** as source AND dest (790,382 scanned).
- `features.safety_stock_network_sourcing_rules`: 2120's sourcing types are **Buy from (85,544 rules /
  21,386 items) + Make at (964)** — **no "Transfer from" at all**.
- **2012** is the transfer hub: **Transfer from = 395,940 rules across 19 source orgs** (2013, 2093, 1080,
  1019, 2014, 9042/9043, 3060…); actual transfer receipts in the billions (2012←2013 ≈ **$1.4B**, last 12mo).
So: **2012 = network hub (transfer-fed, multi-org); 2120 = directly-sourced/self-made leaf.** The
ship/receive symptom (0.094) is real; the cause is purchasing + local manufacturing, not transfer.

## Tables discovered (were NOT in our prior table map) — all READ-ONLY sources
| Table | Grain / key cols | What story it unlocks |
|---|---|---|
| `prod_operations.manufacturing_sc.fact_transfer_order_shipment` | item × source→dest (via HR-location keys) × TO; **carrier, mode_of_transport, ship_method, total_shipped_cost, weight/volume, date_requested/scheduled/actual_ship** | **Actual org-to-org movement + freight + the physical hop** (source→dest, carrier, mode). Ship→receive dates = transit lead time. |
| `prod_operations.manufacturing_sc.fact_transfer_order_receipt` | item × source_org→dest_org keys × TO; **shipped/expected/receive/accept/deliver dates, qty_shipped/received/accepted/rejected, total_*_cost, status** | **Stage of a transfer** (shipped → received → accepted/rejected) + landed cost + on-time (expected vs actual receive). This is the closest thing to "where is it now" that exists. |
| `prod_operations.features.inventory_rebalance_current_transfers` | item × src→dst org × date; order_qty, firm_status, **transfer_direction** | Current firm/planned rebalancing moves between orgs. |
| `prod_operations.features.inventory_rebalance_optimal_transfers` | item × src→dst org × week; qty, **solution_status, mip_gap** | **Optimizer's ideal** transfer plan → *current vs optimal* = the "you could rebalance / stop double-handling" story. 2012↔2013 dominant; 2120 not present. |
| `prod_operations.features.safety_stock_network_sourcing_rules` | item × org; **source_type (Buy/Make/Transfer), supplier_org_code, complete_lead_time, days_of_cover, planner_name, net_org_planner_name** | **The "route": where each org sources each item + lead time + who plans it.** Basis for the org_role tag. |
| `prod_operations.manufacturing.dim_global_sourcing_rule` | item × org; vendor, allocation %, vendor site | Supplier-level sourcing + split allocations. |
| `prod_operations.transportation.fact_transportation_paid` / `manufacturing.fact_cass_outbound_freight` | shipment/lane; freight paid | **Freight $ ("spending double") at lane level.** Not yet org-joined — needs a probe. |
| `prod_edw.dimension.planner_scd1`, `prod_operations.demand.dim_demand_planner`, `procurement.dim_purchase_order_planner_pbi_vw` | planner | Planner identity/contact for the "do the planners meet?" story. |

## The coordination story (verified, answerable now from gold)
Of **5,644** shared SKUs planned by named humans in BOTH orgs, **5,638 (99.9%) are planned by DIFFERENT
people**; only **6** share a planner. → Nearly every dual-org item has two independent owners = a concrete
**planner-coordination / consolidation** surface. (Add `net_org_planner_name` from sourcing rules to see the
network-level planner too.)

## Directly answering the user's two dashboard questions
1. **"Can we show hops / the stage the item/shipment is currently in?"**
   - **Partially, and only for 2012's transfer network** — `fact_transfer_order_receipt/shipment` carry the
     source→dest hop, carrier/mode, and the status ladder (shipped→received→accepted) with dates, so a
     "transfer in flight / received / accepted" stage view is buildable **for transfer orders**.
   - **NOT a full multi-hop track-and-trace.** These are single-leg (source org → dest org) transfer
     records, not a stitched supplier→plant→DC→customer chain, and there is **no live "current location"**
     feed here — "stage" = latest status + date, not GPS. A true multi-hop lineage would need the records
     chained (TO→PO→sales order) which we have not built or verified.
   - **For 2120 it does not apply** — 2120 has no transfer orders (Buy/Make only). Its "stage" story is a
     PO-receipt story (`purchase_receipt_line`, already in our map), not a transfer story.
2. **"Spending double / routes":** freight $ exists (`fact_transportation_paid`, `fact_cass_outbound_freight`)
   and transfer landed cost exists (`total_shipped_cost`/`total_received_cost`) — enough to quantify
   cost-to-move, but the lane↔org join needs one more verification probe before any claim.

## Honest status / scope guard
- All of the above is **discovery + populated-check**, not built. It is **out of P1's plan-vs-actual scope**
  (P1 = plan vs actual at item×org×week). It most naturally belongs to a **P2/P3 network/flow** thread.
- **Do not overengineer:** the *cheap, high-value, in-scope* wins available right now are (a) the
  planner-coordination tile (gold only) and (b) an `org_role` tag (`transfer_hub` vs `direct_source`) derived
  from `safety_stock_network_sourcing_rules` — both small. A full hop/track-and-trace page is a **separate,
  larger initiative** and should be a deliberate decision, not a reflex add.
- Every query here was READ-ONLY SELECT on prod; nothing written outside `sandbox_operations.po_management`.
