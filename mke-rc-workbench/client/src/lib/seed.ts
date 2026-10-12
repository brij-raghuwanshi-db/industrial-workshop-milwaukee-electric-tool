/**
 * Non-data UI script. Everything the workbench displays is now live from the rc_* serving layer
 * or Lakebase — this file holds ONLY the guided-tour narration (a scripted walkthrough, not data)
 * and the honesty footer. The tour navigates to live SKUs; its narration deliberately states no
 * figures so it can never drift from the live pages, which show the real numbers.
 */

export interface TourStep { t: string; title: string; view: string; sku: string | null; drawer?: string; highlight?: string; say: string; }
export const TOUR: TourStep[] = [
  { t: '8:00', title: 'The worklist is already triaged', view: 'worklist', sku: null, say: 'Raw flags are not the morning. The ACT cases are. Lost battles sit apart. DISMISS is quiet on purpose. Every count here is live.' },
  { t: '8:05', title: 'Open a case — the answer is written', view: 'investigate', sku: '48-73-1200', say: 'A recoverable ACT case. The classifier tags, shortfall, holds and forward position are all live from the serving layer.' },
  { t: '8:16', title: 'The trap — don’t over-buy the target', view: 'investigate', sku: '88-93-0100', highlight: 'twotone', say: 'Part of the gap is the safety-stock target refreshing on higher demand, not a physical drop. The live waterfall split shows how much (DK-12).' },
  { t: '8:40', title: 'A trial that ends in do nothing', view: 'investigate', sku: '3697-22', say: 'Below the SS target but PAB stays positive — the verdict is DISMISS. Close it with evidence. This is how the tool earns trust.' },
  { t: '9:00', title: 'A lost battle — damage control', view: 'investigate', sku: '48-11-1850', say: 'Unrecoverable: the breach is inside the lead-time fence, no PO can arrive in time. Allocate, notify, log — not expedite.' },
  { t: '9:30', title: 'One supplier, many fires', view: 'constraints', sku: null, say: 'Flagged SKUs rolled up by supplier, name-normalized so concentration isn’t understated. One sourcing action, not thousands of tickets.' },
  { t: '10:00', title: 'Trials that haven’t opened yet', view: 'coming', sku: null, say: 'Forward risk straight from the plan — where the crunch weeks are, live.' },
  { t: '10:30', title: 'Fix the root — forecast bias', view: 'bias', sku: null, say: 'Governed FVA by channel: where the planner override adds error versus the system. Flag a re-baseline to demand.' },
  { t: '11:00', title: 'The other half of the book', view: 'excess', sku: null, say: 'Excess value not moving — projected balance parked well above target, live from the serving layer.' },
  { t: '16:45', title: 'Prove it was worth it', view: 'value', sku: null, say: 'At-risk committed dollars and the do-nothing count, live. Savings are only claimed once a read-back verifies them.' },
];

export const HONESTY_FOOTER =
  'Every screen reads the rc_* serving layer (READ-ONLY mke-rsc) or Lakebase. Numbers are live at the pinned snapshot; the only DERIVED value is the demand/supply unit split (no audited per-SKU formula). Realized savings are shown only after a next-snapshot read-back.';
