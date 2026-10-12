/**
 * Supply Root-Cause Workbench — prototype data
 *
 * Tier A VALIDATED  = figures/IDs published in Day-3 validation / day-in-the-life
 * Tier B CATALOG_ID = real Milwaukee item IDs from the 1,560-ID catalog
 * Tier C DEMO_FALLBACK = structural cells the docs never published (PO digits, sparkline points)
 *
 * Not a live warehouse query. Headlines stay Tier A.
 */
window.RC = window.RC || {};

RC.META = {
  planner: "leo",
  email: "leo@milwaukeetool.com",
  network: "Olive Branch",
  orgs: ["1080", "2012", "2014", "2013"],
  plan: "20 Global Supply Plan",
  snapshot: "2026-08-31",
  onHandAsOf: "2026-09-02 06:00",
  freshnessNote: "plan snapshot Mon 2026-08-31 · on-hand 2026-09-02 06:00 · READ-ONLY source",
};

RC.PORTFOLIO = {
  provenance: "VALIDATED",
  rawFlags: 10700,
  realFlags: 3634,
  act: 128,
  watch: 884,
  dismiss: 412,
  lostBattles: 47,
  dollarsWinnableM: 14.2,
  unrecoverableM: 372.5,
  recoverableM: 3.7,
  unrecoverablePct: 98,
  excessM: 452,
  excessVsShortage: 3.2,
  excessSkus: 20500,
  rebalanceNear: 1646,
  transferToCoverFwd: 7508,
  nervousSeries: 2668,
  chronicAlwaysBelow: 2307,
  strandedMfgM: 127.5,
  alignmentPct: 54,
  riskWaveWk37: 6933,
  overnightNew: 9,
  overnightRecovered: 3,
  techtronicSkus: 3035,
};

