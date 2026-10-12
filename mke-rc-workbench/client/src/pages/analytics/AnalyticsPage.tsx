import { useState } from 'react';
import {
  useAnalyticsQuery,
  BarChart,
  LineChart,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { usd } from '../../lib/badges';

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="shadow-sm">
      <CardContent className="pt-6">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
        <div className="text-3xl font-bold text-foreground mt-1">{value}</div>
        {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
      </CardContent>
    </Card>
  );
}

function PortfolioHealth() {
  const { data, loading, error } = useAnalyticsQuery('alignment_kpi', {});
  if (loading) return <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>;
  if (error) return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;
  const k = data?.[0];
  const alignPct = Number(k?.alignment_pct ?? 0);
  const totalSkus = Number(k?.total_skus ?? 0);
  const alignedSkus = Number(k?.aligned_skus ?? 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Inventory alignment" value={`${alignPct}%`} sub="healthy $ / total book $" />
        <KpiCard label="Total book" value={usd(k?.total_book_value)} sub={`${totalSkus.toLocaleString()} SKUs`} />
        <KpiCard label="Aligned SKUs" value={alignedSkus.toLocaleString()} sub="within target" />
        <KpiCard label="At-risk + short" value={(totalSkus - alignedSkus).toLocaleString()} sub="need attention" />
      </div>
      <Card className="shadow-sm">
        <CardHeader><CardTitle className="text-sm">Book value by health status ($)</CardTitle></CardHeader>
        <CardContent>
          <BarChart queryKey="portfolio_health" xKey="health_status" yKey="dollars" />
        </CardContent>
      </Card>
    </div>
  );
}

function PatternRollup() {
  const [dimension, setDimension] = useState<string>('supplier');
  return (
    <Card className="shadow-sm">
      <CardHeader><CardTitle className="text-sm">Driver patterns — $ at risk</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="max-w-xs space-y-2">
          <Label htmlFor="dim">Group by</Label>
          <Select value={dimension} onValueChange={setDimension}>
            <SelectTrigger id="dim"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="supplier">Supplier</SelectItem>
              <SelectItem value="org">Org</SelectItem>
              <SelectItem value="criticality">Criticality</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <BarChart queryKey="pattern_rollup" parameters={{ dimension: sql.string(dimension) }} xKey="group_key" yKey="dollars_at_risk" orientation="horizontal" />
      </CardContent>
    </Card>
  );
}

function RiskWave() {
  return (
    <Card className="shadow-sm">
      <CardHeader><CardTitle className="text-sm">Risk wave — SKUs first-crossing per week</CardTitle></CardHeader>
      <CardContent>
        <LineChart queryKey="forward_risk" xKey="crosses_week" yKey="skus_crossing" />
      </CardContent>
    </Card>
  );
}

export function AnalyticsPage() {
  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Portfolio Health</h2>
        <p className="text-sm text-muted-foreground mt-1">
          The S&OP view: one alignment number, value-by-health, driver patterns, and the forward risk wave.
        </p>
      </div>
      <PortfolioHealth />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PatternRollup />
        <RiskWave />
      </div>
    </div>
  );
}
