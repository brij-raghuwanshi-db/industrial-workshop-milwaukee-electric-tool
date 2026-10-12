# MLflow & Databricks AI Engineering Playbook

Governing rule:

> No AI component is production-ready because it produced a convincing demo. It must have a
> versioned contract, representative evaluation dataset, deterministic tests, trace-based quality
> evaluation, human validation, identity & tool controls, deployment evidence, production
> monitoring, and a safe fallback.

Two related but distinct systems, both backed by MLflow: **traditional ML** (forecasting,
classification, ranking, anomaly detection, optimization inputs) and **GenAI/agents** (NL
interaction, retrieval, reasoning, tool selection, recommendations, supervised actions).

## Traditional ML vs GenAI responsibility

Decide first which system owns the problem. A forecast model predicts a distribution; it does not
decide an operational writeback without policy. A Genie Agent answers governed questions; it does
not do unrestricted transactional writeback. Calculations, approvals, Lakebase mutations, and
operational actions stay deterministic and typed regardless.

## ResponsesAgent is the standard for custom agents

Prefer `mlflow.pyfunc.ResponsesAgent` over the older `ChatModel` for new work. It is
framework-agnostic (pure Python / OpenAI SDK / LangGraph / LangChain), supports multi-turn,
tool-calling, streaming events, intermediate messages, multi-agent, and integrates with MLflow
logging/tracing/eval/serving and OpenAI Responses-API-compatible clients.

Every custom agent defines: versioned input & output-item schemas; conversation & correlation
IDs; structured tool-call/tool-result items; typed error/refusal behavior; streaming event
contract; trace tags (App version, agent version, prompt version, env, use case, domain, user
role); timeouts & token budgets; cancellation behavior; idempotency for action tools; safe
handling of unknown/future message-item types.

**Gotchas:** interface compatibility ≠ safe tools / useful traces / adequate eval / reproducible
deploy. Signature + example must cover realistic multi-turn & tool-call structures. Streaming and
non-streaming paths need independent tests. Intermediate tool messages may hold sensitive info —
redact deliberately. OpenAI-API compatibility is not permission to bypass Unity AI Gateway,
endpoint ACLs, payload policy, or Databricks auth. Pin all versions.

## Single agent vs supervisor / multi-agent

Introduce a supervisor only when routing/decomposition across genuinely distinct capabilities
creates measurable value. **Avoid** when: one agent + a deterministic router suffices; specialist
boundaries are labels over the same prompt/data; extra model calls add latency/cost without
improving task success; end-to-end failure diagnosis gets hard; permissions can't be scoped
independently; evaluators can't attribute an error; the workflow is deterministic steps better as
code/SQL/state-machines/Jobs.

Supervisor gotchas: evaluate routing accuracy separately from answer quality; test wrong/no/
multiple specialist selection, delegation loops, repeated tool calls, context loss, contradictory
specialists, partial failure, timeouts; apply least privilege independently per delegated agent/
function; never expose a general-purpose Python/SQL execution tool to an action-capable agent; a
specialist's NL answer is not an executable command — the supervisor emits a typed proposal a
deterministic policy layer validates; preserve parent-child trace relationships.

## Evaluation — combine layers, no single evaluator suffices

Deterministic scorers + LLM judges + domain-expert feedback + operational metrics + end-to-end
outcomes.

| Layer | Preferred evaluator |
|---|---|
| Contract (valid response/tool JSON) | Code scorer |
| Retrieval (required record/doc retrieved) | Ground-truth/code + retrieval judge |
| Grounding (claims supported by evidence) | Groundedness judge + citations check |
| Factuality (values match trusted data) | **Deterministic SQL comparison** |
| Calculation (variance/KPI correct) | Code/SQL scorer |
| Tool choice / arguments | Expected-tool code scorer; schema + exact/partial match |
| Supervisor routing | Routing confusion matrix + trace judge |
| Completeness | Guidelines/custom judge |
| Action policy (no action without approval) | Deterministic trace/state scorer |
| Safety / security | Safety judge + policy checks; adversarial + authz integration tests |
| User value | Human feedback + operational outcome |
| Operations | Trace metrics + platform telemetry |