RC.CASES = {
  "3697-22": {
    id: "3697-22",
    selling: "3697-22",
    desc: "M18 FUEL 2PC Combo Kit",
    family: "M18",
    provenance: "VALIDATED",
    role: "hero",
    verdict: "ACT",
    recoverability: "RECOVERABLE",
    temporal: "acute",
    criticality: "A",
    lifecycle: "mature",
    demandClass: "smooth",
    convergence: 2,
    likely: "Demand",
    dollars: 6980000,
    gap: -904,
    lowPoint: 15906,
    lowPointNote: "below SS target; never negative (V1)",
    firstCross: "wk36",
    weeksAtRisk: 3,
    spark: [40, 48, 52, 61, 70, 78, 85, 92],
    network: "Olive Branch",
    orgs: {
      "2012": { pos: -904, label: "DC — short" },
      "2013": { pos: 3797, label: "same network — headroom" },
      "2014": { pos: 120, label: "DC — on target" },
      "1080": { pos: 80, label: "Mfg" },
    },
    headline:
      "3697-22 fell 904 units below safety stock at wk36. PRIMARY driver: Home Depot over-consumed +101u (251 vs 150 forecast = 134%, last 4 months). CONTRIBUTING: PO 380020278 slipped 212 days, supplier-initiated. Note: +352u of the gap is the safety-stock TARGET refreshing on higher demand — not a physical drop.",
    waterfall: {
      ssAtLt: 904,
      targetRefresh: 352,
      consumption: 101,
      supplySlip: 40,
      holds: 18,
      gap: -904,
    },
    contributions: [
      { cause: "Demand", units: 540, pct: 71, owner: "demand team", lever: "re-baseline Home Depot", residualAfter: 600 },
      { cause: "Supply", units: 270, pct: 30, owner: "planner", lever: "pull-in / transfer", residualAfter: 300 },
      { cause: "Holds", units: 90, pct: 10, owner: "quality", lever: "release hold", residualAfter: 0 },
    ],
    demand: [
      { dg5: "HOME DEPOT", type: "Base", forecast: 150, actual: 251, surprise: 101, provenance: "VALIDATED" },
      { dg5: "FERGUSON", type: "Promo", forecast: 40, actual: 44, surprise: 4, provenance: "DEMO_FALLBACK" },
      { dg5: "ACE", type: "Base", forecast: 30, actual: 28, surprise: -2, provenance: "DEMO_FALLBACK" },
    ],
    priors: {
      months: ["Sep", "Oct", "Nov"],
      vintages: ["late6", "late5", "late4", "late3", "late2", "late1", "now"],
      grid: [
        [150, 150, 160, 180, 210, 240, 251],
        [140, 140, 150, 150, 175, 190, null],
        [130, 130, 135, 140, 150, null, null],
      ],
      provenance: "DEMO_FALLBACK",
    },
    pos: [
      {
        po: "380020278",
        requested: "2026-06-03",
        original: "2026-06-03",
        promised: "2027-01-01",
        slipDays: 212,
        movedBy: "SUPPLIER",
        qty: 750,
        provenance: "VALIDATED",
      },
      {
        po: "380020401",
        requested: "2026-02-24",
        original: "2026-02-24",
        promised: "2026-02-26",
        slipDays: 2,
        movedBy: "BUYER",
        qty: 200,
        provenance: "DEMO_FALLBACK",
      },
    ],
    holds: [
      { type: "Quality hold", org: "2014", units: 18, reason: "REJECTED insp", asOf: "2026-09-01", provenance: "DEMO_FALLBACK" },
      { type: "Cycle adj", org: "2012", units: -12, reason: "CC ADJ ERROR", asOf: "2026-08-28", provenance: "DEMO_FALLBACK" },
    ],
    recommended: [
      { rank: 1, action: "TRANSFER 300u from org 2013", detail: "+3,797 headroom, lane exists ~1wk", feasible: true, covers: 300 },
      { rank: 2, action: "Request supplier pull-in", detail: "covers ~300u more", feasible: true, covers: 300 },
      { rank: 3, action: "Flag remaining 600u to demand", detail: "Home Depot re-baseline", feasible: true, covers: 600 },
    ],
    position: [980, 960, 940, 910, 880, 850, 820, 790, 760, 730, 700, 670, 640, 610],
    ss: 904,
    coverage: { demand: "sourced", supply: "sourced", holds: "reconstructed", supplierExcel: "not-connected" },
  },
  "2941-21Z": {
    id: "2941-21Z",
    selling: "2941-21Z",
    desc: "M18 FUEL (catalog hero)",
    family: "M18",
    provenance: "CATALOG_ID",
    role: "named",
    verdict: "ACT",
    recoverability: "RECOVERABLE",
    temporal: "chronic",
    criticality: "A",
    lifecycle: "transition",
    demandClass: "smooth",
    convergence: 3,
    likely: "Demand",
    dollars: 412000,
    gap: -837,
    lowPoint: -837,
    firstCross: "wk36",
    weeksAtRisk: 6,
    spark: [30, 38, 44, 55, 62, 71, 80, 88],
    network: "Olive Branch",
    orgs: {
      "2014": { pos: -300, label: "DC — short" },
      "1080": { pos: 900, label: "Mfg — excess" },
      "2012": { pos: 40, label: "on target" },
    },
    headline:
      "2941-21Z is 837 units below safety stock at wk36. Three causes converging. Transfer from 1080 covers part of the short before any buy.",
    waterfall: { ssAtLt: 904, targetRefresh: 200, consumption: 101, supplySlip: 40, holds: 18, gap: -837 },
    contributions: [
      { cause: "Demand", units: 540, pct: 60, owner: "demand team", lever: "re-baseline", residualAfter: 600 },
      { cause: "Supply", units: 270, pct: 30, owner: "planner", lever: "pull-in", residualAfter: 300 },
      { cause: "Holds", units: 90, pct: 10, owner: "quality", lever: "release", residualAfter: 0 },
    ],
    demand: [
      { dg5: "HOME DEPOT", type: "Base", forecast: 150, actual: 251, surprise: 101, provenance: "VALIDATED" },
      { dg5: "ACE", type: "Base", forecast: 30, actual: 28, surprise: -2, provenance: "DEMO_FALLBACK" },
    ],
    priors: {
      months: ["Sep", "Oct", "Nov"],
      vintages: ["late6", "late5", "late4", "late3", "late2", "late1", "now"],
      grid: [
        [150, 150, 160, 180, 210, 240, 251],
        [140, 140, 150, 150, 175, 190, null],
        [130, 130, 135, 140, 150, null, null],
      ],
      provenance: "DEMO_FALLBACK",
    },
    pos: [
      { po: "380019104", requested: "2026-02-17", original: "2026-02-17", promised: "2026-03-10", slipDays: 21, movedBy: "SUPPLIER", qty: 750, provenance: "DEMO_FALLBACK" },
    ],
    holds: [{ type: "Quality hold", org: "2014", units: 18, reason: "REJECTED insp", asOf: "2026-09-01", provenance: "DEMO_FALLBACK" }],
    recommended: [
      { rank: 1, action: "TRANSFER 300u 1080 → 2014", detail: "covers the short; lane 14,772 hist.", feasible: true, covers: 300 },
      { rank: 2, action: "Flag residual to demand", detail: "Home Depot", feasible: true, covers: 600 },
    ],
    position: [900, 880, 850, 800, 740, 680, 620, 560, 500, 440, 400, 360, 320, 280],
    ss: 904,
    coverage: { demand: "sourced", supply: "sourced", holds: "reconstructed", supplierExcel: "not-connected" },
  },
  "296720": {
    id: "296720",
    selling: "296720",
    desc: "Cushion-dip SKU (do-nothing)",
    family: "Accessories",
    provenance: "VALIDATED",
    role: "dismiss",
    verdict: "DISMISS",
    recoverability: "RECOVERABLE",
    temporal: "acute",
    criticality: "C",
    lifecycle: "mature",
    demandClass: "smooth",
    convergence: 1,
    likely: "Demand",
    dollars: 0,
    gap: -31297,
    lowPoint: 20457,
    firstCross: "wk38",
    weeksAtRisk: 2,
    spark: [20, 22, 28, 40, 38, 24, 18, 12],
    network: "Olive Branch",
    orgs: { "2012": { pos: 20457, label: "never negative" } },
    headline:
      "Flagged below safety-stock TARGET at wk38 (−31,297 vs target), but on-hand never goes negative (low point +20,457). Dips into the cushion, recovers wk40. Safety stock is doing its job. Recommended: no action.",
    waterfall: { ssAtLt: 31297, targetRefresh: 0, consumption: 0, supplySlip: 0, holds: 0, gap: -31297 },
    contributions: [{ cause: "Demand", units: 0, pct: 100, owner: "none", lever: "do nothing", residualAfter: 0 }],
    demand: [],
    priors: { months: ["Sep"], vintages: ["late3", "now"], grid: [[100, 100]], provenance: "DEMO_FALLBACK" },
    pos: [],
    holds: [],
    recommended: [{ rank: 1, action: "DISMISS + close flag", detail: "PAB stays positive all 14 weeks", feasible: true, covers: 0 }],
    position: [28000, 27000, 25000, 23000, 22000, 21000, 20457, 21000, 23000, 25000, 26000, 27000, 27500, 28000],
    ss: 51754,
    coverage: { demand: "sourced", supply: "sourced", holds: "sourced", supplierExcel: "not-connected" },
  },
  "345020": {
    id: "345020",
    selling: "345020",
    desc: "Committed loss — inside lead-time fence",
    family: "M18",
    provenance: "VALIDATED",
    role: "lost",
    verdict: "ACT",
    recoverability: "UNRECOVERABLE",
    temporal: "acute",
    criticality: "A",
    lifecycle: "mature",
    demandClass: "smooth",
    convergence: 1,
    likely: "Supply",
    dollars: 4780000,
    gap: -1765,
    lowPoint: -1765,
    firstCross: "wk37",
    weeksAtRisk: 4,
    spark: [50, 55, 60, 70, 82, 90, 95, 99],
    network: "Olive Branch",
    orgs: { "2012": { pos: -1765, label: "no in-network excess" } },
    headline:
      "Crosses below SS wk37, INSIDE the 130-day lead-time fence — no PO can arrive in time. No in-network excess to transfer. This shortage is locked in.",
    waterfall: { ssAtLt: 1765, targetRefresh: 0, consumption: 40, supplySlip: 1725, holds: 0, gap: -1765 },
    contributions: [{ cause: "Supply", units: 1765, pct: 100, owner: "sourcing", lever: "allocate / notify / accept", residualAfter: 1765 }],
    demand: [],
    priors: { months: ["Sep"], vintages: ["late3"], grid: [[80]], provenance: "DEMO_FALLBACK" },
    pos: [{ po: "380088001", requested: "2026-01-10", original: "2026-01-10", promised: "2026-06-01", slipDays: 142, movedBy: "SUPPLIER", qty: 400, provenance: "DEMO_FALLBACK" }],
    holds: [],
    recommended: [
      { rank: 1, action: "ALLOCATE scarce supply", detail: "committed customers first", feasible: true, covers: 0 },
      { rank: 2, action: "Notify affected customers early", detail: "damage control — not an expedite", feasible: true, covers: 0 },
      { rank: 3, action: "Log as committed loss", detail: "then Full RCA to prevent next quarter", feasible: true, covers: 0 },
    ],
    position: [400, 200, 50, -200, -800, -1200, -1765, -1765, -1765, -1600, -1500, -1400, -1300, -1200],
    ss: 400,
    coverage: { demand: "sourced", supply: "sourced", holds: "sourced", supplierExcel: "not-connected" },
  },
};

