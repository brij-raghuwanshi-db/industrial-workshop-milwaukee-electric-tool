// The live-cascade bus. Every write emits `dataMutated`; every data view subscribes and refetches,
// so an approved action updates the queue + KPIs with no page reload. This is the payoff.
export const DATA_MUTATED = 'po:dataMutated';

export function emitDataMutated() {
  window.dispatchEvent(new CustomEvent(DATA_MUTATED));
}

export function onDataMutated(fn: () => void): () => void {
  const handler = () => fn();
  window.addEventListener(DATA_MUTATED, handler);
  return () => window.removeEventListener(DATA_MUTATED, handler);
}
