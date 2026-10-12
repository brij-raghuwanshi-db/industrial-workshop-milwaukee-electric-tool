---
name: mke-project-scope-sources
description: MKE authoritative scope lives in customer_requirements/ (3 docs) — they outrank any distilled summary; validate scope live before building
metadata: 
  node_type: memory
  type: project
  originSessionId: ed081939-8656-4083-b3da-17ba19979798
---

The authoritative scope for the Milwaukee supply-chain project is the three requirement docs in
`customer_requirements/` (not the `development_pattern/` operating-pattern discussions, which are
about *how* to work):

- `Actuals_Supply_Plan_Requirements.md` → **P1** (confirmed sources incl.
  `prod_edw.fact.20_supply_daily`, `receiving_receipt_transactions`, `sales_order_line_transactions`,
  `inventory_days_on_hand`; decisions D1–D6; thresholds; 180-day backfill).
- `Red_Keychain_Supply_Planning_Requirements.md` → **P2** (supply exceptions) + **P4** (demand
  exceptions); 18-type taxonomy across 5 categories; broader ordering program is context, not scope.
- `01_Requirements.md` → **P3** Demand Events App (lifecycle, locking, mkedg5 disaggregation,
  Forecast Builder, output contract).

Priority order P1→P2→P3→P4; **PO Exceptions OUT of scope** (verify — it flipped once historically).

**Why:** these docs are the customer source of record and are more concrete/current than the
skill's distilled summary; treating a paraphrase as authoritative caused prior rework.

**How to apply:** the skill's `references/project-scope-and-delivery.md` is a **validate-first
snapshot** (as-of date, [req-confirmed] vs [synthesized] tags) — re-read the real docs and verify
table names/grains/thresholds against live Unity Catalog before building; a newer requirement
always wins over the summary. Two open boundaries to confirm with the owner: the P2 supply-vs-PO
exception split, and that PO Exceptions are still excluded. Write locations follow
[[mke-project-guardrails]] (sandbox, not the `prod_operations`/`prod_edw` locations the docs name).
See the full operating pattern in [[mke-operating-pattern]] and lessons in [[mke-lessons-learnt]].
