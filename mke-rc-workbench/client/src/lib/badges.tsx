import { Badge } from '@databricks/appkit-ui/react';

// Semantic classifier badges — colorPalette via Badge variant tokens (never hardcoded hex).
// AppKit Badge supports variant: default | secondary | destructive | outline.

export function VerdictBadge({ value }: { value: string | null }) {
  if (!value || value === 'none') return <Badge variant="outline">—</Badge>;
  const variant = value === 'ACT' ? 'destructive' : value === 'WATCH' ? 'default' : 'secondary';
  return <Badge variant={variant}>{value}</Badge>;
}

export function CriticalityBadge({ value }: { value: string | null }) {
  if (!value) return null;
  const label = value === 'UNCLASSIFIED' ? '—' : `Ⓒlass ${value}`;
  const variant = value === 'A' ? 'destructive' : value === 'B' ? 'default' : 'secondary';
  return <Badge variant={variant}>{label}</Badge>;
}

export function RecoverabilityBadge({ value }: { value: string | null }) {
  if (!value) return null;
  const variant = value === 'UNRECOVERABLE' ? 'destructive' : value === 'RECOVERABLE' ? 'secondary' : 'outline';
  return <Badge variant={variant}>{value}</Badge>;
}

export function LifecycleBadge({ value }: { value: string | null }) {
  if (!value || value === 'mature') return null;
  return <Badge variant="outline">{value === 'NPD' ? '🌱 NPD' : '🔁 transition'}</Badge>;
}

export function TemporalBadge({ value }: { value: string | null }) {
  if (!value || value === 'none') return null;
  const variant = value === 'chronic' ? 'destructive' : 'default';
  return <Badge variant={variant}>{value}</Badge>;
}

// Format a number as compact USD. Warehouse BIGINT/DECIMAL columns arrive as strings
// in the JSON payload, so coerce defensively before any numeric method.
export function usd(v: number | string | null | undefined): string {
  const n = typeof v === 'number' ? v : Number(v);
  if (v == null || Number.isNaN(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(n / 1e3).toFixed(0)}k`;
  return `$${n.toFixed(0)}`;
}

// Format a yyyyMMdd date_key (int or string) as a readable string.
export function fmtWeek(dateKey: number | string | null | undefined): string {
  if (dateKey == null) return '—';
  const s = String(dateKey);
  if (s.length !== 8) return s;
  return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
}