RC.WATCHLIST = [
  { id: "3697-22", desc: "M18 FUEL 2PC Combo Kit", gap: -904, weeks: "wk36", likely: "Demand", verdict: "ACT", recov: "RECOVERABLE", conv: 2, crit: "A", life: "", dollars: 6980000, spark: [40, 48, 52, 61, 70, 78, 85, 92], provenance: "VALIDATED" },
  { id: "345020", desc: "Committed-loss SKU", gap: -1765, weeks: "wk37", likely: "Supply", verdict: "ACT", recov: "UNRECOVERABLE", conv: 1, crit: "A", life: "", dollars: 4780000, spark: [50, 55, 60, 70, 82, 90, 95, 99], provenance: "VALIDATED", bucket: "lost" },
  { id: "2941-21Z", desc: "M18 FUEL", gap: -837, weeks: "Oct", likely: "Demand", verdict: "ACT", recov: "RECOVERABLE", conv: 3, crit: "A", life: "transition", dollars: 412000, spark: [30, 38, 44, 55, 62, 71, 80, 88], provenance: "CATALOG_ID" },
  { id: "48-73-1321", desc: "PACKOUT accessory", gap: -1240, weeks: "6 wk", likely: "Supply", verdict: "ACT", recov: "RECOVERABLE", conv: 1, crit: "B", life: "", dollars: 2660000, spark: [20, 22, 28, 40, 55, 60, 70, 75], provenance: "CATALOG_ID" },
  { id: "2772A-21J", desc: "M18 kit", gap: -560, weeks: "3 wk", likely: "Holds", verdict: "ACT", recov: "RECOVERABLE", conv: 2, crit: "A", life: "", dollars: 190000, spark: [12, 14, 18, 22, 30, 28, 35, 40], provenance: "CATALOG_ID" },
  { id: "48-81-4780", desc: "M18 battery pack", gap: -420, weeks: "wk39", likely: "Supply", verdict: "WATCH", recov: "RECOVERABLE", conv: 1, crit: "B", life: "", dollars: 210000, spark: [8, 10, 12, 11, 14, 16, 18, 20], provenance: "CATALOG_ID" },
  { id: "2123-21HDJ", desc: "M18 FUEL hammer", gap: -180, weeks: "wk41", likely: "Demand", verdict: "WATCH", recov: "RECOVERABLE", conv: 1, crit: "A", life: "NPD", dollars: 95000, spark: [5, 6, 8, 9, 10, 12, 11, 13], provenance: "CATALOG_ID" },
  { id: "296720", desc: "Cushion dip", gap: -31297, weeks: "wk38", likely: "Demand", verdict: "DISMISS", recov: "RECOVERABLE", conv: 1, crit: "C", life: "", dollars: 0, spark: [20, 22, 28, 40, 38, 24, 18, 12], provenance: "VALIDATED" },
  { id: "48-25-1252", desc: "Saw blade", gap: -90, weeks: "wk40", likely: "Demand", verdict: "DISMISS", recov: "RECOVERABLE", conv: 1, crit: "C", life: "", dollars: 0, spark: [4, 5, 6, 8, 7, 5, 4, 3], provenance: "CATALOG_ID" },
  { id: "3401-20", desc: "Lighting", gap: -220, weeks: "wk42", likely: "Supply", verdict: "WATCH", recov: "UNRECOVERABLE", conv: 1, crit: "B", life: "", dollars: 88000, spark: [10, 12, 14, 16, 18, 20, 22, 24], provenance: "CATALOG_ID" },
];

