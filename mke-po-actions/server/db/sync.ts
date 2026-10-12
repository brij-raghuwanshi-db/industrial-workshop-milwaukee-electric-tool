// Delta -> Lakebase one-shot sync for the PO-actions app.
// Reads sandbox_operations.po_management.sdp_* via the AppKit ANALYTICS plugin (appkit.analytics.query),
// which authenticates with the app service-principal credential chain automatically — no token needed.
// Then chunk-inserts into the app_po mirror tables. Guarded on emptiness; tolerant of missing sources.
import { SCHEMA } from './schema-sql';

interface LakebaseLike {
  query(text: string, params?: unknown[]): Promise<{ rows: Record<string, unknown>[] }>;
}
// analytics.query returns a result whose rows we normalize to Record<string,unknown>[]
type AnalyticsQuery = (sql: string) => Promise<unknown>;

const CAT = 'sandbox_operations.po_management';

const SRC = {
  exceptions: `
    WITH latest_week AS (SELECT MAX(week_start) w FROM ${CAT}.sdp_plan_vs_actual),
    chronic AS (
      SELECT item_ref, org, MAX(CASE WHEN chronic_pct_late>=60 THEN 1 ELSE 0 END) is_chronic
      FROM ${CAT}.sdp_order_stage_gold GROUP BY item_ref, org)
    SELECT pva.item_id, pva.item_description, pva.abc, pva.organization_code,
         CAST(pva.week_start AS STRING) week_start, pva.planner_name,
         pva.actual_end_on_hand, pva.planned_safety_stock, pva.applied_standard_cost,
         (pva.planned_safety_stock - pva.actual_end_on_hand) stockout_gap_units,
         ROUND((pva.planned_safety_stock - pva.actual_end_on_hand)*pva.applied_standard_cost,0) stockout_risk_usd,
         pva.onhand_variance_pct,
         'Stockout / below safety stock' exception_type,
         COALESCE(c.is_chronic,0) is_chronic
    FROM ${CAT}.sdp_plan_vs_actual pva CROSS JOIN latest_week lw
    LEFT JOIN chronic c ON pva.item_id=c.item_ref AND pva.organization_code=c.org
    WHERE pva.organization_code='2012' AND pva.week_start=lw.w
      AND pva.planned_safety_stock>0 AND pva.actual_end_on_hand<pva.planned_safety_stock
    ORDER BY stockout_risk_usd DESC`,
  trajectory: `
    WITH latest_week AS (SELECT MAX(week_start) w FROM ${CAT}.sdp_plan_vs_actual),
    exc AS (SELECT DISTINCT item_id FROM ${CAT}.sdp_plan_vs_actual pva CROSS JOIN latest_week lw
            WHERE pva.organization_code='2012' AND pva.week_start=lw.w
              AND pva.planned_safety_stock>0 AND pva.actual_end_on_hand<pva.planned_safety_stock)
    SELECT pva.item_id, pva.organization_code, CAST(pva.week_start AS STRING) week_start,
         pva.item_description, pva.planned_pab, pva.actual_end_on_hand, pva.onhand_variance_abs,
         pva.onhand_variance_pct, pva.onhand_status, pva.actual_po_received, pva.actual_shipped,
         pva.planned_safety_stock, pva.planner_name, pva.applied_standard_cost
    FROM ${CAT}.sdp_plan_vs_actual pva JOIN exc ON pva.item_id=exc.item_id
    WHERE pva.organization_code='2012'`,
  kpi: `
    WITH latest_week AS (SELECT MAX(week_start) w FROM ${CAT}.sdp_plan_vs_actual),
    chronic AS (SELECT item_ref, org, MAX(CASE WHEN chronic_pct_late>=60 THEN 1 ELSE 0 END) is_chronic
                FROM ${CAT}.sdp_order_stage_gold GROUP BY item_ref, org),
    s AS (SELECT pva.item_id, pva.planner_name,
            ROUND((pva.planned_safety_stock-pva.actual_end_on_hand)*pva.applied_standard_cost,0) risk,
            COALESCE(c.is_chronic,0) is_chronic
          FROM ${CAT}.sdp_plan_vs_actual pva CROSS JOIN latest_week lw
          LEFT JOIN chronic c ON pva.item_id=c.item_ref AND pva.organization_code=c.org
          WHERE pva.organization_code='2012' AND pva.week_start=lw.w
            AND pva.planned_safety_stock>0 AND pva.actual_end_on_hand<pva.planned_safety_stock)
    SELECT '2012' org, COUNT(DISTINCT item_id) total_stockout_items,
      ROUND(SUM(risk),0) total_stockout_risk_usd,
      COUNT(DISTINCT CASE WHEN is_chronic=1 THEN item_id END) chronic_supplier_items,
      COUNT(DISTINCT planner_name) distinct_planners FROM s`,
};

