import { useState } from 'react';
import {
  useAnalyticsQuery,
  HeatmapChart,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
  Alert,
  AlertDescription,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { CriticalityBadge, RecoverabilityBadge, VerdictBadge, usd } from '../../lib/badges';

// ── The 26-scenario catalog ──
function ScenarioCatalog() {
  const { data, loading, error } = useAnalyticsQuery('scenario_catalog', {});
  const [openCode, setOpenCode] = useState<string | null>(null);

  if (loading) return <div className="space-y-2">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>;
  if (error) return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;
  if (!data || data.length === 0) return <div className="text-muted-foreground">No scenarios found.</div>;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Code</TableHead>
            <TableHead>Scenario</TableHead>
            <TableHead>Requirement</TableHead>
            <TableHead className="text-right">IDs</TableHead>
            <TableHead className="text-right">On spine</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((r) => {
            const code = r.scenario_code as string;
            return (
              <TableRow key={code} className={`cursor-pointer ${openCode === code ? 'bg-muted' : ''}`} onClick={() => setOpenCode(openCode === code ? null : code)}>
                <TableCell className="font-medium">{code}</TableCell>
                <TableCell>{r.scenario_title as string}</TableCell>
                <TableCell><Badge variant="outline">{r.requirement_map as string}</Badge></TableCell>
                <TableCell className="text-right">{Number(r.member_ids).toLocaleString()}</TableCell>
                <TableCell className="text-right">{Number(r.on_spine).toLocaleString()}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      {openCode && <ScenarioMembers code={openCode} />}
    </div>
  );
}

function ScenarioMembers({ code }: { code: string }) {
  const { data, loading, error } = useAnalyticsQuery('scenario_members', { scenario_code: sql.string(code) });
  return (
    <Card className="shadow-sm">
      <CardHeader><CardTitle className="text-sm">{code} — member IDs</CardTitle></CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-32" />}
        {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
        {data && data.length > 0 && (
          <div className="max-h-80 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead>Verdict</TableHead>
                  <TableHead>Crit</TableHead>
                  <TableHead>Recover</TableHead>
                  <TableHead className="text-right">$ at risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((r) => (
                  <TableRow key={r.item_id as string}>
                    <TableCell className="font-medium">{r.item_id as string}</TableCell>
                    <TableCell><VerdictBadge value={r.action_verdict as string} /></TableCell>
                    <TableCell><CriticalityBadge value={r.criticality_class as string} /></TableCell>
                    <TableCell><RecoverabilityBadge value={r.recoverability_class as string} /></TableCell>
                    <TableCell className="text-right">{usd(r.dollars_at_risk as number)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Recursive cause × week heatmap navigator (DK-22) ──
type Crumb = { level: string; parent: string; label: string };

function HeatmapNavigator() {
  // drill stack: start at cause level, parent 'ALL'
  const [stack, setStack] = useState<Crumb[]>([{ level: 'cause', parent: 'ALL', label: 'All causes' }]);
  const cur = stack[stack.length - 1];
  const { data, loading, error } = useAnalyticsQuery('cause_week_heat', {
    level: sql.string(cur.level),
    parent_filter: sql.string(cur.parent),
  });

  // next level in the ladder: cause -> org -> criticality (leaf)
  const nextLevel = (lvl: string) => (lvl === 'cause' ? 'org' : lvl === 'org' ? 'criticality' : null);

  function drill(rowKey: string, rowLabel: string, childRowCount: number) {
    const nl = nextLevel(cur.level);
    if (!nl) return; // leaf
    // stop-rule: only recurse while the child level would band (>= ~4 rows). Otherwise stay.
    if (childRowCount < 4) return;
    setStack([...stack, { level: nl, parent: rowKey, label: rowLabel }]);
  }
  function popTo(idx: number) {
    setStack(stack.slice(0, idx + 1));
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-1 text-sm">
        {stack.map((c, i) => (
          <span key={`${c.level}-${c.parent}`} className="flex items-center gap-1">
            <button className="underline underline-offset-2 hover:text-primary" onClick={() => popTo(i)}>{c.label}</button>
            {i < stack.length - 1 && <span className="text-muted-foreground">▸</span>}
          </span>
        ))}
      </div>
      <div className="text-xs text-muted-foreground">
        Cell intensity = $ short-pressure that week (darker = more committed value at risk). Hover a cell for the
        exact figure. Click a row below to drill; the leaf level stops at criticality.
      </div>
      {loading && <Skeleton className="h-64" />}
      {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
      {data && data.length === 0 && <div className="text-muted-foreground text-sm">No variance at this level — pop up a level.</div>}
      {data && data.length > 0 && (
        <>
          <HeatmapChart
            queryKey="cause_week_heat"
            parameters={{ level: sql.string(cur.level), parent_filter: sql.string(cur.parent) }}
            xKey="week"
            yAxisKey="row_label"
            yKey="cell_value_signed"
            colorPalette="sequential"
            showLabels={false}
          />
          <div className="flex flex-wrap gap-2">
            {[...new Map(data.map((r) => [r.row_key as string, r])).values()].map((r) => (
              <button
                key={r.row_key as string}
                className="text-xs border rounded px-2 py-1 hover:bg-muted"
                onClick={() => drill(r.row_key as string, r.row_label as string, Number(r.child_row_count))}
              >
                {r.row_label as string} ▸
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export function ScenariosPage() {
  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Scenarios</h2>
        <p className="text-sm text-muted-foreground mt-1">
          The 26 validated scenario lenses and the recursive cause × week heatmap. Every ID is live from the serving layer.
        </p>
      </div>
      <Tabs defaultValue="catalog">
        <TabsList>
          <TabsTrigger value="catalog">26 Scenarios</TabsTrigger>
          <TabsTrigger value="heatmap">Cause × Week Heatmap</TabsTrigger>
        </TabsList>
        <TabsContent value="catalog" className="mt-4">
          <Card className="shadow-sm"><CardContent className="pt-6"><ScenarioCatalog /></CardContent></Card>
        </TabsContent>
        <TabsContent value="heatmap" className="mt-4">
          <Card className="shadow-sm"><CardContent className="pt-6"><HeatmapNavigator /></CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
