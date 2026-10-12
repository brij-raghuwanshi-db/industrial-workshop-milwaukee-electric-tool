import {
  Card, CardContent, Button, Input, Skeleton, Badge,
  Sheet, SheetContent, SheetHeader, SheetTitle, LineChart,
} from '@databricks/appkit-ui/react';
import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle, Search, Zap, Ban, Clock, ArrowUp, ArrowDown, TrendingUp, ShieldAlert, CheckCircle2, Sparkles,
} from 'lucide-react';
import { emitDataMutated, onDataMutated } from '../../lib/events';

interface QueueRow {
  item_id: string; item_description: string; abc: string; organization_code: string;
  planner_name: string; actual_end_on_hand: number; planned_safety_stock: number;
  stockout_gap_units: number; stockout_risk_usd: number; onhand_variance_pct: number;
  is_chronic: number; action_id: string | null; action_status: string | null; action_type: string | null;
}
interface Kpis {
  base: { total_stockout_items: number; total_stockout_risk_usd: number;
    chronic_supplier_items: number; distinct_planners: number } | null;
  actioned: { resolved_usd: number; resolved_items: number } | null;
}

const money = (n: number | null | undefined) =>
  n == null ? '—' : n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M'
    : n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);
const num = (n: number | null | undefined) => (n == null ? '—' : Math.round(n).toLocaleString());

const ACTIONS = [
  { key: 'EXPEDITE', label: 'Expedite', icon: Zap, tone: 'good' },
  { key: 'PULL_IN', label: 'Pull in', icon: ArrowUp, tone: 'good' },
  { key: 'NEW_PO', label: 'New PO', icon: ArrowUp, tone: 'good' },
  { key: 'INCREASE_QTY', label: 'Increase', icon: TrendingUp, tone: 'good' },
  { key: 'DECREASE_QTY', label: 'Decrease', icon: ArrowDown, tone: 'warn' },
  { key: 'PUSH_OUT', label: 'Push out', icon: Clock, tone: 'warn' },
  { key: 'CANCEL', label: 'Cancel', icon: Ban, tone: 'bad' },
  { key: 'WAIT_HOLD', label: 'Wait / hold', icon: Clock, tone: 'warn' },
];