Verify supply-chain quantities/dates/versions/calculations **deterministically** whenever
authoritative data exists — don't ask an LLM to check arithmetic, SQL equality, authorization,
state transitions, or idempotency.

**Datasets / suites:** smoke (tiny, every change) · golden (business-critical w/ expected facts,
SQL, tools, args, outcomes) · regression (every confirmed production failure becomes a durable
test) · adversarial (injection, unauthorized, exfiltration, tool abuse, malformed, ambiguous) ·
long-tail · performance · action-safety (prepare/approve/execute/verify, stale records,
duplicates, rollback, partial external failure) · model-change (rerun on any FM/prompt/tool/index/
framework change). Keep a human-labeled final holdout that was never used to tune prompts/judges.
No production secrets or unrestricted sensitive data in eval sets.

## LLM-judge discipline

Judges are useful for nuanced criteria code can't assess — not objective ground truth. A strong
custom judge specifies: exact object (response/trace/retrieval/tool/task); business context & user
role; allowed evidence; criteria & exclusions; output type & allowed values; anchored rubric;
pass/fail/borderline examples; required rationale; missing-context handling; judge model &
version.

Gotchas: scores shift with judge model/prompt/temperature/provider; judges can favor verbosity,
own model family, familiar phrasing, or reference-similar answers; a plausible rationale ≠ a
correct score; if the judge sees the expected answer it may score textual similarity; don't assume
a model is an unbiased judge of its own output; run repeated/multiple judges for high-variance/
high-impact criteria; track judge latency & cost (eval can cost more than generation); treat
prompt-optimization features as experiments, not invisible prod dependencies. Align judges with
domain-expert feedback under a documented rubric; track agreement, false-pass, false-fail by
category (high average agreement is unacceptable if it falsely passes unauthorized actions or wrong
numbers).

## Trace-first observability

Every production request produces a trace linking: app request + authenticated user; agent &
prompt versions; supervisor routing; specialist calls; retrieval queries & doc IDs; SQL/function/
tool calls & sanitized args; model & endpoint; token/latency/cost; output & citations; feedback;
proposed action ID; Lakebase workflow ID; approval & external-execution correlation IDs.

