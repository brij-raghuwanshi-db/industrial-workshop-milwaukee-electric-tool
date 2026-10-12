import {
  Card, CardContent, CardHeader, CardTitle, Badge, Skeleton, LineChart,
  Accordion, AccordionItem, AccordionTrigger, AccordionContent,
} from '@databricks/appkit-ui/react';
import { useState, useEffect } from 'react';
import { BookOpen, Lightbulb, Target, TrendingUp } from 'lucide-react';

// The guided tour: each scenario we uncovered, taught as STORY → REASONING → LIVE DATA → ACTIONS.
// Data is fetched live per subsection (never hardcoded) so the app itself onboards a newcomer.

interface Row { [k: string]: unknown }
const money = (n: number) => n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);

function useLazy(path: string, open: boolean) {
  const [data, setData] = useState<Row | Row[] | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!open || data) return;
    setLoading(true);
    fetch(path).then((r) => r.json()).then((d) => { setData(d); setLoading(false); }).catch(() => setLoading(false));
  }, [open, path, data]);
  return { data, loading };
}

export function ScenariosPage() {
  const [open, setOpen] = useState<string | undefined>('s0');
  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-violet-500" /> Supply Scenarios — the playbook
        </h2>
        <p className="text-sm text-muted-foreground">
          Every situation we uncovered in the data, told as a story: <b>what's happening → why it matters →
          the live evidence → what to do</b>. Open a section to see the real numbers pulled live, then act on
          them in the Cockpit. This is how a new planner learns the business from the app itself.
        </p>
      </div>

      <Accordion type="single" collapsible value={open} onValueChange={setOpen} className="space-y-3">
        <Scenario id="s0" tag="Start here" title="Why this app exists — insight ≠ action"
          open={open === 's0'}
          story="The dashboard tells you 2,516 items at Olive Branch (org 2012) are below safety stock — $91M of exposure. But a chart can't cancel a PO. Planners still had to leave the screen and act in Oracle/Excel."
          reasoning="This app closes the loop: see the ranked queue → ask why → forecast the future → simulate a what-if → approve → it's recorded with an audit trail and a (simulated) Oracle push. The dashboard is where you sit; here is where you fly."
          recommended="Go to the Cockpit, open the top item, and walk one action end-to-end."
          probable={["Expedite the below-safety-stock item", "Fix the supplier if it's chronically late"]}>
          <div className="text-sm text-muted-foreground">No query — this is the orientation. The rest of the sections each pull live data.</div>
        </Scenario>

        <Scenario id="s5" tag="S5 · Prioritization" title="Rank by dollars, not units (the $0.01-part trap)"
          open={open === 's5'} endpoint="/api/po/scenario/cost-vs-units"
          story="A planner naturally sorts the exception list by the biggest unit shortfall. But a 50,000-unit gap on a $0.01 scrap part matters far less than a 500-unit gap on a $500 battery."
          reasoning="We rank by $ at risk = gap × standard cost. Watch how the top-5-by-units list is almost entirely different items than the top-5-by-dollars — sorting by units would send the planner to the wrong fires."
          recommended="Always work the queue top-down by $ at risk (the Cockpit default)."
          probable={["Expedite the high-$ batteries first", "Ignore the high-unit / low-$ scrap items"]}
          render={(d) => {
            const dd = d as { by_dollar?: Row[]; by_units?: Row[] };
            return (
              <div className="grid md:grid-cols-2 gap-4">
                <MiniTable title="Top 5 by $ at risk (correct)" rows={dd.by_dollar ?? []} dollar />
                <MiniTable title="Top 5 by units (misleading)" rows={dd.by_units ?? []} />
              </div>
            );
          }} />

        <Scenario id="chronic" tag="Supply signal" title="Systemic vs one-off — fix the supplier, don't just expedite"
          open={open === 'chronic'} endpoint="/api/po/scenario/chronic"
          story="Some items miss safety stock because a supplier is chronically late (>60% of the time), not because of a one-time hiccup. Expediting the same item every week treats the symptom forever."
          reasoning="We flag chronic-supplier items from the historical lead-time record. For these, the right action is FIX SUPPLIER (a sourcing conversation), not another expedite. Here are the systemic items ranked by $."
          recommended="For chronic items, escalate to sourcing; for the rest, expedite."
          probable={["FIX SUPPLIER on chronic items", "EXPEDITE on one-offs"]}
          render={(d) => {
            const dd = d as { rows?: Row[]; total?: Row };
            return (
              <div>
                <div className="text-sm mb-2">Systemic exposure: <b>{money(Number(dd.total?.dollar ?? 0))}</b> across {String(dd.total?.items ?? 0)} items.</div>
                <MiniTable title="Chronic-supplier items (fix the source)" rows={dd.rows ?? []} dollar />
              </div>
            );
          }} />

        <Scenario id="hero" tag="S2 · On-hand & why" title="One SKU's story — how it drifted below safety stock"
          open={open === 'hero'} endpoint="/api/po/scenario/hero-trajectory"
          story="Take the single highest-$ item. Its plan said it would be fine; the actuals tell a different story — receipts stalled, on-hand slid under the safety-stock floor."
          reasoning="Overlay planned on-hand (PAB) vs actual on-hand vs the safety-stock floor over time. When actual crosses below the floor, that's the stockout risk crystallizing — and the forecast (in the Cockpit drawer) projects it forward."
          recommended="Open this SKU in the Cockpit, run the forecast + what-if, then approve the fix."
          probable={["Expedite / pull in the next receipt", "Increase the next order qty if demand is rising"]}
          render={(d) => {
            const dd = d as { item_id?: string; rows?: Row[] };
            return (
              <div>
                <div className="text-sm mb-2">Hero item: <Badge variant="outline">{dd.item_id ?? '—'}</Badge></div>
                {dd.rows?.length ? (
                  <LineChart data={dd.rows} xKey="week_start"
                    yKey={['planned_pab', 'actual_end_on_hand', 'planned_safety_stock']} height={260}
                    options={{ color: ['#2272B4', '#22a06b', '#c0392b'],
                      legend: { show: true, bottom: 0, data: ['planned_pab', 'actual_end_on_hand', 'planned_safety_stock'] },
                      series: [{}, {}, { lineStyle: { type: 'dashed' } }] }} />
                ) : <div className="text-sm text-muted-foreground">No trajectory.</div>}
              </div>
            );
          }} />
      </Accordion>
    </div>
  );
}