RC.COMING = [
  { id: "48-73-1410", healthy: true, crosses: "wk41", weeksTo: 5, depth: -420, recov: "RECOVERABLE", move: "transfer 200 from 1080 (lane exists)", dollars: 210000, provenance: "CATALOG_ID" },
  { id: "2821-21J", healthy: true, crosses: "wk43", weeksTo: 7, depth: -180, recov: "RECOVERABLE", move: "small pull-in now avoids the crossing", dollars: 95000, provenance: "CATALOG_ID" },
  { id: "48-32-4171", healthy: true, crosses: "wk39", weeksTo: 3, depth: -310, recov: "UNRECOVERABLE", move: "inside lead time — transfer/allocate, do not PO", dollars: 180000, provenance: "CATALOG_ID" },
  { id: "CPPLH2001", healthy: true, crosses: "wk42", weeksTo: 6, depth: -90, recov: "RECOVERABLE", move: "pull-in 90u", dollars: 44000, provenance: "CATALOG_ID" },
  { id: "49-66-6654", healthy: true, crosses: "wk40", weeksTo: 4, depth: -250, recov: "RECOVERABLE", move: "transfer 250 from 2013", dollars: 120000, provenance: "CATALOG_ID" },
];

RC.WAVE = [
  { wk: "wk36", n: 612, provenance: "DEMO_FALLBACK" },
  { wk: "wk37", n: 6933, provenance: "VALIDATED" },
  { wk: "wk38", n: 612, provenance: "DEMO_FALLBACK" },
  { wk: "wk39", n: 441, provenance: "DEMO_FALLBACK" },
  { wk: "wk40", n: 380, provenance: "DEMO_FALLBACK" },
  { wk: "wk41", n: 290, provenance: "DEMO_FALLBACK" },
  { wk: "wk42", n: 210, provenance: "DEMO_FALLBACK" },
  { wk: "wk43", n: 160, provenance: "DEMO_FALLBACK" },
];

