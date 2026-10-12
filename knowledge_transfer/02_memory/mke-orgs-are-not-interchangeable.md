---
name: mke-orgs-are-not-interchangeable
description: "MKE orgs behave structurally differently; thresholds/bias/comparisons must be org-aware, not global"
metadata:
  type: project
  originSessionId: a9071493-e794-41ac-b42c-76c7ff4ac6ec
---

Validated 2026-08-31 against Rung-2 gold (`sandbox_operations.po_management.rung2_plan_vs_actual`): org 2120
Mexico is a **structurally different** operating environment from org 2012 Olive Branch, not a smaller copy.
The plan-vs-actual **logic generalized to 2120 with zero rewrite** (grain re-verified clean, org→plan
predicate prevents double-count), but the **judgement layer does not transfer**:
- **Bias magnitude differs ~5× (NOT inverted):** by row-sign BOTH orgs over-plan (actual on-hand > planned
  PAB) — 2012 41% over/26% under, 2120 38% over/19% under, medians 0% both. Mean onhand_variance_pct +101%
  (2012) vs +21% (2120) measures the overage-tail SIZE, not direction. (Both subagents initially said
  "inverted/opposite"; a sign test refuted it — a caution that outlier-inflated means aren't a direction.)
- **$-thresholds don't scale:** 2120 p99 miss is $9.6K vs 2012 $141.5K → the >$200K escalate never fires
  at 2120. Fixed $ bands mis-fire; a 2120 planner would see zero escalations and wrongly read "all clear."
- **3 NEW 2120-only facts** (only visible after loading 2120): planner concentration (6 planners vs 92; 2
  own ~85%), 41% Mexico-exclusive SKUs (4,041/9,758 — so cross-org "same item" tiles must INNER JOIN on the
  5,717 shared items, never union), and 2120 is a net-receiving node (ship/receive 0.094 vs 0.377 → hub fed
  by intercompany transfer/local suppliers). Plus lean-yet-green (SS 120 vs 2,343 units, 62% vs 36% green).

**Why:** the user pushed back — "we can't blindly say all orgs show same behavior" — and the data proved
them right.

**How to apply:** treat `organization_code` as a **judgement context, not just a filter**. Concrete
data-model changes (min-sufficient, fit inside the existing gold + Rung-3 pipeline): (1) org-keyed
`threshold_config` table with **percentile-based bands** that auto-calibrate per org (+ an absolute-$
floor); (2) **directional** per-org bias correction (read the org's bias sign; never a global correction);
(3) cross-org comparisons INNER JOIN on shared SKUs; (4) first-class planner attribute + a planner-load
view; (5) an `org_role` (hub vs producer) tag so a hub's low ship-rate isn't flagged as a miss. Deferred
(needs data beyond gold): confirming 2012→2120 intercompany transfer (material-transaction ledger);
COO/FX-import exposure (add COO from items_scd1). Full write-up:
`data_understanding/data_stories/org2120_validation/` (INDEX + A/B/C). See [[mke-data-profiling-facts]],
[[mke-lessons-learnt]].