function Scenario({ id, tag, title, story, reasoning, recommended, probable, endpoint, open, render, children }: {
  id: string; tag: string; title: string; story: string; reasoning: string; recommended: string;
  probable: string[]; endpoint?: string; open: boolean;
  render?: (data: Row | Row[]) => React.ReactNode; children?: React.ReactNode;
}) {
  const { data, loading } = useLazy(endpoint ?? '', open && !!endpoint);
  return (
    <AccordionItem value={id} className="border rounded-lg px-4 bg-card">
      <AccordionTrigger className="hover:no-underline">
        <div className="flex items-center gap-3 text-left">
          <Badge className="bg-violet-100 text-violet-700 hover:bg-violet-100">{tag}</Badge>
          <span className="font-semibold">{title}</span>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pb-4">
        <Block icon={BookOpen} label="Story" text={story} />
        <Block icon={Lightbulb} label="Why it matters" text={reasoning} />
        <div className="rounded-lg border bg-muted/20 p-3">
          <div className="text-xs uppercase text-muted-foreground mb-2 flex items-center gap-1"><TrendingUp className="h-3.5 w-3.5" /> Live evidence</div>
          {endpoint ? (loading ? <Skeleton className="h-40 w-full" /> : data ? render?.(data) : <div className="text-sm text-muted-foreground">No data.</div>) : children}
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 rounded-lg border border-emerald-200 bg-emerald-50/40 p-3">
            <div className="text-xs uppercase text-emerald-700 mb-1 flex items-center gap-1"><Target className="h-3.5 w-3.5" /> Recommended action</div>
            <div className="text-sm">{recommended}</div>
          </div>
          <div className="flex-1 rounded-lg border p-3">
            <div className="text-xs uppercase text-muted-foreground mb-1">Probable actions</div>
            <div className="flex flex-wrap gap-1.5">{probable.map((p) => <Badge key={p} variant="outline">{p}</Badge>)}</div>
          </div>
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}

function Block({ icon: Icon, label, text }: { icon: React.ComponentType<{ className?: string }>; label: string; text: string }) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground mb-1 flex items-center gap-1"><Icon className="h-3.5 w-3.5" /> {label}</div>
      <p className="text-sm">{text}</p>
    </div>
  );
}

function MiniTable({ title, rows }: { title: string; rows: Row[]; dollar?: boolean }) {
  return (
    <Card><CardHeader className="pb-1"><CardTitle className="text-xs">{title}</CardTitle></CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-xs">
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b last:border-0">
                <td className="px-3 py-1.5 font-medium">{String(r.item_id)}</td>
                <td className="px-2 py-1.5 text-muted-foreground truncate max-w-[140px]">{String(r.item_description ?? '')}</td>
                <td className="px-2 py-1.5 text-right tabular-nums">{Number(r.gap_units ?? 0).toLocaleString()} u</td>
                <td className="px-3 py-1.5 text-right font-semibold tabular-nums">{money(Number(r.dollar ?? 0))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