Gotchas: full tracing can leak prompts/rows/outputs/args/credentials — redact and govern trace
access; sampling can miss rare failures — always retain errors, safety violations, live-action
attempts, flagged interactions; async tracing can drop telemetry on overflow/termination — monitor
queues; a trace is not the transactional action audit (correlate, don't conflate); a successful
trace doesn't prove the external action committed; avoid high-cardinality/sensitive values in
broadly searchable tags; standardize span names across specialists.

## Prompts, tools, retrieval

- **Prompts as governed artifacts** (MLflow Prompt Registry): immutable versions, diffing, tags in
  traces. A prompt change can alter tool behavior with no code change; prompt aliases are mutable
  (promotion controls like model aliases); rerun the full eval suite on any model migration.
  Prompt instructions are **not** security controls.
- **Tools** are small, typed, permission-aware capabilities — not escape hatches. Classes:
  Read / Explain / Compute / Simulate / Prepare / Approve / Execute / Verify. Validate every arg
  server-side (enums, ranges, business keys, effective dates, authz); bound & redact results;
  separate read from write; explicit retry semantics (writes need idempotency keys + verified
  status); typed outcomes for timeout/partial/stale/unavailable; apply policy before execution;
  record tool version. Never expose arbitrary SQL/Python/shell/HTTP/filesystem/secret tools to a
  production agent.
- **Retrieval/RAG** separates: retrieval correctness · context quality · response groundedness ·
  answer correctness · citation correctness. Enforce access control before results enter model
  context; cache keys include user/permission context + source version; **supply-chain facts often
  need structured SQL/metric tools, not vector search** — use Vector Search for narrative
  knowledge, governed SQL for quantitative truth; expose forecast vintage/grain/source
  deterministically rather than letting the model reconcile conflicting plan versions.

## Traditional ML — forecasting workflow

Define decision/target/grain/hierarchy/horizon/forecast-origin/delivery-time → preserve forecast
vintages & planning lags → establish seasonal-naive & other baselines → correct/flag
stockout-censored demand, one-time orders, promotions, substitutions, new products,
discontinuations → **time-based backtesting** (never random-split a time series) → evaluate at
operational grains AND rollups → measure statistical error AND business consequences → track
snapshot/code/params/env/metrics/artifacts/model/features in MLflow → validate the logged model in
isolation (`mlflow.models.predict()`) → register candidate, assign governed aliases after approval,
deploy batch or real-time per latency → log predictions & outcomes, monitor drift, define
retraining & rollback.

Evaluate: WAPE/WMAPE, MAE, RMSE, bias, service metrics; error by horizon & vintage; by
SKU-location/family/region/channel/planner; ABC/XYZ; stable/seasonal/intermittent/lumpy/new/EOL;
peak/promo/disruption/stockout; under- vs over-forecast cost; vs naive/statistical/planner/
consensus; interval coverage; runtime/freshness/cost/late-input behavior. Promotion is based on
segment gains, bias, service/inventory impact, stability, and whether planning can consume it —
not just aggregate WAPE.

**Gotchas:** logging ≠ registration ≠ approval ≠ deployment ≠ monitoring; metrics mislead if runs
use different windows/snapshots; leakage from revised actuals/future plan versions/shipment
outcomes/post-period attributes/features computed after forecast origin; forecast-vintage loss
invalidates backtesting; a global metric hides catastrophic performance on strategic items;
retraining every data point causes instability/cost; batch inference usually beats always-on
serving for scheduled planning cadence; design inference-table payloads/retention/permissions/cost;
change aliases through controlled approval.

## Production gates

- **Development:** interface/schema tests pass; tracing complete & redacted; representative eval
  set exists; deterministic scorers pass critical invariants; baseline comparison; human reviewers
  approve domain behavior.
- **Staging:** golden/regression/adversarial/action-safety suites pass; judges validated vs human
  labels; latency/token/model-call/tool-call/cost budgets pass; OBO/App identities & least-priv
  tested; network/endpoint failure tests; load/cancel/retry/duplicate-delivery tests; all versions
  pinned.
- **Production:** approval record identifies deployed versions + eval evidence; proven rollback;
  production traces/feedback/alerts/scheduled scorers enabled; safety-critical live actions retain
  all traces + transactional audits; canary/limited-user release for meaningful changes; **kill
  switch disables action execution independently of read-only analysis**; on-call ownership &
  incident classification defined.

## Unity AI Gateway

Centralized access control, routing, usage tracking, payload logging, guardrails. Gotchas:
guardrails don't prove factual correctness or action validity; payload logging may capture
sensitive data (configure access/retention); rate limits must account for supervisor fan-out +
eval traffic; evaluate every allowed fallback model; endpoint permission ≠ underlying UC/Lakebase/
external permissions; separate dev-eval quotas from prod traffic; track cost by app/use-case/user-
group/agent/env.

## Framework selection

Compare on: ResponsesAgent compatibility; native trace quality & span customization; streaming
semantics; typed tool support; state/checkpoint design; human-approval interrupts; multi-agent
routing; error/retry/timeout/cancellation; testability without live LLM calls; dependency/release
stability; deployment footprint & startup; security history & transitive deps; portability/
lock-in. Pure Python may be best for a small deterministic loop; the choice follows demonstrated
complexity, not architectural ambition.