RC.CONSTRAINTS = [
  { name: "Techtronic Cordless", skus: 3035, share: 32, fill: 88, chronic: true, provenance: "VALIDATED", note: "TTI LIMITED/LTD/LMTD merged" },
  { name: "Milwaukee Mfg Corp", skus: 218, share: 8, fill: 94, chronic: false, provenance: "VALIDATED" },
  { name: "Pinehurst Mfg GmbH", skus: 123, share: 5, fill: 91, chronic: false, provenance: "VALIDATED" },
];

RC.PATTERNS_CUSTOMER = [
  { name: "Home Depot", dollars: 488000, skus: 9, note: "over-consuming across 9 SKUs", provenance: "VALIDATED" },
  { name: "TTI NZ", dollars: 210000, skus: 4, note: "+190% vs late-3", provenance: "VALIDATED" },
  { name: "ACE", dollars: 160000, skus: 3, note: "planner override adds error", provenance: "VALIDATED" },
];

RC.EXCESS = [
  { id: "273421", desc: "High-cover SKU", onHand: 12400, ss: 1800, dollars: 4520000, weeksCover: 237, driver: "fcst dropped", provenance: "VALIDATED" },
  { id: "290920", desc: "High-cover SKU", onHand: 9900, ss: 900, dollars: 5590000, weeksCover: 123, driver: "over-received", provenance: "VALIDATED" },
  { id: "48-22-8929", desc: "PACKOUT", onHand: 8200, ss: 1100, dollars: 1200000, weeksCover: 34, driver: "fcst dropped", provenance: "CATALOG_ID" },
  { id: "48-73-1434", desc: "Accessory", onHand: 6400, ss: 800, dollars: 800000, weeksCover: 41, driver: "over-received", provenance: "CATALOG_ID" },
  { id: "49-16-2650", desc: "Bit set", onHand: 4100, ss: 500, dollars: 420000, weeksCover: 28, driver: "MOQ", provenance: "CATALOG_ID" },
];