const MIRROR = {
  exceptions: { target: `${SCHEMA}.mirror_exceptions`,
    columns: ['item_id','item_description','abc','organization_code','week_start','planner_name',
      'actual_end_on_hand','planned_safety_stock','applied_standard_cost','stockout_gap_units',
      'stockout_risk_usd','onhand_variance_pct','exception_type','is_chronic'] },
  trajectory: { target: `${SCHEMA}.mirror_trajectory`,
    columns: ['item_id','organization_code','week_start','item_description','planned_pab',
      'actual_end_on_hand','onhand_variance_abs','onhand_variance_pct','onhand_status',
      'actual_po_received','actual_shipped','planned_safety_stock','planner_name','applied_standard_cost'] },
  kpi: { target: `${SCHEMA}.mirror_kpi`,
    columns: ['org','total_stockout_items','total_stockout_risk_usd','chronic_supplier_items','distinct_planners'] },
};

// Normalize whatever appkit.analytics.query returns into an array of row-objects.
function toRows(res: unknown): Record<string, unknown>[] {
  if (!res) return [];
  const r = res as Record<string, unknown>;
  // common shapes: { rows: [...] } | [...] | { data: [...] } | { result: { data_array, schema } }
  if (Array.isArray(res)) return res as Record<string, unknown>[];
  if (Array.isArray(r.rows)) return r.rows as Record<string, unknown>[];
  if (Array.isArray(r.data)) return r.data as Record<string, unknown>[];
  const resu = r.result as { data_array?: unknown[][] } | undefined;
  const manifest = (r.manifest as { schema?: { columns?: { name: string }[] } }) || undefined;
  if (resu?.data_array && manifest?.schema?.columns) {
    const cols = manifest.schema.columns.map((c) => c.name);
    return resu.data_array.map((row) => Object.fromEntries(cols.map((c, i) => [c, row[i]])));
  }
  return [];
}

async function syncOne(lb: LakebaseLike, aq: AnalyticsQuery, key: keyof typeof MIRROR) {
  const cfg = MIRROR[key];
  const { rows: cnt } = await lb.query(`SELECT COUNT(*)::int n FROM ${cfg.target}`);
  if (Number((cnt[0] as { n: number }).n) > 0) {
    console.log(`[sync] ${cfg.target} already populated, skipping`);
    return;
  }
  let rows: Record<string, unknown>[];
  try {
    rows = toRows(await aq(SRC[key]));
  } catch (e) {
    console.warn(`[sync] source read failed for ${key} — leaving mirror empty:`, (e as Error).message);
    return;
  }
  if (!rows.length) { console.warn(`[sync] ${key}: source returned 0 rows`); return; }
  const cols = cfg.columns;
  const ncol = cols.length;
  for (let i = 0; i < rows.length; i += 1000) {
    const batch = rows.slice(i, i + 1000);
    const placeholders = batch
      .map((_, r) => `(${cols.map((__, c) => `$${r * ncol + c + 1}`).join(',')})`)
      .join(',');
    const flat = batch.flatMap((row) => cols.map((c) => (row[c] === undefined ? null : row[c])));
    await lb.query(
      `INSERT INTO ${cfg.target} (${cols.join(',')}) VALUES ${placeholders} ON CONFLICT DO NOTHING`,
      flat,
    );
  }
  console.log(`[sync] ${cfg.target}: inserted ${rows.length} rows`);
}

export async function syncFromDelta(lb: LakebaseLike, aq: AnalyticsQuery) {
  for (const key of Object.keys(MIRROR) as (keyof typeof MIRROR)[]) {
    try { await syncOne(lb, aq, key); }
    catch (e) { console.warn(`[sync] ${key} failed:`, (e as Error).message); }
  }
}
