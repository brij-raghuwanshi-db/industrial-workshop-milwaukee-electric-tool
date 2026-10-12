import {
  Card, CardContent, CardHeader, CardTitle, Skeleton, PieChart,
} from '@databricks/appkit-ui/react';
import { useState, useEffect } from 'react';
import { Info } from 'lucide-react';
import { onDataMutated } from '../../lib/events';

// Reliable horizontal bars (CSS) — deterministic, always render, look clean. The AppKit data-mode
// BarChart proved flaky with our JSON; these give us full control + labels + $ formatting.
const money = (n: number) => n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);
function Bars({ rows, labelKey, valueKey, color = '#2272B4' }: {
  rows: Record<string, unknown>[]; labelKey: string; valueKey: string; color?: string;
}) {
  const max = Math.max(1, ...rows.map((r) => Number(r[valueKey]) || 0));
  return (
    <div className="space-y-2">
      {rows.map((r, i) => {
        const v = Number(r[valueKey]) || 0;
        return (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className="w-28 shrink-0 truncate text-right text-muted-foreground">{String(r[labelKey])}</div>
            <div className="flex-1 bg-muted/40 rounded h-5 relative overflow-hidden">
              <div className="h-full rounded transition-all" style={{ width: `${Math.max(2, (v / max) * 100)}%`, background: color }} />
            </div>
            <div className="w-16 shrink-0 tabular-nums font-medium">{money(v)}</div>
          </div>
        );
      })}
    </div>
  );
}

// Native analytics from our OWN Lakebase mirrors (no catalog dependency). Every card teaches:
// a one-line "what this shows / why it matters" so a newcomer understands without prior knowledge.

interface Row { [k: string]: unknown }

function useEndpoint(path: string) {
  const [data, setData] = useState<Row[] | Row | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let alive = true;
    const load = () => fetch(path).then((r) => r.json()).then((d) => { if (alive) { setData(d); setLoading(false); } })
      .catch(() => alive && setLoading(false));
    load();
    const off = onDataMutated(load);
    return () => { alive = false; off(); };
  }, [path]);
  return { data, loading };
}

export function AnalyticsPage() {
  const abc = useEndpoint('/api/po/analytics/by-abc');
  const planner = useEndpoint('/api/po/analytics/by-planner');
  const chronic = useEndpoint('/api/po/analytics/chronic-split');
  const bands = useEndpoint('/api/po/analytics/risk-bands');
  const progress = useEndpoint('/api/po/analytics/progress');
  const p = (progress.data as Row) || {};
  const resolvedPct = p.total_usd ? Math.round(100 * Number(p.resolved_usd) / Number(p.total_usd)) : 0;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Stockout Analytics</h2>
        <p className="text-sm text-muted-foreground">
          Where the below-safety-stock exposure sits — by value class, by owner, and by supplier type —
          so you know <b>where to spend the morning</b>. Live from the action queue; updates as you act.
        </p>
      </div>

      {/* progress banner */}
      <Card className="bg-gradient-to-r from-emerald-50 to-transparent">
        <CardContent className="pt-4 flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="text-xs text-muted-foreground">Exposure resolved this session</div>
            <div className="text-2xl font-bold text-emerald-600">{money(Number(p.resolved_usd || 0))} <span className="text-sm text-muted-foreground">/ {money(Number(p.total_usd || 0))}</span></div>
          </div>
          <div className="flex-1 min-w-[200px] max-w-md">
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-emerald-500 transition-all" style={{ width: `${Math.min(100, resolvedPct)}%` }} />
            </div>
            <div className="text-xs text-muted-foreground mt-1">{String(p.executed ?? 0)} of {String(p.total_items ?? 0)} items actioned · {resolvedPct}% of $ resolved</div>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        <ChartCard title="$ at risk by ABC class"
          why="ABC = value tier (A = the vital few). A-items carry $64M of the $91M — discipline should focus there first.">
          {abc.loading ? <Sk /> : <Bars rows={(abc.data as Row[]) ?? []} labelKey="abc" valueKey="dollar_at_risk" color="#2272B4" />}
        </ChartCard>

        <ChartCard title="Systemic vs one-off exposure"
          why="Chronic-supplier items ($) are a recurring problem — fix the SOURCE, not the symptom. One-offs just need expediting.">
          {chronic.loading ? <Sk /> : <PieChart data={(chronic.data as Row[]) ?? []} xKey="kind" yKey="dollar_at_risk" height={240} />}
        </ChartCard>

        <ChartCard title="Who owns the fires — $ at risk by planner"
          why="The work has to be routed to a human. This ranks planners by the exposure they own, so you know who to alert.">
          {planner.loading ? <Sk /> : <Bars rows={(planner.data as Row[]) ?? []} labelKey="planner" valueKey="dollar_at_risk" color="#995495" />}
        </ChartCard>

        <ChartCard title="Exposure concentration — by $ band"
          why="A few huge items usually carry most of the risk (Pareto). Act on the ≥$1M band first for the biggest swing.">
          {bands.loading ? <Sk /> : <Bars rows={(bands.data as Row[]) ?? []} labelKey="band" valueKey="dollar_at_risk" color="#FF7054" />}
        </ChartCard>
      </div>

      <p className="text-xs text-muted-foreground">
        This is our own governed data rendered natively in the app. The full SDP AI/BI dashboard remains
        available in Databricks; here we surface the action-relevant cuts that update live as you act.
      </p>
    </div>
  );
}

function ChartCard({ title, why, children }: { title: string; why: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm">{title}</CardTitle>
        <p className="text-xs text-muted-foreground flex items-start gap-1"><Info className="h-3 w-3 mt-0.5 shrink-0" />{why}</p>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
const Sk = () => <Skeleton className="h-[240px] w-full" />;