RC.REBALANCE = [
  { id: "3697-22", shortOrg: "2012", shortU: -904, excessOrg: "2013", excessU: 3797, coverable: 300, pct: 33, provenance: "VALIDATED" },
  { id: "48228902WM", shortOrg: "2013", shortU: -245000, excessOrg: "2012", excessU: 680000, coverable: 245000, pct: 100, provenance: "VALIDATED" },
  { id: "2941-21Z", shortOrg: "2014", shortU: -300, excessOrg: "1080", excessU: 900, coverable: 300, pct: 100, provenance: "CATALOG_ID" },
  { id: "48-32-4662CA", shortOrg: "2012", shortU: -180, excessOrg: "2014", excessU: 400, coverable: 180, pct: 100, provenance: "CATALOG_ID" },
];

RC.NERVOUS = [
  { id: "48-40-0720", revisions: 5, reversals: 4, frozen: true, swing: 200, series: [120, 340, 130, 360, 140], provenance: "CATALOG_ID" },
  { id: "2941-21Z", revisions: 4, reversals: 3, frozen: true, swing: 80, series: [200, 280, 210, 300, 220], provenance: "CATALOG_ID" },
  { id: "3401-20", revisions: 6, reversals: 5, frozen: false, swing: 140, series: [80, 200, 90, 210, 95], provenance: "CATALOG_ID" },
];

RC.SUPPLIERS = [
  { name: "Techtronic Cordless", slips: 408, share: 32, fill: 88, miss: 3, chronic: true, provenance: "VALIDATED" },
  { name: "Bolt Industrial", slips: 231, share: 18, fill: 94, miss: 1, chronic: false, provenance: "DEMO_FALLBACK" },
  { name: "Cordex", slips: 226, share: 18, fill: 91, miss: 2, chronic: true, provenance: "DEMO_FALLBACK" },
];

RC.BIAS = [
  { dg5: "TTI NZ", actual: 67442, late3: 23261, biasPct: 190, planner: null, system: null, flag: "chronic UNDER-forecast", provenance: "VALIDATED" },
  { dg5: "PCS", actual: 541265, late3: 257964, biasPct: 110, planner: null, system: null, flag: "chronic UNDER-forecast", provenance: "VALIDATED" },
  { dg5: "OTHER NA", actual: 760129, late3: 371871, biasPct: 104, planner: null, system: null, flag: "chronic UNDER-forecast", provenance: "VALIDATED" },
  { dg5: "HOME DEPOT", actual: null, late3: null, biasPct: null, planner: -587166, system: -581035, flag: "model+planner", provenance: "VALIDATED" },
  { dg5: "HDW FLD", actual: null, late3: null, biasPct: null, planner: -380873, system: -246844, flag: "OVERRIDE adds error", provenance: "VALIDATED" },
  { dg5: "ACE", actual: null, late3: null, biasPct: null, planner: -338302, system: -181870, flag: "OVERRIDE adds error", provenance: "VALIDATED" },
];

RC.FLOW = {
  mfg1080M: 127.5,
  dcM: 705,
  mfgUnits: 13.7,
  dcUnits: 43.4,
  openTransfers: 240197,
  closedTransfers: 445638,
  provenance: "VALIDATED",
};

RC.DORMANT = [
  { id: "4931-20", org: "2120", dollars: 1200000, lastShip: "412d ago", abc: "A", hold: false, verdict: "review E&O", provenance: "DEMO_FALLBACK" },
  { id: "2804-20", org: "2012", dollars: 400000, lastShip: "never", abc: "C", hold: true, verdict: "intentional", provenance: "DEMO_FALLBACK" },
  { id: "48-36-1308", org: "2014", dollars: 220000, lastShip: "180d ago", abc: "B", hold: false, verdict: "review E&O", provenance: "CATALOG_ID" },
];

RC.PORTFOLIO_BREAK = {
  aligned: 54,
  atRisk: 18,
  short: 12,
  excess: 16,
  neverShippedM: 545,
  dormantM: 16,
  provenance: "VALIDATED",
};

RC.HEAT_CAUSES = [
  { key: "Demand", label: "Demand · 10 TOL", weeks: [2, 4, 9, 3, 1, 1, 1] },
  { key: "Supply", label: "Supplier TTI", weeks: [8, 8, 8, 7, 6, 5, 4] },
  { key: "Holds", label: "Holds / quality", weeks: [1, 1, 6, 6, 5, 4, 3] },
  { key: "Org2120", label: "Org pool 2120", weeks: [5, 8, 8, 7, 6, 6, 5] },
];

