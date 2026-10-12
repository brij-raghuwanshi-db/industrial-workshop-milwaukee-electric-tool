/* Supply Root-Cause Workbench — prototype interactions */
(function () {
  const $ = (id) => document.getElementById(id);
  const state = {
    view: "worklist",
    tab: "now",
    sku: "3697-22",
    verdictFilter: "ALL",
    search: "",
    evidence: [],
    log: [],
    ledger: { projected: 0, realized: 1410000, notActed: 0, lossAvoided: 0, residual: 2100000, baseline: 2100000 },
    tour: -1,
    heat: [{ level: "cause", label: "All causes" }],
    studio: { supply: 750, demand: 0, transfer: 200 },
    ghost: true,
    scrub: 8,
  };

  const NAV = [
    ["worklist", "Worklist"],
    ["investigate", "Case"],
    ["coming", "Coming risk"],
    ["constraints", "Constraints"],
    ["excess", "Excess"],
    ["rebalance", "Rebalance"],
    ["stability", "Stability"],
    ["supplier", "Supplier"],
    ["bias", "Bias / FVA"],
    ["flow", "Flow"],
    ["portfolio", "Portfolio"],
    ["dormant", "Dormant"],
    ["heatmap", "Heatmap"],
    ["studio", "Studio"],
    ["alerts", "Alerts"],
    ["escalation", "Escalation"],
    ["log", "Log"],
    ["ledger", "Ledger"],
    ["value", "Value"],
    ["ask", "Ask"],
  ];

  function usd(n) {
    if (n == null) return "—";
    const a = Math.abs(n);
    if (a >= 1e9) return "$" + (n / 1e9).toFixed(1) + "B";
    if (a >= 1e6) return "$" + (n / 1e6).toFixed(2) + "M";
    if (a >= 1e3) return "$" + (n / 1e3).toFixed(0) + "k";
    return "$" + n.toFixed(0);
  }
  function stamp(kind, text) {
    return `<span class="stamp stamp-${kind}">${text}</span>`;
  }
  function spark(arr) {
    const m = Math.max(...arr, 1);
    return `<span class="spark">${arr.map((v) => `<i style="height:${Math.max(2, (v / m) * 18)}px"></i>`).join("")}</span>`;
  }
  function recovStamp(r) {
    return r === "UNRECOVERABLE" ? stamp("unrecoverable", "Unrecoverable") : stamp("recoverable", "Recoverable");
  }
  function verdictStamp(v, recov) {
    if (recov === "UNRECOVERABLE") return stamp("lost", "Lost battle");
    if (v === "ACT") return stamp("act", "ACT");
    if (v === "WATCH") return stamp("watch", "WATCH");
    return stamp("dismiss", "DISMISS");
  }
  function critStamp(c) {
    const k = (c || "C").toLowerCase();
    return stamp(k === "a" ? "a" : k === "b" ? "b" : "c", c === "A" ? "Ⓐ" : c === "B" ? "Ⓑ" : "Ⓒ");
  }
  function causeStamp(c) {
    const k = (c || "").toLowerCase();
    return stamp(k.includes("demand") ? "demand" : k.includes("hold") ? "holds" : "supply", c);
  }

  function ensureCase(id) {
    if (RC.CASES[id]) return RC.CASES[id];
    const row =
      RC.WATCHLIST.find((r) => r.id === id) ||
      (RC.COMING.find((r) => r.id === id) && {
        id,
        desc: "Forward-risk SKU",
        provenance: "CATALOG_ID",
        verdict: "WATCH",
        recov: RC.COMING.find((r) => r.id === id).recov,
        conv: 1,
        crit: "B",
        life: "",
        likely: "Supply",
        dollars: RC.COMING.find((r) => r.id === id).dollars,
        gap: RC.COMING.find((r) => r.id === id).depth,
        weeks: RC.COMING.find((r) => r.id === id).crosses,
        spark: [8, 10, 12, 14, 16, 18, 20, 22],
      }) ||
      RC.WATCHLIST[0];
    return {
      id: row.id,
      desc: row.desc,
      provenance: row.provenance,
      verdict: row.verdict,
      recoverability: row.recov,
      temporal: "acute",
      criticality: row.crit,
      lifecycle: row.life || "mature",
      convergence: row.conv,
      likely: row.likely,
      dollars: row.dollars,
      gap: row.gap,
      firstCross: row.weeks,
      headline: `${row.id} is ${Math.abs(row.gap)} units vs safety-stock target at ${row.weeks}. Likely cause ${row.likely}. Open the trial track to isolate.`,
      waterfall: { ssAtLt: Math.abs(row.gap), targetRefresh: 0, consumption: Math.round(Math.abs(row.gap) * 0.6), supplySlip: Math.round(Math.abs(row.gap) * 0.3), holds: Math.round(Math.abs(row.gap) * 0.1), gap: row.gap },
      contributions: [{ cause: row.likely, units: Math.abs(row.gap), pct: 100, owner: "planner", lever: "investigate", residualAfter: 0 }],
      demand: [],
      pos: [],
      holds: [],
      recommended: [{ rank: 1, action: "Open recommended playbook", detail: "Feasibility from network", feasible: true, covers: 0 }],
      position: row.spark.map((v) => v * 10),
      ss: Math.abs(row.gap),
      orgs: { "2012": { pos: row.gap, label: "org" } },
      coverage: { demand: "sourced", supply: "sourced", holds: "reconstructed", supplierExcel: "not-connected" },
      priors: { months: ["Sep"], vintages: ["late3", "now"], grid: [[100, 110]], provenance: "DEMO_FALLBACK" },
    };
  }

  function navHtml() {
    $("nav").innerHTML = NAV.map(
      ([id, lab]) => `<button type="button" data-view="${id}" class="${state.view === id ? "is-on" : ""}">${lab}</button>`
    ).join("");
  }

  function go(view, sku) {
    if (view === "ask") {
      $("genie").classList.add("is-on");
      if (!$("genie-msgs").dataset.seeded) {
        $("genie-msgs").innerHTML = `<div class="bubble bot">Ask over the serving layer. I will not invent PAB or safety stock — those are governed arithmetic.</div>`;
        $("genie-msgs").dataset.seeded = "1";
      }
      return;
    }
    state.view = view;
    if (sku) state.sku = sku;
    if (view === "investigate" && sku) state.evidence = [];
    document.body.classList.remove("hl-recommend");
    render();
  }

  function addLog(row) {
    state.log.unshift({ when: "2026-09-03 " + new Date().toTimeString().slice(0, 5), ...row });
  }
  function bump(kind, amt) {
    if (kind === "projected") state.ledger.projected += amt;
    if (kind === "notActed") state.ledger.notActed += amt;
    if (kind === "loss") state.ledger.lossAvoided += amt;
    state.ledger.residual = Math.max(0, state.ledger.baseline - state.ledger.projected);
  }

  /* ───────── views ───────── */
  function viewWorklist() {
    const p = RC.PORTFOLIO;
    const q = state.search.toLowerCase();
    let rows = RC.WATCHLIST.filter((r) => !q || r.id.toLowerCase().includes(q) || r.desc.toLowerCase().includes(q));
    if (state.verdictFilter === "ACT") rows = rows.filter((r) => r.verdict === "ACT" && r.recov !== "UNRECOVERABLE");
    if (state.verdictFilter === "WATCH") rows = rows.filter((r) => r.verdict === "WATCH");
    if (state.verdictFilter === "DISMISS") rows = rows.filter((r) => r.verdict === "DISMISS");
    if (state.verdictFilter === "LOST") rows = rows.filter((r) => r.recov === "UNRECOVERABLE");

    const nowTable = `
      <div class="panel">
        <div class="panel-h">
          <h2>Your worklist — ACT · recoverable · $</h2>
          <div class="tabs">
            ${["ALL", "ACT", "WATCH", "DISMISS", "LOST"].map((f) => `<button type="button" data-filt="${f}" class="${state.verdictFilter === f ? "is-on" : ""}">${f}</button>`).join("")}
          </div>
        </div>
        <table>
          <thead><tr>
            <th>SKU</th><th>Description</th><th>Gap</th><th>Crosses</th><th>Cause</th><th>Verdict</th><th>Recov</th><th>Conv</th><th>ABC</th><th class="num">$ at risk</th><th>8wk</th>
          </tr></thead>
          <tbody>
            ${rows
              .map((r) => {
                const lost = r.recov === "UNRECOVERABLE";
                const cls = r.verdict === "DISMISS" ? "row-dismiss" : lost ? "row-lost" : "";
                return `<tr class="${cls} ${state.sku === r.id ? "is-sel" : ""}" data-open="${r.id}">
                  <td class="sku">${r.id}</td>
                  <td>${r.desc} ${r.life ? stamp("transition", r.life) : ""} <span class="prov">${r.provenance}</span></td>
                  <td class="num">${r.gap.toLocaleString()}</td>
                  <td>${r.weeks}</td>
                  <td>${causeStamp(r.likely)}</td>
                  <td>${verdictStamp(r.verdict, r.recov)}</td>
                  <td>${recovStamp(r.recov)}</td>
                  <td>${r.conv}</td>
                  <td>${critStamp(r.crit)}</td>
                  <td class="num">${r.dollars ? usd(r.dollars) : "—"}</td>
                  <td>${spark(r.spark)}</td>
                </tr>`;
              })
              .join("")}
          </tbody>
        </table>
      </div>`;

    return `
      <p class="kicker">Detect · morning briefing</p>
      <h1 class="page-title">The 10,700-row alarm is not the work. These 128 cases are.</h1>
      <p class="lede">Classifier ran overnight on the Monday snapshot. ACT + recoverable + $ first. DISMISS is the cushion doing its job. Lost battles are damage control — not expedites.</p>
      <div class="banner">
        <span class="tag">OVERNIGHT</span>
        <span>${p.overnightNew} newly at-risk · ${p.overnightRecovered} recovered · 1 supplier pattern (Techtronic, ${p.techtronicSkus.toLocaleString()} SKUs)</span>
        <button type="button" data-view="alerts">Open alerts</button>
        <button type="button" data-view="constraints">Open constraint</button>
      </div>
      <div class="kpi-row">
        <div class="kpi"><div class="lab">ACT today</div><div class="val">${p.act} <em>of ${p.rawFlags.toLocaleString()}</em></div><div class="meta"><span class="up">${p.realFlags.toLocaleString()} real</span> · near-term + physical + recoverable</div></div>
        <div class="kpi"><div class="lab">$ at risk winnable</div><div class="val">${usd(p.dollarsWinnableM * 1e6)}</div><div class="meta">committed $ · not std-cost only</div></div>
        <div class="kpi"><div class="lab">WATCH</div><div class="val">${p.watch}</div><div class="meta">real but not yet / far-out</div></div>
        <div class="kpi quiet"><div class="lab">DISMISS · cushion</div><div class="val">${p.dismiss}</div><div class="meta">66% of below-SS flags never stock out</div></div>
        <div class="kpi lost"><div class="lab">Lost battles</div><div class="val">${p.lostBattles}</div><div class="meta">${usd(p.unrecoverableM * 1e6)} unrecoverable book · 98%</div></div>
      </div>
      <div class="tabs" style="margin-bottom:10px">
        <button type="button" class="${state.tab === "now" ? "is-on" : ""}" data-tab="now">Now</button>
        <button type="button" class="${state.tab === "coming" ? "is-on" : ""}" data-tab="coming">Coming risk</button>
        <button type="button" class="${state.tab === "patterns" ? "is-on" : ""}" data-tab="patterns">Patterns</button>
      </div>
      ${state.tab === "now" ? nowTable : state.tab === "coming" ? comingPanel() : patternsPanel()}
    `;
  }

  function comingPanel() {
    const max = Math.max(...RC.WAVE.map((w) => w.n));
    return `
      <div class="grid-2">
        <div class="panel">
          <div class="panel-h"><h2>Projected to cross below SS · next 8 weeks</h2><span class="prov">plan PAB — not a new forecast</span></div>
          <table>
            <thead><tr><th>SKU</th><th>Now</th><th>Crosses</th><th>Weeks</th><th>Depth</th><th>Recov</th><th>Move</th></tr></thead>
            <tbody>
              ${RC.COMING.map(
                (r) => `<tr data-open="${r.id}">
                  <td class="sku">${r.id}</td>
                  <td>${r.healthy ? "healthy" : "flagged"}</td>
                  <td>${r.crosses}</td>
                  <td>+${r.weeksTo}</td>
                  <td class="num">${r.depth}</td>
                  <td>${recovStamp(r.recov)}</td>
                  <td>${r.move} <span class="prov">${r.provenance}</span></td>
                </tr>`
              ).join("")}
            </tbody>
          </table>
        </div>
        <div class="exhibit">
          <h3>Risk wave — first-cross per week</h3>
          <p class="lede" style="margin-bottom:8px">wk37: <strong>${RC.PORTFOLIO.riskWaveWk37.toLocaleString()}</strong> SKUs crest. Capacity crunch — work top-$ first, log the deferred tail.</p>
          ${RC.WAVE.map(
            (w) => `<div class="wf-row"><span>${w.wk}</span><div class="wf-track"><div class="wf-fill gap" style="width:${(w.n / max) * 100}%"></div></div><span class="num">${w.n.toLocaleString()}</span></div>`
          ).join("")}
        </div>
      </div>`;
  }

  function patternsPanel() {
    const max = RC.CONSTRAINTS[0].skus;
    return `
      <div class="grid-2">
        <div class="exhibit">
          <h3>By supplier — escalate once</h3>
          ${RC.CONSTRAINTS.map(
            (s) => `<div class="wf-row" style="margin:10px 0"><span>${s.name}</span><div class="wf-track"><div class="wf-fill supply" style="width:${(s.skus / max) * 100}%"></div></div><span class="num">${s.skus.toLocaleString()}</span></div>`
          ).join("")}
          <button class="btn primary" type="button" data-view="constraints" style="margin-top:10px">Open constraint pivot</button>
        </div>
        <div class="exhibit">
          <h3>By customer (DG5)</h3>
          ${RC.PATTERNS_CUSTOMER.map(
            (c) => `<div style="margin:10px 0"><strong>${c.name}</strong> · ${usd(c.dollars)} · ${c.skus} SKUs<br><span style="color:var(--muted)">${c.note}</span></div>`
          ).join("")}
          <button class="btn" type="button" data-view="bias">Flag to demand</button>
        </div>
      </div>`;
  }

  function posChart(c) {
    const vals = c.position || [10, 20];
    const ss = c.ss || 100;
    const min = Math.min(...vals, ss, 0);
    const max = Math.max(...vals, ss);
    const h = 110;
    const w = 520;
    const x = (i) => (i / (vals.length - 1)) * w;
    const y = (v) => h - ((v - min) / (max - min || 1)) * h;
    const line = vals.map((v, i) => `${x(i)},${y(v)}`).join(" ");
    const ssY = y(ss);
    let ghosts = "";
    if (state.ghost && c.orgs) {
      const keys = Object.keys(c.orgs);
      keys.forEach((k, gi) => {
        const series = vals.map((v, i) => v + (c.orgs[k].pos > 0 ? 80 : -60) * Math.sin((i + gi) / 3));
        ghosts += `<polyline fill="none" stroke="#b7b1a4" stroke-width="1" points="${series.map((v, i) => `${x(i)},${y(v)}`).join(" ")}" />`;
      });
    }
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <line x1="0" y1="${ssY}" x2="${w}" y2="${ssY}" stroke="#6f6a60" stroke-dasharray="4 3" />
      ${ghosts}
      <polyline fill="none" stroke="#161513" stroke-width="2" points="${line}" />
    </svg>`;
  }

  function viewInvestigate() {
    const c = ensureCase(state.sku);
    const wf = c.waterfall;
    const tot = wf.ssAtLt || 1;
    const w = (n) => Math.max(4, (Math.abs(n) / tot) * 100);
    const locked = c.recoverability === "UNRECOVERABLE";
    const dismiss = c.verdict === "DISMISS" && c.recoverability !== "UNRECOVERABLE";
    const twoToneOn = state.highlight === "twotone";

    const locker =
      state.evidence.length === 0
        ? `<div class="empty">Evidence locker is empty. Run the trial track — Demand, then Supply, then Holds. Insert what belongs in the two-bullet letter.</div>`
        : state.evidence.map((e) => `<div class="lock-item"><div class="c">${e.cause}</div>${e.text}</div>`).join("");

    return `
      <div class="case">
        <div class="case-main">
          <div class="file-head">
            <div class="crumbs"><button type="button" data-view="worklist">‹ Worklist</button> · Case file · ${c.network || "Olive Branch"}</div>
            <div class="file-stamps">
              ${verdictStamp(c.verdict, c.recoverability)} ${recovStamp(c.recoverability)}
              ${stamp("demand", c.convergence + " causes")} ${critStamp(c.criticality)}
              ${c.lifecycle && c.lifecycle !== "mature" ? stamp("transition", c.lifecycle) : ""}
              <span class="prov">${c.provenance}</span>
            </div>
            <p class="kicker">${c.id} · ${c.desc}</p>
            <p class="finding">${c.headline}</p>
          </div>

          <div class="trial">
            ${(c.contributions || [{ cause: "Demand", pct: 0, units: 0 }])
              .concat(
                ["Demand", "Supply", "Holds"].filter((x) => !(c.contributions || []).some((k) => k.cause === x)).map((cause) => ({ cause, pct: 0, units: 0, owner: "—", lever: "clear" }))
              )
              .filter((v, i, a) => a.findIndex((z) => z.cause === v.cause) === i)
              .slice(0, 3)
              .map(
                (t) => `<div class="station" data-cause="${t.cause}" data-drawer="${t.cause.toLowerCase()}">
                  <div class="n">Trial ${t.cause === "Demand" ? "1 · most likely" : t.cause === "Supply" ? "2" : "3 · long tail"}</div>
                  <h3>${t.cause}</h3>
                  <div class="st">${t.pct}% · ${t.units}u · ${t.owner || ""}</div>
                  <div class="bar"></div>
                </div>`
              )
              .join("")}
          </div>

          <div class="split">
            <div class="exhibit">
              <h3>Exhibit — waterfall from SS @ lead time</h3>
              <div class="waterfall">
                <div class="wf-row"><span>SS @ LT</span><div class="wf-track"><div class="wf-fill ss" style="width:100%"></div></div><span class="num">${wf.ssAtLt}</span></div>
                <div class="wf-row ${twoToneOn ? "twotone-on" : ""}"><span>Target refresh</span><div class="wf-track"><div class="wf-fill refresh" style="width:${w(wf.targetRefresh)}%"></div></div><span class="num">+${wf.targetRefresh}</span></div>
                <div class="wf-row"><span>Consumption</span><div class="wf-track"><div class="wf-fill demand" style="width:${w(wf.consumption)}%"></div></div><span class="num">−${wf.consumption}</span></div>
                <div class="wf-row"><span>Supply slip</span><div class="wf-track"><div class="wf-fill supply" style="width:${w(wf.supplySlip)}%"></div></div><span class="num">−${wf.supplySlip}</span></div>
                <div class="wf-row"><span>Holds / adj</span><div class="wf-track"><div class="wf-fill holds" style="width:${w(wf.holds)}%"></div></div><span class="num">−${wf.holds}</span></div>
                <div class="wf-row"><span>Gap</span><div class="wf-track"><div class="wf-fill gap" style="width:${w(wf.gap)}%"></div></div><span class="num">${wf.gap}</span></div>
              </div>
              ${wf.targetRefresh ? `<div class="callout"><strong>DK-12 trap.</strong> +${wf.targetRefresh}u of this gap is the safety-stock <em>target</em> refreshing on higher demand — not a physical drop. Do not over-buy the full ${Math.abs(wf.gap)}.</div>` : ""}
              ${dismiss ? `<div class="callout"><strong>Do nothing.</strong> PAB stays positive. Close the flag with evidence.</div>` : ""}
              ${locked ? `<div class="callout"><strong>Unrecoverable.</strong> Breach inside the lead-time fence. Do not expedite a PO. Damage control: allocate / notify / log.</div>` : ""}
            </div>
            <div class="exhibit">
              <h3>Position over time · pooled solid, orgs ghost</h3>
              <div class="chart-pos">${posChart(c)}</div>
              <p class="ghost-note">Dashed = safety stock. Solid = pooled network. Faint = member orgs. ${c.firstCross} annotated in the finding.</p>
              <label style="font-size:11px"><input type="checkbox" id="ghost-tog" ${state.ghost ? "checked" : ""}/> Ghost overlay on</label>
              <div class="honesty">
                <span class="s">Demand sourced</span>
                <span class="s">PO who-moved sourced</span>
                <span class="r">Holds reconstructed</span>
                <span class="n">Supplier Excel not connected</span>
              </div>
            </div>
          </div>

          <div class="rec-bar">
            <h3>Recommended — feasibility-gated playbook</h3>
            ${(c.recommended || [])
              .map(
                (r) => `<div class="rec-item">
                  <span class="rk">${r.rank}</span>
                  <div><strong>${r.action}</strong><div style="opacity:.75;font-size:12px">${r.detail}</div></div>
                  <button type="button" data-act="${r.rank}">Do this</button>
                </div>`
              )
              .join("")}
          </div>
        </div>
        <aside class="locker">
          <h3>Evidence locker · the letter</h3>
          ${locker}
          <button class="go" type="button" data-view="escalation">Draft escalation</button>
        </aside>
      </div>`;
  }

  function viewComing() {
    return `<p class="kicker">Anticipate</p><h1 class="page-title">What’s about to break — while there’s still time.</h1><p class="lede">Uses the plan’s own forward PAB. Transfer-to-cover checked before any buy. ${RC.PORTFOLIO.transferToCoverFwd.toLocaleString()} forward crossings are coverable in-network.</p>${comingPanel()}`;
  }

  function viewConstraints() {
    const max = RC.CONSTRAINTS[0].skus;
    return `
      <p class="kicker">S7b · one root</p>
      <h1 class="page-title">3,035 fires. One defendant.</h1>
      <p class="lede">Techtronic Cordless after TTI LIMITED/LTD/LMTD normalization. Escalate once. Allocate scarce capacity to A-class committed SKUs.</p>
      <div class="grid-2">
        <div class="exhibit">
          ${RC.CONSTRAINTS.map(
            (s) => `<div style="margin:12px 0">
              <div style="display:flex;justify-content:space-between"><strong>${s.name}</strong><span class="num">${s.skus.toLocaleString()} SKUs · fill ${s.fill}%</span></div>
              <div class="barh supply"><span style="width:${(s.skus / max) * 100}%"></span></div>
              <span class="prov">${s.provenance}</span>
            </div>`
          ).join("")}
          <button class="btn primary" type="button" data-modal="qbr">Escalate pattern once</button>
        </div>
        <div class="exhibit">
          <h3>Allocate Techtronic capacity — top $ first</h3>
          <table>
            <thead><tr><th>SKU</th><th>ABC</th><th class="num">$</th></tr></thead>
            <tbody>
              ${RC.WATCHLIST.filter((r) => r.verdict === "ACT")
                .slice(0, 5)
                .map((r) => `<tr data-open="${r.id}"><td class="sku">${r.id}</td><td>${critStamp(r.crit)}</td><td class="num">${usd(r.dollars)}</td></tr>`)
                .join("")}
            </tbody>
          </table>
        </div>
      </div>`;
  }

  function viewExcess() {
    return `
      <p class="kicker">S1 · finance + planner</p>
      <h1 class="page-title">$452M is sitting above target. Shortage is the smaller problem.</h1>
      <p class="lede">Excess is 3.2× more prevalent than shortage. Rank by weeks-of-cover, not ×SS (×SS over-flags fast movers).</p>
      <div class="kpi-row">
        <div class="kpi"><div class="lab">$ excess</div><div class="val">${usd(RC.PORTFOLIO.excessM * 1e6)}</div><div class="meta">peak / next qtr · std cost</div></div>
        <div class="kpi"><div class="lab">SKUs overstocked</div><div class="val">${RC.PORTFOLIO.excessSkus.toLocaleString()}</div></div>
        <div class="kpi"><div class="lab">Excess : shortage</div><div class="val">3.2 : 1</div></div>
        <div class="kpi"><div class="lab">Never-shipped</div><div class="val">${usd(RC.PORTFOLIO_BREAK.neverShippedM * 1e6)}</div><div class="meta">pairs with dormant lens</div></div>
        <div class="kpi"><div class="lab">Alignment</div><div class="val">${RC.PORTFOLIO.alignmentPct}%</div></div>
      </div>
      <div class="panel"><table>
        <thead><tr><th>SKU</th><th>On-hand</th><th>SS</th><th class="num">Excess $</th><th>Weeks cover</th><th>Driver</th><th></th></tr></thead>
        <tbody>${RC.EXCESS.map(
          (r) => `<tr>
            <td class="sku">${r.id} <span class="prov">${r.provenance}</span></td>
            <td class="num">${r.onHand.toLocaleString()}</td>
            <td class="num">${r.ss.toLocaleString()}</td>
            <td class="num">${usd(r.dollars)}</td>
            <td>${r.weeksCover} wk ${r.weeksCover > 52 ? stamp("watch", "E&O") : ""}</td>
            <td>${r.driver}</td>
            <td><button class="btn" type="button" data-view="rebalance">Rebalance</button></td>
          </tr>`
        ).join("")}</tbody>
      </table></div>`;
  }

  function viewRebalance() {
    return `
      <p class="kicker">S2 · highest ROI</p>
      <h1 class="page-title">Short here. Excess there. Transfer, don’t buy.</h1>
      <p class="lede">${RC.PORTFOLIO.rebalanceNear.toLocaleString()} near-term item×network cases. Coverage is often partial — show coverable %, then buy the rest.</p>
      <div class="panel"><table>
        <thead><tr><th>SKU</th><th>Short org</th><th>Units</th><th>Excess org</th><th>Units</th><th>Coverable</th><th></th></tr></thead>
        <tbody>${RC.REBALANCE.map(
          (r) => `<tr data-open="${r.id}">
            <td class="sku">${r.id} <span class="prov">${r.provenance}</span></td>
            <td>${r.shortOrg}</td><td class="num">${r.shortU.toLocaleString()}</td>
            <td>${r.excessOrg}</td><td class="num">+${r.excessU.toLocaleString()}</td>
            <td>${r.pct}% (${r.coverable.toLocaleString()}u)</td>
            <td><button class="btn primary" type="button" data-modal="transfer" data-sku="${r.id}">Draft transfer</button></td>
          </tr>`
        ).join("")}</tbody>
      </table></div>`;
  }

  function viewStability() {
    return `
      <p class="kicker">S3 · don’t react to thrash</p>
      <h1 class="page-title">${RC.PORTFOLIO.nervousSeries.toLocaleString()} nervous series. Most of the book is stable (~3%).</h1>
      <div class="panel"><table>
        <thead><tr><th>SKU</th><th>Revisions</th><th>Reversals</th><th>Frozen zone</th><th>Swing</th><th>Target path</th></tr></thead>
        <tbody>${RC.NERVOUS.map(
          (r) => `<tr data-open="${r.id}"><td class="sku">${r.id}</td><td>${r.revisions}</td><td>${r.reversals}</td><td>${r.frozen ? stamp("watch", "yes") : "—"}</td><td>${r.swing}%</td><td>${spark(r.series)}</td></tr>`
        ).join("")}</tbody>
      </table></div>`;
  }

  function viewSupplier() {
    return `
      <p class="kicker">S4 · sourcing</p>
      <h1 class="page-title">Top 4 suppliers = 78% of self-initiated slips.</h1>
      <div class="panel"><table>
        <thead><tr><th>Supplier</th><th>Self-slips YTD</th><th>Share</th><th>Fill</th><th>Miss</th><th></th></tr></thead>
        <tbody>${RC.SUPPLIERS.map(
          (s) => `<tr><td>${s.name} ${s.chronic ? stamp("watch", "chronic") : ""} <span class="prov">${s.provenance}</span></td>
            <td class="num">${s.slips}</td><td>${s.share}%</td><td>${s.fill}%</td><td>${s.miss}</td>
            <td><button class="btn" type="button" data-modal="qbr">Schedule QBR</button></td></tr>`
        ).join("")}</tbody>
      </table></div>`;
  }

  function viewBias() {
    return `
      <p class="kicker">S5 · governed fact_forecast_accuracy</p>
      <h1 class="page-title">Where the planner override adds error — that is the FVA insight.</h1>
      <p class="lede">Demand plans are 10 TOL / PRT / ACC / HND / QP — not 20 Global. Lag-3 is the accuracy lock; priors on the case file still walk late 1–6.</p>
      <div class="panel"><table>
        <thead><tr><th>Customer</th><th class="num">Actual</th><th class="num">Late-3</th><th>Bias</th><th class="num">Planner</th><th class="num">System</th><th>Flag</th></tr></thead>
        <tbody>${RC.BIAS.map(
          (b) => `<tr>
            <td>${b.dg5} <span class="prov">${b.provenance}</span></td>
            <td class="num">${b.actual ? b.actual.toLocaleString() : "—"}</td>
            <td class="num">${b.late3 ? b.late3.toLocaleString() : "—"}</td>
            <td>${b.biasPct != null ? "+" + b.biasPct + "%" : "—"}</td>
            <td class="num">${b.planner != null ? b.planner.toLocaleString() : "—"}</td>
            <td class="num">${b.system != null ? b.system.toLocaleString() : "—"}</td>
            <td>${b.flag.includes("OVERRIDE") ? stamp("act", b.flag) : b.flag}</td>
          </tr>`
        ).join("")}</tbody>
      </table></div>
      <p style="margin-top:12px"><button class="btn primary" type="button" data-modal="demand">Flag re-baseline to demand · HDW FLD + ACE</button></p>`;
  }

  function viewFlow() {
    const f = RC.FLOW;
    return `
      <p class="kicker">S6 · count integrity</p>
      <h1 class="page-title">$127.5M in manufacturing. That is not shippable at the DC.</h1>
      <p class="lede">In-transit cost columns are empty. Open transfer orders (${f.openTransfers.toLocaleString()}) are the count-integrity signal.</p>
      <div class="flow">
        <div class="node-box warn"><div class="kicker">1080 MFG</div><div class="val" style="font-family:var(--serif);font-size:28px">${usd(f.mfg1080M * 1e6)}</div><div>${f.mfgUnits}M units · stranded</div></div>
        <div class="arrow">→</div>
        <div class="node-box"><div class="kicker">2014 / 2012 DC</div><div style="font-family:var(--serif);font-size:28px">${usd(f.dcM * 1e6)}</div><div>${f.dcUnits}M units</div></div>
        <div class="arrow">→</div>
        <div class="node-box"><div class="kicker">Customer</div><div>ship</div></div>
      </div>
      <button class="btn" type="button" data-view="rebalance">Stranded SKUs → rebalance</button>`;
  }

  function viewPortfolio() {
    const b = RC.PORTFOLIO_BREAK;
    return `
      <p class="kicker">S8 · S&OP</p>
      <h1 class="page-title">Inventory alignment is 54%. The Sankey is where the dollars sit.</h1>
      <div class="kpi-row">
        <div class="kpi"><div class="lab">Aligned</div><div class="val">${b.aligned}%</div><div class="meta">healthy $ / book $</div></div>
        <div class="kpi"><div class="lab">At-risk</div><div class="val">${b.atRisk}%</div></div>
        <div class="kpi"><div class="lab">Short</div><div class="val">${b.short}%</div></div>
        <div class="kpi"><div class="lab">Excess / E&O</div><div class="val">${b.excess}%</div></div>
        <div class="kpi"><div class="lab">Unclassified ABC</div><div class="val">37%</div><div class="meta">shown, never dropped</div></div>
      </div>
      <div class="sankey">
        <div class="sk-col"><div class="sk-node" style="flex:1">Total book $</div></div>
        <div class="sk-link"></div>
        <div class="sk-col">
          <div class="sk-node a" style="flex:2">Ⓐ A-class</div>
          <div class="sk-node" style="flex:1.4">Ⓑ</div>
          <div class="sk-node" style="flex:1">Ⓒ + Unclassified</div>
        </div>
        <div class="sk-link"></div>
        <div class="sk-col">
          <div class="sk-node ok" style="flex:${b.aligned}">Aligned ${b.aligned}%</div>
          <div class="sk-node warn" style="flex:${b.atRisk}">At-risk ${b.atRisk}%</div>
          <div class="sk-node a" style="flex:${b.short}">Short ${b.short}%</div>
          <div class="sk-node ex" style="flex:${b.excess}">Excess ${b.excess}%</div>
        </div>
      </div>`;
  }

  function viewDormant() {
    return `
      <p class="kicker">S9 · the other balance sheet</p>
      <h1 class="page-title">$545M never-shipped. $16M dormant. Managed holds are not E&O.</h1>
      <div class="panel"><table>
        <thead><tr><th>SKU</th><th>Org</th><th class="num">On-hand $</th><th>Last ship</th><th>ABC</th><th>Hold</th><th>Verdict</th></tr></thead>
        <tbody>${RC.DORMANT.map(
          (r) => `<tr><td class="sku">${r.id}</td><td>${r.org}</td><td class="num">${usd(r.dollars)}</td><td>${r.lastShip}</td><td>${critStamp(r.abc)}</td><td>${r.hold ? stamp("dismiss", "managed") : "—"}</td><td>${r.verdict}</td></tr>`
        ).join("")}</tbody>
      </table></div>`;
  }

  function viewHeatmap() {
    const level = state.heat[state.heat.length - 1].level;
    const rows = level === "cause" ? RC.HEAT_CAUSES : RC.HEAT_ORGS;
    if (level === "sku") {
      /* leaf handled below; keep org rows for context */
    }
    const weeks = ["wk37", "wk38", "wk39", "wk40", "wk41", "wk42", "wk43"];
    const heatRow = (r) =>
      `<div class="heat-row"><button type="button" class="sku" data-heat="${r.key}">${r.label}</button>${r.weeks
        .map((v, i) => {
          const bg = `rgba(180,35,24,${0.15 + v / 12})`;
          return `<div class="heat-cell" data-heat="${r.key}" style="background:${bg}">${v}</div>`;
        })
        .join("")}</div>`;
    const leaf =
      level === "org" || level === "sku"
        ? `<div class="panel" style="margin-top:12px"><div class="panel-h"><h2>Leaf — SKU list (stop-rule: don’t render SKU×week)</h2></div>
        <table><thead><tr><th>SKU</th><th>Verdict</th><th></th></tr></thead><tbody>
        ${RC.HEAT_SKUS.map((id) => {
          const c = ensureCase(id);
          return `<tr data-open="${id}"><td class="sku">${id}</td><td>${verdictStamp(c.verdict, c.recoverability)}</td><td><button class="btn" data-open="${id}">Investigate</button></td></tr>`;
        }).join("")}
        </tbody></table></div>`
        : "";
    return `
      <p class="kicker">S12 · DK-22</p>
      <h1 class="page-title">Cause × week. Horizontal is chronic. Vertical is a wave. A lone cell is acute.</h1>
      <p class="lede">$-weighted and signed. Weeks-by-volume are near-uniform — the story is row concentration, not a volume grid.</p>
      <div class="crumb">${state.heat.map((h, i) => `<button type="button" data-crumb="${i}">${h.label}</button>`).join(" ▸ ")}</div>
      <div class="heat" style="margin-top:12px">
        <div class="heat-row"><span></span>${weeks.map((w) => `<span style="font-size:10px;color:var(--muted)">${w}</span>`).join("")}</div>
        ${rows.map(heatRow).join("")}
      </div>
      ${leaf}`;
  }

  function viewStudio() {
    const s = state.studio;
    return `
      <p class="kicker">Scenario studio · R21</p>
      <h1 class="page-title">Override the line. Watch the position recover — with MOQ enforced.</h1>
      <div class="grid-2">
        <div class="exhibit">
          <label>Incoming supply /wk <input type="number" id="st-sup" value="${s.supply}" /></label><br/><br/>
          <label>Demand Δ% <input type="number" id="st-dmd" value="${s.demand}" /></label><br/><br/>
          <label>Transfer from 1080 <input type="number" id="st-tr" value="${s.transfer}" /></label>
          <p class="ghost-note">MOQ 250 · multiple 50 · lead 3wk. Supplier cap is a manual override — not from a live feed.</p>
          <button class="btn primary" type="button" id="st-run">Re-project</button>
        </div>
        <div class="exhibit">
          <h3>Gap −904 → ${-904 + Math.round(s.transfer + (750 - s.supply) * -0.4)}</h3>
          <p>Scenario covers part of 3697-22. Apply to escalation when the planner accepts the override.</p>
        </div>
      </div>`;
  }

  function viewAlerts() {
    return `
      <p class="kicker">Push, not pull</p>
      <h1 class="page-title">New this snapshot.</h1>
      ${RC.ALERTS.map((a) => `<div class="banner" style="margin-bottom:8px"><span class="tag">${a.kind}</span><span>${a.text}</span>
        ${a.sku ? `<button type="button" data-open="${a.sku}">Investigate</button>` : ""}
        ${a.view ? `<button type="button" data-view="${a.view}">Open</button>` : ""}
      </div>`).join("")}`;
  }

  function viewEscalation() {
    const c = ensureCase(state.sku);
    const bullets =
      state.evidence.length > 0
        ? state.evidence.map((e) => `<li>${e.text}</li>`).join("")
        : `<li><strong>Root cause:</strong> ${c.headline}</li><li><strong>Risk:</strong> ${Math.abs(c.gap)}u below SS beginning ${c.firstCross}; ${usd(c.dollars)} at risk, ${c.network || "Olive Branch"} pooled.</li>`;
    return `
      <p class="kicker">Screen D · the artifact</p>
      <h1 class="page-title">The two-bullet letter. Same structure every time.</h1>
      <div class="letter">
        <h2>Subject: ${c.id} supply risk — ${Math.abs(c.gap)}u below SS ${c.firstCross}, ${c.likely || "multi"}-driven</h2>
        <ul>${bullets}</ul>
        <p>Actions proposed: ${c.recommended?.[0]?.action || "—"}</p>
        <div class="foot">AI-assisted draft from governed data — verify before sending. Sources: waterfall, consumption (10_demand_daily), PO change orders. Template first; fluent prose optional. <span class="prov">DETERMINISTIC_RULE</span></div>
      </div>
      <p style="margin-top:12px">
        <button class="btn primary" type="button" data-modal="send">Send · write to outbox</button>
        <button class="btn" type="button" onclick="navigator.clipboard.writeText(document.querySelector('.letter').innerText)">Copy</button>
      </p>`;
  }

  function viewLog() {
    const rows =
      state.log.length === 0
        ? `<tr><td colspan="6" style="color:var(--muted)">No actions yet this session. Transfer, dismiss, or send an escalation — they land here. Captured going forward only.</td></tr>`
        : state.log
            .map(
              (r) => `<tr><td>${r.when}</td><td class="sku">${r.sku}</td><td>${r.cause || "—"}</td><td>${r.suggested || "—"} → ${r.actual || r.suggested}</td><td>${r.by || "leo"}</td><td>${r.status}</td></tr>`
            )
            .join("");
    return `
      <p class="kicker">Screen E</p>
      <h1 class="page-title">What we found. What we did. What happened.</h1>
      <div class="panel"><table>
        <thead><tr><th>When</th><th>SKU</th><th>Cause</th><th>Suggested → actual</th><th>By</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>`;
  }

  function viewLedger() {
    const L = state.ledger;
    return `
      <p class="kicker">Screen G · DK-21</p>
      <h1 class="page-title">08:00 froze $2.10M at risk. The tape only moves when you act — and it stays honest.</h1>
      <div class="kpi-row">
        <div class="kpi"><div class="lab">🔵 Projected today</div><div class="val">${usd(L.projected)}</div><div class="meta">nothing is saved at the click</div></div>
        <div class="kpi"><div class="lab">✅ Realized this week</div><div class="val">${usd(L.realized)}</div><div class="meta">read-back from next snapshot</div></div>
        <div class="kpi quiet"><div class="lab">⚪ Correctly not-acted</div><div class="val">${usd(L.notActed)}</div><div class="meta">DISMISS / WATCH avoided over-order</div></div>
        <div class="kpi lost"><div class="lab">🟥 Loss avoided</div><div class="val">${usd(L.lossAvoided)}</div><div class="meta">unrecoverable — never in “saved”</div></div>
        <div class="kpi"><div class="lab">Residual risk</div><div class="val">${usd(L.residual)}</div></div>
      </div>
      <div class="panel"><table class="ledger-tape">
        <thead><tr><th>Time</th><th>SKU</th><th>Suggested → actual</th><th>State</th><th class="num">Δ$</th></tr></thead>
        <tbody>
          ${
            state.log.length
              ? state.log
                  .map((r) => `<tr><td>${r.when}</td><td>${r.sku}</td><td>${r.suggested} → ${r.actual || r.suggested} ${r.diverged ? '<span class="chip-div">div</span>' : ""}</td><td>${r.status}</td><td class="num">${r.delta ? usd(r.delta) : "—"}</td></tr>`)
                  .join("")
              : `<tr><td colspan="5">No actions logged — baseline $2.10M at risk. Start triaging.</td></tr>`
          }
        </tbody>
      </table></div>`;
  }

  function viewValue() {
    return `
      <p class="kicker">Screen F · quantify the savings</p>
      <h1 class="page-title">Minutes, not hours. And 412 times we correctly did nothing.</h1>
      <div class="kpi-row">
        <div class="kpi"><div class="lab">Time to answer</div><div class="val">~8 min</div><div class="meta">▼ from ~2 hrs stated baseline</div></div>
        <div class="kpi"><div class="lab">Systems touched</div><div class="val">1</div><div class="meta">▼ from 5–7</div></div>
        <div class="kpi quiet"><div class="lab">Actions suppressed</div><div class="val">412</div><div class="meta">false-alarm-avoided $</div></div>
        <div class="kpi"><div class="lab">$ protected (verified)</div><div class="val">$1.6M</div><div class="meta">read-back only — not proposed</div></div>
        <div class="kpi"><div class="lab">Cause mix</div><div class="val">61%</div><div class="meta">demand · matches the room’s Pareto</div></div>
      </div>
      <div class="exhibit">
        <h3>Impact ladder — don’t claim early</h3>
        <div class="wf-row"><span>Proposed</span><div class="wf-track"><div class="wf-fill refresh" style="width:90%"></div></div><span class="num">$3.1M</span></div>
        <div class="wf-row"><span>Verified</span><div class="wf-track"><div class="wf-fill ss" style="width:50%"></div></div><span class="num">$1.6M</span></div>
        <div class="wf-row"><span>Realized</span><div class="wf-track"><div class="wf-fill demand" style="width:28%"></div></div><span class="num">$0.9M</span></div>
      </div>`;
  }

  const VIEWS = {
    worklist: viewWorklist,
    investigate: viewInvestigate,
    coming: viewComing,
    constraints: viewConstraints,
    excess: viewExcess,
    rebalance: viewRebalance,
    stability: viewStability,
    supplier: viewSupplier,
    bias: viewBias,
    flow: viewFlow,
    portfolio: viewPortfolio,
    dormant: viewDormant,
    heatmap: viewHeatmap,
    studio: viewStudio,
    alerts: viewAlerts,
    escalation: viewEscalation,
    log: viewLog,
    ledger: viewLedger,
    value: viewValue,
  };

  function render() {
    navHtml();
    const fn = VIEWS[state.view] || viewWorklist;
    $("stage").innerHTML = fn();
    bindStage();
  }

  function bindStage() {
    $("stage").querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => go(b.dataset.view)));
    $("stage").querySelectorAll("[data-open]").forEach((b) =>
      b.addEventListener("click", () => {
        go("investigate", b.dataset.open);
      })
    );
    $("stage").querySelectorAll("[data-tab]").forEach((b) =>
      b.addEventListener("click", () => {
        state.tab = b.dataset.tab;
        render();
      })
    );
    $("stage").querySelectorAll("[data-filt]").forEach((b) =>
      b.addEventListener("click", () => {
        state.verdictFilter = b.dataset.filt;
        render();
      })
    );
    $("stage").querySelectorAll("[data-drawer]").forEach((b) => b.addEventListener("click", () => openDrawer(b.dataset.drawer)));
    $("stage").querySelectorAll("[data-act]").forEach((b) => b.addEventListener("click", () => doRecommend(+b.dataset.act)));
    $("stage").querySelectorAll("[data-modal]").forEach((b) => b.addEventListener("click", () => openModal(b.dataset.modal, b.dataset.sku)));
    $("stage").querySelectorAll("[data-heat]").forEach((b) =>
      b.addEventListener("click", () => {
        const cur = state.heat[state.heat.length - 1];
        if (cur.level === "cause") state.heat.push({ level: "org", label: b.dataset.heat });
        else if (cur.level === "org") state.heat.push({ level: "sku", label: b.dataset.heat });
        render();
      })
    );
    $("stage").querySelectorAll("[data-crumb]").forEach((b) =>
      b.addEventListener("click", () => {
        state.heat = state.heat.slice(0, +b.dataset.crumb + 1);
        render();
      })
    );
    const g = $("ghost-tog");
    if (g)
      g.addEventListener("change", () => {
        state.ghost = g.checked;
        render();
      });
    const run = $("st-run");
    if (run)
      run.addEventListener("click", () => {
        state.studio.supply = +$("st-sup").value;
        state.studio.demand = +$("st-dmd").value;
        state.studio.transfer = +$("st-tr").value;
        render();
      });
  }

  function openDrawer(which) {
    const c = ensureCase(state.sku);
    const title = which === "demand" ? "Demand — who did this?" : which === "supply" ? "Supply — who moved the PO?" : "Holds — is it even shippable?";
    let body = "";
    if (which === "demand") {
      body = `<p>${c.demand?.length ? "" : "No DG5 rows on this case — insert is still available from the finding."}</p>
        <table><thead><tr><th>Customer</th><th>Type</th><th>Forecast</th><th>Actual</th><th>Δ</th></tr></thead>
        <tbody>${(c.demand || [])
          .map(
            (d) => `<tr><td>${d.dg5}</td><td>${d.type}</td><td class="num">${d.forecast}</td><td class="num">${d.actual}</td><td class="num">${d.surprise > 0 ? "+" : ""}${d.surprise}</td></tr>`
          )
          .join("")}</tbody></table>
        <h3 style="margin-top:16px">Priors · late 1–6</h3>
        <table><thead><tr><th></th>${(c.priors?.vintages || []).map((v) => `<th>${v}</th>`).join("")}</tr></thead>
        <tbody>${(c.priors?.months || [])
          .map((m, i) => `<tr><td>${m}</td>${(c.priors.grid[i] || []).map((v) => `<td class="num">${v ?? "░"}</td>`).join("")}</tr>`)
          .join("")}</tbody></table>`;
    } else if (which === "supply") {
      body = `<table><thead><tr><th>PO</th><th>Requested</th><th>Promise</th><th>Slip</th><th>Moved by</th></tr></thead>
        <tbody>${(c.pos || [])
          .map(
            (p) => `<tr><td class="sku">${p.po}</td><td>${p.requested}</td><td>${p.promised}</td><td class="num">+${p.slipDays}d</td><td>${stamp(p.movedBy === "SUPPLIER" ? "act" : "watch", p.movedBy)}</td></tr>`
          )
          .join("")}</tbody></table>
        <p class="ghost-note">change_order_originator_type — the room assumed this was not in the EDW.</p>`;
    } else {
      body = `<table><thead><tr><th>Type</th><th>Org</th><th>Units</th><th>Reason</th></tr></thead>
        <tbody>${(c.holds || []).map((h) => `<tr><td>${h.type}</td><td>${h.org}</td><td class="num">${h.units}</td><td>${h.reason}</td></tr>`).join("") || `<tr><td colspan="4">No holds on this case. Holds are never “open” — use apply recency.</td></tr>`}</tbody></table>`;
    }
    $("drawer").innerHTML = `<button class="x" type="button" id="dx">×</button><h2>${title}</h2><p class="lede">${c.id}</p>${body}
      <p style="margin-top:16px"><button class="btn primary" type="button" id="ins">Insert into escalation</button></p>`;
    $("drawer").classList.add("is-on");
    $("drawer-back").classList.add("is-on");
    $("dx").onclick = closeDrawer;
    $("drawer-back").onclick = closeDrawer;
    $("ins").onclick = () => {
      const text =
        which === "demand"
          ? `Home Depot over-consumed +101u (251 vs 150, 134%), base demand, last 4 months.`
          : which === "supply"
            ? `PO 380020278 slipped 212 days, SUPPLIER-initiated.`
            : `18u quality hold at 2014 DC; signed adjustments read separately.`;
      state.evidence.push({ cause: which, text });
      closeDrawer();
      render();
    };
  }
  function closeDrawer() {
    $("drawer").classList.remove("is-on");
    $("drawer-back").classList.remove("is-on");
  }

  function doRecommend(rank) {
    const c = ensureCase(state.sku);
    const r = (c.recommended || []).find((x) => x.rank === rank) || c.recommended[0];
    if (/DISMISS/i.test(r.action)) return openModal("dismiss");
    if (/ALLOCATE|Notify|Log as committed/i.test(r.action)) return openModal("loss");
    if (/TRANSFER/i.test(r.action)) return openModal("transfer");
    if (/Flag/i.test(r.action)) return openModal("demand");
    return openModal("pullin");
  }

  function openModal(kind, sku) {
    const c = ensureCase(sku || state.sku);
    let html = "";
    if (kind === "transfer") {
      html = `<h2>Draft transfer</h2>
        <p>Move what we already own. ${c.id}: short at 2012, +3,797 at 2013 (or 1080→2014 on 2941).</p>
        <p>Qty <input id="m-qty" value="300" style="width:80px"/> · lane ~1wk · coverable partial on 3697-22.</p>
        <p>App suggested: transfer. Actual may differ — captured on close.</p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Log transfer · 🔵 projected</button></div>`;
    } else if (kind === "dismiss") {
      html = `<h2>Dismiss with evidence</h2>
        <p>${c.headline}</p>
        <p>PAB stays positive. This is the trust feature — not an absence of one.</p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Dismiss + close flag</button></div>`;
    } else if (kind === "loss") {
      html = `<h2>Damage control — committed loss</h2>
        <p>Inside the lead-time fence. This $ is <strong>not savings</strong>. Allocate, notify, then RCA for next quarter.</p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn danger" id="mok">Log lost battle</button></div>`;
    } else if (kind === "demand") {
      html = `<h2>Flag to demand</h2>
        <p>Structured handoff. Reason taxonomy is DK-8 governed codes — not invented buckets.</p>
        <p>Reason <select id="m-reason">${RC.REASON_CODES.map((x) => `<option>${x}</option>`).join("")}</select></p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Send to demand</button></div>`;
    } else if (kind === "qbr") {
      html = `<h2>Escalate pattern — once</h2>
        <p>Techtronic Cordless · 3,035 SKUs. One QBR + capacity allocation. Convergence credits <strong>once</strong>, not 3,035 times.</p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Log pattern escalation</button></div>`;
    } else if (kind === "send") {
      html = `<h2>Send escalation</h2>
        <p>Writes to Lakebase integration_outbox in production. Here: demo commit, then it appears on the log.</p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Send</button></div>`;
    } else if (kind === "pullin") {
      html = `<h2>Request pull-in</h2>
        <p>Feasible against lead time only if recoverable. Suggested vs actual captured on close.</p>
        <p>Actual action <select id="m-act"><option>pull-in</option><option>air-freight</option><option>no action</option></select></p>
        <p>Reason <select id="m-reason">${RC.REASON_CODES.map((x) => `<option>${x}</option>`).join("")}</select></p>
        <div class="actions"><button class="btn" id="mc">Cancel</button><button class="btn primary" id="mok">Log action</button></div>`;
    }
    $("modal").innerHTML = html;
    $("modal-back").classList.add("is-on");
    $("mc").onclick = closeModal;
    $("modal-back").onclick = (e) => {
      if (e.target.id === "modal-back") closeModal();
    };
    $("mok").onclick = () => {
      if (kind === "transfer") {
        addLog({ sku: c.id, cause: "Supply", suggested: "transfer 300", actual: "transfer 300", status: "🔵 projected", delta: 412000 });
        bump("projected", 412000);
      } else if (kind === "dismiss") {
        addLog({ sku: c.id, cause: "Cushion", suggested: "DISMISS", actual: "DISMISS", status: "⚪ not-acted", delta: 0 });
        bump("notActed", 88000);
      } else if (kind === "loss") {
        addLog({ sku: c.id, cause: "Unrecoverable", suggested: "allocate", actual: "allocate", status: "🟥 loss-avoided", delta: 260000 });
        bump("loss", 260000);
      } else if (kind === "demand" || kind === "qbr" || kind === "send" || kind === "pullin") {
        const act = $("m-act") ? $("m-act").value : kind;
        addLog({ sku: kind === "qbr" ? "Techtronic ×3035" : c.id, cause: "Demand/pattern", suggested: kind, actual: act, status: "Sent", delta: kind === "qbr" ? 640000 : 0 });
        if (kind === "qbr") bump("projected", 640000);
      }
      closeModal();
      if (kind === "send") go("log");
      else render();
    };
  }
  function closeModal() {
    $("modal-back").classList.remove("is-on");
  }

  function runTour(i) {
    state.tour = i;
    if (i < 0 || i >= RC.TOUR.length) {
      document.body.classList.remove("tour-on");
      return;
    }
    document.body.classList.add("tour-on");
    const step = RC.TOUR[i];
    $("tour-t").textContent = step.t;
    $("tour-say").textContent = step.say;
    state.highlight = step.highlight || null;
    document.body.classList.toggle("hl-recommend", step.highlight === "recommend");
    go(step.view, step.sku || undefined);
    if (step.drawer) setTimeout(() => openDrawer(step.drawer), 250);
    else closeDrawer();
  }

  /* chrome */
  $("nav").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-view]");
    if (b) go(b.dataset.view);
  });
  $("play").onclick = () => runTour(0);
  $("tour-next").onclick = () => runTour(state.tour + 1);
  $("tour-prev").onclick = () => runTour(Math.max(0, state.tour - 1));
  $("tour-end").onclick = () => {
    state.tour = -1;
    document.body.classList.remove("tour-on", "hl-recommend");
    closeDrawer();
  };
  $("f-search").addEventListener("input", (e) => {
    state.search = e.target.value;
    if (state.view === "worklist") render();
    const hit = RC.WATCHLIST.find((r) => r.id.toLowerCase() === e.target.value.toLowerCase());
    if (hit && e.target.value.length > 4) go("investigate", hit.id);
  });
  $("f-state").addEventListener("change", (e) => {
    document.body.classList.remove("state-loading", "state-empty", "state-error");
    if (e.target.value === "loading") document.body.classList.add("state-loading");
    if (e.target.value === "empty") document.body.classList.add("state-empty");
    if (e.target.value === "error") document.body.classList.add("state-error");
  });
  $("genie-x").onclick = () => $("genie").classList.remove("is-on");
  $("genie-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = $("genie-q").value.trim();
    if (!q) return;
    $("genie-msgs").innerHTML += `<div class="bubble user">${q}</div><div class="bubble bot">Top A-class ACT SKUs by committed $: 3697-22 ($6.98M), 345020 (unrecoverable — damage control), 2941-21Z. Numbers from the classifier spine — verify SQL.</div>`;
    $("genie-sql").textContent = `SELECT item_id, action_verdict, recoverability_class, committed_value\nFROM sandbox_operations.po_management.rc_serving_sku_week\nWHERE criticality_class = 'A' AND action_verdict = 'ACT'\nORDER BY committed_value DESC\nLIMIT 10;`;
    $("genie-q").value = "";
  });

  render();
})();