export function CockpitPage() {
  const [rows, setRows] = useState<QueueRow[]>([]);
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<QueueRow | null>(null);
  const [flash, setFlash] = useState(false);

  const load = useCallback(async () => {
    const [qr, kr] = await Promise.all([
      fetch('/api/po/queue?limit=200').then((r) => r.json()),
      fetch('/api/po/kpis').then((r) => r.json()),
    ]);
    setRows(Array.isArray(qr) ? qr : []);
    setKpis(kr);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => onDataMutated(() => { setFlash(true); load(); setTimeout(() => setFlash(false), 900); }), [load]);

  const search = async (term: string) => {
    setQ(term);
    if (!term.trim()) { load(); return; }
    const res = await fetch(`/api/po/search?q=${encodeURIComponent(term)}`).then((r) => r.json());
    setRows((res.rows ?? []).map((x: Partial<QueueRow>) => ({ ...x } as QueueRow)));
  };

  const remainingUsd = kpis?.base ? kpis.base.total_stockout_risk_usd - (kpis.actioned?.resolved_usd ?? 0) : null;
  const resolvedPct = kpis?.base?.total_stockout_risk_usd
    ? Math.round(100 * (kpis.actioned?.resolved_usd ?? 0) / kpis.base.total_stockout_risk_usd) : 0;

  return (
    <div className="space-y-5">
      {/* Hero header */}
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-rose-500" /> Stockout Action Cockpit
          </h2>
          <p className="text-sm text-muted-foreground">
            Org 2012 · below-safety-stock items · ranked by $ at risk · act, forecast, and commit — live.
          </p>
        </div>
        <div className={`text-right transition-all ${flash ? 'scale-105' : ''}`}>
          <div className="text-xs text-muted-foreground">$ resolved this session</div>
          <div className="text-xl font-bold text-emerald-600">{money(kpis?.actioned?.resolved_usd ?? 0)}</div>
        </div>
      </div>

      {/* KPI hero row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi icon={AlertTriangle} tone="rose" title="Stockout items" value={num(kpis?.base?.total_stockout_items)}
             sub={`${kpis?.actioned?.resolved_items ?? 0} actioned`} />
        <Kpi icon={TrendingUp} tone="amber" title="$ at risk remaining" value={money(remainingUsd)}
             sub={`${resolvedPct}% resolved`} progress={resolvedPct} />
        <Kpi icon={ShieldAlert} tone="violet" title="Chronic-supplier" value={num(kpis?.base?.chronic_supplier_items)}
             sub="systemic — fix source" />
        <Kpi icon={CheckCircle2} tone="sky" title="Planners affected" value={num(kpis?.base?.distinct_planners)}
             sub="route the work" />
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
        <Input className="pl-9" placeholder="Search item id or description — M18 battery, 48111…"
               value={q} onChange={(e) => search(e.target.value)} />
      </div>

      {/* Queue */}
      <Card className="overflow-hidden">
        <div className="px-4 py-3 border-b bg-muted/30 text-sm font-semibold flex items-center justify-between">
          <span>Action queue{q ? ` · “${q}”` : ''} · {rows.length} items</span>
          <span className="text-xs font-normal text-violet-600 flex items-center gap-1">
            <Sparkles className="h-3 w-3" /> Click any row for AI analysis + recommended action
          </span>
        </div>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-2">{[...Array(7)].map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs uppercase text-muted-foreground bg-muted/20">
                  <tr className="text-left">
                    <th className="px-4 py-2">Item</th><th className="px-2 py-2">ABC</th>
                    <th className="px-2 py-2 text-right">Gap (u)</th><th className="px-2 py-2 text-right">$ at risk</th>
                    <th className="px-2 py-2">Supplier</th><th className="px-2 py-2">Planner</th>
                    <th className="px-2 py-2">Status</th><th className="px-2 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => {
                    const done = !!r.action_status && r.action_status !== 'rejected';
                    return (
                      <tr key={r.item_id} onClick={() => setSelected(r)}
                          title="Click for AI analysis + recommended action"
                          className={`border-b last:border-0 transition-colors cursor-pointer ${done ? 'bg-emerald-50/60 hover:bg-emerald-100/60' : 'hover:bg-violet-50/60'}`}>
                        <td className="px-4 py-2 font-medium">{r.item_id}
                          <div className="text-xs text-muted-foreground max-w-[220px] truncate">{r.item_description}</div></td>
                        <td className="px-2 py-2"><Badge variant="outline">{r.abc}</Badge></td>
                        <td className="px-2 py-2 text-right tabular-nums">{num(r.stockout_gap_units)}</td>
                        <td className="px-2 py-2 text-right font-semibold tabular-nums">{money(r.stockout_risk_usd)}</td>
                        <td className="px-2 py-2">{r.is_chronic
                          ? <Badge className="bg-rose-100 text-rose-700 hover:bg-rose-100">chronic</Badge>
                          : <span className="text-xs text-muted-foreground">ok</span>}</td>
                        <td className="px-2 py-2 text-xs">{r.planner_name}</td>
                        <td className="px-2 py-2">{done
                          ? <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">{r.action_type} ✓</Badge>
                          : <span className="text-xs text-muted-foreground">open</span>}</td>
                        <td className="px-2 py-2 text-right">
                          <Button size="sm" variant={done ? 'ghost' : 'default'}
                                  onClick={(e) => { e.stopPropagation(); setSelected(r); }}>
                            {done ? 'View' : 'Explain ▸'}</Button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {selected && <DetailDrawer row={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

const toneMap: Record<string, string> = {
  rose: 'text-rose-500 bg-rose-50', amber: 'text-amber-500 bg-amber-50',
  violet: 'text-violet-500 bg-violet-50', sky: 'text-sky-500 bg-sky-50',
};
function Kpi({ icon: Icon, tone, title, value, sub, progress }: {
  icon: React.ComponentType<{ className?: string }>; tone: string; title: string; value: string;
  sub?: string; progress?: number;
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs text-muted-foreground">{title}</div>
            <div className="text-2xl font-bold tabular-nums mt-0.5">{value}</div>
            {sub && <div className="text-xs text-muted-foreground mt-0.5">{sub}</div>}
          </div>
          <span className={`rounded-lg p-2 ${toneMap[tone]}`}><Icon className="h-4 w-4" /></span>
        </div>
        {progress != null && (
          <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${Math.min(100, progress)}%` }} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface FcRow { ds: string; y_forecast: number; y_lower: number; y_upper: number }

function DetailDrawer({ row, onClose }: { row: QueueRow; onClose: () => void }) {
  const [forecast, setForecast] = useState<FcRow[]>([]);
  const [ss, setSs] = useState<number | null>(null);
  const [whatif, setWhatif] = useState<Record<string, unknown> | null>(null);
  const [chosen, setChosen] = useState('EXPEDITE');
  const [finalQty, setFinalQty] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [explainText, setExplainText] = useState('');
  const [explainMeta, setExplainMeta] = useState<Record<string, unknown> | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [engine, setEngine] = useState<'auto' | 'llm' | 'rules'>('auto');

  useEffect(() => {
    fetch(`/api/po/forecast/${encodeURIComponent(row.item_id)}`).then((r) => r.json()).then((d) => {
      setForecast(d.forecast ?? []); setSs(d.safety_stock ?? null);
    });
  }, [row.item_id]);

  // Live-streaming agentic analysis (SSE): the explanation types out token-by-token, then a `done`
  // event delivers the structured recommendation. Callable on open (auto) AND via buttons (re-run /
  // switch engine). engine='llm' streams REAL model tokens; 'rules' streams the deterministic reasoning.
  const runExplain = useCallback((eng: 'auto' | 'llm' | 'rules') => {
    setExplaining(true); setExplainText(''); setExplainMeta(null);
    const es = new EventSource(`/api/po/explain-stream/${encodeURIComponent(row.item_id)}?engine=${eng}`);
    es.addEventListener('meta', (e) => setExplainMeta(JSON.parse((e as MessageEvent).data)));
    es.addEventListener('token', (e) => {
      const { t } = JSON.parse((e as MessageEvent).data) as { t: string };
      setExplainText((prev) => prev + t);
    });
    es.addEventListener('done', (e) => {
      const d = JSON.parse((e as MessageEvent).data) as Record<string, unknown>;
      setExplainMeta((m) => ({ ...(m ?? {}), ...d }));
      if (d.recommended_action) { setChosen(String(d.recommended_action)); runWhatIf(String(d.recommended_action)); }
      if (d.recommended_qty != null) setFinalQty(String(Math.round(Number(d.recommended_qty))));
      setExplaining(false); es.close();
    });
    es.addEventListener('error', () => { setExplaining(false); es.close(); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [row.item_id]);

  const pickEngine = (eng: 'auto' | 'llm' | 'rules') => { setEngine(eng); runExplain(eng); };

  // auto-run on open (the "click item → analysis streams in" moment)
  useEffect(() => { runExplain('auto'); }, [runExplain]);

  const runWhatIf = async (action: string) => {
    setChosen(action);
    const d = await fetch(`/api/po/whatif/${encodeURIComponent(row.item_id)}?action=${action}`).then((r) => r.json());
    setWhatif(d);
    if (d.simulated_units && !finalQty) setFinalQty(String(Math.round(d.simulated_units)));
  };

  const approve = async () => {
    setBusy(true);
    try {
      const recQty = whatif?.simulated_units ? Math.round(Number(whatif.simulated_units)) : null;
      const finQty = finalQty ? Number(finalQty) : recQty;
      const prop = await fetch('/api/po/actions/propose', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: row.item_id, organization_code: '2012', action_type: chosen,
          drafted_note: `Planner-approved ${chosen}`, requested_qty: finQty, decision_mode: 'order' }),
      }).then((r) => r.json());
      await fetch(`/api/po/actions/${prop.id}/execute`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: reason || null }),
      });
      emitDataMutated();
      onClose();
    } finally { setBusy(false); }
  };

  const breach = whatif?.simulated_breaches_ss;
  const chartData = forecast.map((f) => ({ ...f, safety_stock: ss ?? undefined }));

  return (
    <Sheet open onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            {row.item_id}
            {row.is_chronic ? <Badge className="bg-rose-100 text-rose-700">chronic supplier</Badge> : null}
          </SheetTitle>
          <div className="text-sm text-muted-foreground">{row.item_description}</div>
        </SheetHeader>

        <div className="space-y-5 mt-4">
          {/* context chips */}
          <div className="flex flex-wrap gap-2 text-xs">
            <Chip label="ABC" value={row.abc} />
            <Chip label="$ at risk" value={money(row.stockout_risk_usd)} strong />
            <Chip label="Gap" value={`${num(row.stockout_gap_units)} u`} />
            <Chip label="On-hand" value={num(row.actual_end_on_hand)} />
            <Chip label="Safety stock" value={num(row.planned_safety_stock)} />
            <Chip label="Planner" value={row.planner_name} />
          </div>

          {/* AGENTIC: the copilot streams an explanation live + recommends an action */}
          <Card className="border-violet-200 bg-violet-50/40">
            <CardContent className="pt-4">
              <div className="text-xs uppercase text-violet-700 mb-2 flex items-center justify-between gap-2 flex-wrap">
                <span className="flex items-center gap-1">
                  <Sparkles className={`h-3.5 w-3.5 ${explaining ? 'animate-pulse' : ''}`} /> AI analysis
                  {explaining ? ' · streaming…' : explainMeta?.source === 'llm' ? ' · LLM (live)' : explainMeta?.source === 'rules' ? ' · rules (live)' : ''}
                </span>
                {/* engine toggle — both options kept: real LLM stream vs deterministic reasoning */}
                <div className="flex items-center gap-1">
                  <div className="inline-flex rounded-md border border-violet-200 overflow-hidden">
                    {(['auto', 'llm', 'rules'] as const).map((eng) => (
                      <button key={eng} disabled={explaining} onClick={() => pickEngine(eng)}
                        className={`px-2 py-0.5 text-[11px] normal-case transition-colors ${
                          engine === eng ? 'bg-violet-600 text-white' : 'bg-white text-violet-700 hover:bg-violet-50'
                        } disabled:opacity-50`}>
                        {eng === 'auto' ? 'Auto' : eng === 'llm' ? 'LLM' : 'Rules'}
                      </button>
                    ))}
                  </div>
                  <Button size="sm" variant="ghost" className="h-6 px-2 text-violet-700"
                          disabled={explaining} onClick={() => runExplain(engine)}>
                    <Sparkles className="h-3 w-3 mr-1" />{explaining ? 'Analyzing…' : 'Re-run'}
                  </Button>
                </div>
              </div>
              {explainText || explaining ? (
                <div className="space-y-2">
                  <p className="text-sm">
                    {explainText}
                    {explaining ? <span className="inline-block w-1.5 h-4 -mb-0.5 ml-0.5 bg-violet-500 animate-pulse" /> : null}
                  </p>
                  {!explaining && explainMeta?.recommended_action ? (
                    <div className="flex items-center gap-2 flex-wrap text-sm">
                      <span className="text-muted-foreground">Recommends:</span>
                      <Badge className="bg-violet-600 text-white hover:bg-violet-600">{String(explainMeta.recommended_action)}
                        {explainMeta.recommended_qty != null ? ` · ${Math.round(Number(explainMeta.recommended_qty)).toLocaleString()} u` : ''}</Badge>
                      {explainMeta.confidence ? <span className="text-xs text-muted-foreground">confidence: {String(explainMeta.confidence)}</span> : null}
                      {explainMeta.reason ? <span className="text-xs text-muted-foreground">— {String(explainMeta.reason)}</span> : null}
                    </div>
                  ) : null}
                </div>
              ) : <div className="text-xs text-muted-foreground">Analysis unavailable.</div>}
            </CardContent>
          </Card>

          {/* forecast */}
          <Card>
            <div className="px-4 pt-3 text-sm font-semibold flex items-center gap-1">
              <TrendingUp className="h-4 w-4 text-sky-500" /> On-hand forecast (ai_forecast) vs safety stock
            </div>
            <CardContent className="pt-2">
              {chartData.length ? (
                <LineChart data={chartData} xKey="ds" yKey={['y_forecast', 'safety_stock']} height={200}
                  options={{
                    color: ['#2272B4', '#c0392b'],
                    legend: { show: true, bottom: 0, data: ['y_forecast', 'safety_stock'] },
                    series: [{}, { lineStyle: { type: 'dashed' } }],
                  }} />
              ) : <div className="text-xs text-muted-foreground py-6 text-center">Forecast unavailable — heuristic trend.</div>}
            </CardContent>
          </Card>

          {/* action verbs */}
          <div>
            <div className="text-sm font-medium mb-2">Choose an action — what-if simulates the effect on cover</div>
            <div className="flex flex-wrap gap-2">
              {ACTIONS.map((a) => {
                const active = chosen === a.key;
                return (
                  <Button key={a.key} size="sm" variant={active ? 'default' : 'outline'} onClick={() => runWhatIf(a.key)}>
                    <a.icon className="h-3.5 w-3.5 mr-1" />{a.label}
                  </Button>
                );
              })}
            </div>
          </div>

          {/* what-if result */}
          {whatif && !whatif.error && (
            <Card className={breach ? 'border-rose-300 bg-rose-50/40' : 'border-emerald-300 bg-emerald-50/40'}>
              <CardContent className="pt-4 text-sm space-y-1.5">
                <div className="font-semibold flex items-center gap-1">
                  {breach ? <AlertTriangle className="h-4 w-4 text-rose-500" /> : <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                  What-if: {String(whatif.action)} · {num(Number(whatif.simulated_units))} u
                </div>
                <div>Projected min on-hand <b>{num(Number(whatif.baseline_min_onhand))}</b> → <b>{num(Number(whatif.simulated_min_onhand))}</b>
                  {' '}(floor {num(Number(whatif.safety_stock_floor))})</div>
                <div className={breach ? 'text-rose-700' : 'text-emerald-700'}>
                  {breach ? '⚠ still breaches safety stock' : '✓ clears safety stock'} · exposure Δ {money(Number(whatif.exposure_delta_usd))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* decision capture */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground">Final quantity (override the rec)</label>
              <Input value={finalQty} onChange={(e) => setFinalQty(e.target.value)} placeholder="e.g. 75" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Reason if changed</label>
              <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="why 100 → 75?" />
            </div>
          </div>

          <Button className="w-full h-11 text-base" disabled={busy} onClick={approve}>
            {busy ? 'Submitting…' : `✓ Approve & execute ${chosen}`}
          </Button>
          <p className="text-[11px] text-muted-foreground text-center">
            Writes to Lakebase (audit trail) + SIMULATED Oracle push — no real external call. Decision captured for MLflow eval.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function Chip({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <span className="inline-flex flex-col rounded-md border px-2.5 py-1 bg-card">
      <span className="text-[10px] uppercase text-muted-foreground">{label}</span>
      <span className={strong ? 'font-bold' : 'font-medium'}>{value}</span>
    </span>
  );
}
