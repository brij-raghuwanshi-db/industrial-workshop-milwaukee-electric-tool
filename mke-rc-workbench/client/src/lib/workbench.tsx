// Workbench visual helpers — stamps, provenance chips, formatters, sparkline.
// Ported from prototype/js/app.js (stamp/critStamp/verdictStamp/usd/spark).
import type { ReactNode } from 'react';

export type Tier = 'VALIDATED' | 'CATALOG_ID' | 'DEMO_FALLBACK' | 'SYNTHETIC_MEASURE';

export function Prov({ tier }: { tier: Tier | string | null | undefined }) {
  if (!tier) return null;
  return <span className="wb-prov" title="Data provenance">{tier}</span>;
}

export function Stamp({ kind, children }: { kind: string; children: ReactNode }) {
  return <span className={`wb-stamp ${kind}`}>{children}</span>;
}

export function VerdictStamp({ verdict, recov }: { verdict?: string | null; recov?: string | null }) {
  if (recov === 'UNRECOVERABLE') return <Stamp kind="lost">Lost battle</Stamp>;
  if (verdict === 'ACT') return <Stamp kind="act">ACT</Stamp>;
  if (verdict === 'WATCH') return <Stamp kind="watch">WATCH</Stamp>;
  if (verdict === 'DISMISS') return <Stamp kind="dismiss">DISMISS</Stamp>;
  return <Stamp kind="c">—</Stamp>;
}

export function RecovStamp({ recov }: { recov?: string | null }) {
  if (!recov) return null;
  return recov === 'UNRECOVERABLE'
    ? <Stamp kind="unrecoverable">Unrecoverable</Stamp>
    : <Stamp kind="recoverable">Recoverable</Stamp>;
}

export function CritStamp({ crit }: { crit?: string | null }) {
  if (!crit || crit === 'UNCLASSIFIED') return null;
  const k = crit.toLowerCase();
  const label = crit === 'A' ? 'Ⓐ' : crit === 'B' ? 'Ⓑ' : 'Ⓒ';
  return <Stamp kind={k === 'a' ? 'a' : k === 'b' ? 'b' : 'c'}>{label}</Stamp>;
}

export function CauseStamp({ cause }: { cause?: string | null }) {
  if (!cause) return null;
  const k = cause.toLowerCase();
  const kind = k.includes('demand') ? 'demand' : k.includes('hold') ? 'holds' : 'supply';
  return <Stamp kind={kind}>{cause}</Stamp>;
}

export function LifecycleStamp({ life }: { life?: string | null }) {
  if (!life || life === 'mature' || life === '') return null;
  return <Stamp kind="transition">{life === 'NPD' ? '🌱 NPD' : '🔁 transition'}</Stamp>;
}

// compact USD; coerces warehouse numeric strings.
export function usd(v: number | string | null | undefined): string {
  const n = typeof v === 'number' ? v : Number(v);
  if (v == null || Number.isNaN(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
  if (a >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M';
  if (a >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'k';
  return '$' + n.toFixed(0);
}

export function num(v: number | string | null | undefined): string {
  const n = typeof v === 'number' ? v : Number(v);
  if (v == null || Number.isNaN(n)) return '—';
  return n.toLocaleString();
}

export function Spark({ points }: { points: number[] }) {
  const m = Math.max(...points, 1);
  return (
    <span className="wb-spark" style={{ width: points.length * 6 }}>
      {points.map((v, i) => (
        <i key={i} style={{ height: Math.max(2, (v / m) * 18) }} />
      ))}
    </span>
  );
}