RC.HEAT_ORGS = [
  { key: "2012", label: "inv-org 2012", weeks: [6, 7, 8, 5, 4, 3, 2] },
  { key: "2013", label: "inv-org 2013", weeks: [2, 3, 4, 3, 2, 2, 1] },
  { key: "2014", label: "inv-org 2014", weeks: [4, 5, 6, 5, 4, 3, 2] },
  { key: "1080", label: "inv-org 1080", weeks: [3, 4, 5, 4, 3, 2, 2] },
  { key: "2120", label: "inv-org 2120", weeks: [1, 2, 2, 1, 1, 1, 0] },
];

RC.HEAT_SKUS = ["3697-22", "2941-21Z", "48-73-1321", "2772A-21J", "345020"];

RC.REASON_CODES = [
  "Incorrect POS assumptions",
  "NPD/Transition",
  "Promo strategy change",
  "Business Decision",
  "Constrained Ordering",
  "Make-to-Order",
  "Timing",
  "Seasonality",
  "Expansion",
  "E&O",
  "Customer Opportunity",
  "Supplier capacity",
];

RC.ALERTS = [
  { kind: "new", text: "3697-22 crossed into risk (wk36) — cause pre-built", sku: "3697-22" },
  { kind: "pattern", text: "Techtronic slipped a pattern of 3,035 SKUs", sku: null, view: "constraints" },
  { kind: "ok", text: "4811 recovered after pull-in (demo)", sku: "48-73-1321" },
];

RC.TOUR = [
  { t: "8:00", title: "The worklist is already triaged", view: "worklist", sku: null, say: "10,700 raw flags are not the morning. 128 ACT cases are. Lost battles sit apart. DISMISS is quiet on purpose." },
  { t: "8:05", title: "Open the case — the answer is written", view: "investigate", sku: "3697-22", say: "A partner asked about 3697-22. The two-bullet finding is already at the top. Demand is on the stand first." },
  { t: "8:08", title: "Trial 1 — Demand", view: "investigate", sku: "3697-22", drawer: "demand", say: "Home Depot 251 vs 150, base demand. Who did this, answered on sight. Insert into the evidence locker." },
  { t: "8:12", title: "Trial 2 — Supply", view: "investigate", sku: "3697-22", drawer: "supply", say: "PO slipped 212 days. Moved by SUPPLIER — the room thought this was lost tribal knowledge." },
  { t: "8:16", title: "The trap — don’t over-buy the target", view: "investigate", sku: "3697-22", highlight: "twotone", say: "+352 of the −904 gap is the safety-stock target refreshing. That is not a physical drop." },
  { t: "8:20", title: "Verdict — transfer, don’t expedite", view: "investigate", sku: "3697-22", highlight: "recommend", say: "Org 2013 has +3,797 headroom. Recommended action #1 is TRANSFER 300, not a PO." },
  { t: "8:40", title: "A trial that ends in do nothing", view: "investigate", sku: "296720", say: "Below the SS target, never negative. Dismiss with evidence. This is how the tool earns trust." },
  { t: "9:00", title: "A lost battle — damage control", view: "investigate", sku: "345020", say: "Inside the 130-day fence. No PO can arrive. Allocate, notify, log. Full RCA is for prevention, not this week’s fix." },
  { t: "9:30", title: "3,035 fires, one defendant", view: "constraints", sku: null, say: "Techtronic Cordless after name-normalization. One sourcing action, not 3,035 tickets." },
  { t: "10:00", title: "Trials that haven’t opened yet", view: "coming", sku: null, say: "Forward PAB from the plan itself — not an invented forecast. wk37 is a capacity crunch: 6,933 SKUs." },
  { t: "10:30", title: "Fix the root — forecast bias", view: "bias", sku: null, say: "HDW FLD: the planner override adds error versus the system. Flag a re-baseline to demand." },
  { t: "11:00", title: "The other half of the book", view: "excess", sku: null, say: "$452M excess, 3.2× shortage. 273421 has 237 weeks of cover." },
  { t: "16:30", title: "The log writes itself", view: "log", sku: null, say: "Every transfer, dismiss, and lost-battle log is append-only. Tribal notes become memory." },
  { t: "16:45", title: "Prove it was worth it", view: "value", sku: null, say: "Minutes not hours. 412 actions suppressed. Verified $ only. The tool measures itself." },
];
