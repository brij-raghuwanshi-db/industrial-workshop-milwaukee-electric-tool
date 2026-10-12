# MLflow and Databricks AI Engineering Playbook for Supply Chain

## Executive position

All Milwaukee supply-chain AI work should use two related but distinct engineering systems:

1. **Traditional ML engineering** for forecasting, classification, ranking, anomaly detection, and optimization inputs.
2. **GenAI and agent engineering** for natural-language interaction, evidence retrieval, analysis, tool selection, recommendations, and supervised actions.

MLflow is the lifecycle backbone for both, but the artifacts, tests, evaluation methods, and production controls differ. Traditional models are primarily judged against observed outcomes using statistical and business metrics. Agents must also be judged on traces, retrieval, reasoning behavior, tool selection, tool arguments, groundedness, safety, action policy, latency, cost, and human acceptance.

For new custom Databricks agents, the preferred contract is MLflow `ResponsesAgent`, not the older `ChatModel` abstraction. `ResponsesAgent` is framework-agnostic, supports multi-turn and tool-calling outputs, streaming events, intermediate messages, and multi-agent scenarios, and integrates with MLflow logging, tracing, evaluation, serving, and OpenAI Responses API-compatible clients.[^1][^2][^3]

The governing rule is:

> No AI component is production-ready because it produced a convincing demonstration. It must have a versioned contract, representative evaluation dataset, deterministic tests, trace-based quality evaluation, human validation, identity and tool controls, deployment evidence, production monitoring, and a safe fallback.

## AI responsibility boundaries

| Component | Appropriate responsibility | Must not own by itself |
|---|---|---|
| Forecast model | Predict demand distribution or point forecast | Decide an operational writeback without policy |
| Classifier/ranker | Score exception type, urgency, or likely cause | Become the authoritative business rule without validation |
| Optimization model | Generate constrained alternatives | Invent missing constraints or execute directly |
| Genie Agent | Answer governed analytical questions | Unrestricted transactional writeback |
| Specialist Agent | Investigate one bounded domain | Broad enterprise authority |
| Supervisor Agent | Route/decompose work across bounded specialists and tools | Bypass specialist permissions or business approval |
| React UI | Present evidence and capture intent/approval | Enforce authorization by button state |
| FastAPI | Validate commands, identity, policy, and transactions | Replace authoritative ERP/WMS controls |
| Lakebase | Persist cases, state, approvals, and delivery status | Replace Delta analytical history |
| Unity AI Gateway | Govern model/agent access, traffic, and guardrails | Prove business correctness of the response |
| MLflow | Track, version, trace, evaluate, register, and monitor | Define Milwaukee business truth without domain owners |

## ResponsesAgent standard

### Why it fits

`mlflow.pyfunc.ResponsesAgent` is a specialized model interface for structured Agent responses and tool calling. It is a subclass of `PythonModel` and can wrap agents built with pure Python, OpenAI SDK, LangGraph, LangChain, or another framework.[^4][^2][^1]

The interface provides compatibility with Databricks AI features and uses `ResponsesAgentResponse` for non-streaming results and `ResponsesAgentStreamEvent` for streaming results. That makes it suitable as the stable deployment boundary even if the internal orchestration framework changes.[^2][^5]

### Implementation contract

Every custom Agent should define:

- Versioned input schema.
- Versioned output-item schema.
- Conversation and correlation identifiers.
- Structured tool-call and tool-result items.
- Typed error and refusal behavior.
- Streaming event contract.
- Trace tags for App version, Agent version, prompt version, environment, use case, business domain, and user role.
- Timeouts and token budgets.
- Cancellation behavior.
- Idempotency behavior for action tools.
- Safe handling of unknown or future message-item types.

### ResponsesAgent gotchas

- Wrapping an Agent in `ResponsesAgent` gives interface compatibility; it does not automatically make tools safe, traces useful, evaluation adequate, or deployment reproducible.
- The model signature and representative input example must cover realistic multi-turn and tool-call structures, not only a one-line question.
- Streaming and non-streaming paths require independent tests. A correct `predict()` implementation does not prove that partial events are ordered, resumable, or safely rendered.
- Intermediate tool messages may contain operationally sensitive information. Trace and response redaction policies must be deliberate.
- Do not assume older `ChatModel` tutorials represent the preferred current interface; MLflow 3 recommends `ResponsesAgent` for new work.[^3]
- Client, MLflow, Databricks Runtime, serving environment, and Agent-library versions must be pinned and compatibility-tested.
- OpenAI API compatibility is an interface advantage, not permission to bypass Unity AI Gateway, endpoint ACLs, payload policy, or Databricks authentication.

## Agent Server and App development

MLflow Agent Server supplies a FastAPI server with invocation and streaming registration, Responses API validation, tracing integration, and local reload support. It is useful for local development and contract testing, but the Milwaukee Databricks App may still need its own FastAPI backend-for-frontend for user identity, Lakebase transactions, supply-chain policies, action approval, and UI-specific APIs.[^6]

Choose the integration deliberately:

| Need | Preferred pattern |
|---|---|
| Isolated Agent development and serving contract | MLflow Agent Server |
| Databricks Model Serving deployment | Logged `ResponsesAgent` model |
| Rich Agentic App with writebacks | React + application FastAPI + Agent endpoint/client |
| Very low-latency in-process orchestration | In-process Agent only after scaling and dependency risks are accepted |
| Long-running asynchronous analysis | FastAPI starts a durable Job/work item and returns status ID |

Do not run heavy Spark computation, long model training, or fragile background loops in App web workers. A browser request should not remain open while a long supply-chain investigation or forecast training job executes.

## Supervisor and multi-agent design

A supervisor should be introduced only when routing or decomposition across genuinely distinct capabilities creates measurable value. Databricks Supervisor Agent can coordinate Genie Agents, Agent endpoints, Unity Catalog functions, MCP servers, and custom agents.[^7]

A plausible supply-chain topology is:

```text
Supply Chain Supervisor
  |-- Actual-vs-Plan Analyst
  |-- Demand Planning Specialist
  |-- Supply Exception Specialist
  |-- Inventory Specialist
  |-- Forecast Model Tool
  |-- Policy and Procedure Retriever
  |-- Scenario/Optimization Tool
  |-- Action Preparation Tool
```

Each specialist needs a bounded purpose, owned semantic model, approved tools, permission scope, evaluation set, and fallback. A supervisor is not automatically better than a single Agent with five well-designed tools.

### When not to use multi-agent

Avoid a supervisor architecture when:

- One Agent and a deterministic router can satisfy the use case.
- Specialist boundaries are labels over the same prompt and same data.
- Additional model calls materially increase latency and cost without improving task success.
- End-to-end failure diagnosis becomes difficult.
- Permissions cannot be scoped independently.
- The evaluation team cannot determine which component caused the error.
- The workflow contains deterministic steps better represented as code, SQL, state machines, or Jobs.

### Supervisor gotchas

- Evaluate routing accuracy separately from answer quality.
- Test whether the supervisor chooses the correct specialist, no specialist, or multiple specialists.
- Test delegation loops, repeated tool calls, context loss, contradictory specialists, partial failure, and timeout behavior.
- Apply least privilege independently. `CAN QUERY` or data access for the supervisor does not imply that every delegated Agent and function is correctly authorized.
- Databricks warns that arbitrary-code tools can expose sensitive data; only trusted code and explicit guardrails/permissions should be used.[^8]
- Do not expose a general-purpose Python or SQL execution tool to an action-capable Agent.
- A specialist’s natural-language answer must not be interpreted as an executable command. The supervisor must produce a typed proposal that a deterministic policy layer validates.
- End-to-end traces must preserve parent-child relationships across supervisor, specialist, retrieval, model, and action spans.

## Traditional ML lifecycle

MLflow for conventional ML covers experiment tracking, model evaluation, registry, deployment, and production lifecycle management. The Model Registry provides lineage, versions, aliases, tags, and annotations; aliases such as `champion` can represent the model selected for deployment rather than relying on mutable stage names.[^9][^10][^11]

### Forecasting workflow

For Milwaukee demand forecasting:

1. Define decision, target signal, grain, hierarchy, horizon, forecast origin, and acceptable delivery time.
2. Preserve forecast vintages and planning lags.
3. Establish seasonal-naive and other accepted baselines.
4. Correct or flag stockout-censored demand, one-time orders, promotions, substitutions, new products, and discontinuations.
5. Use time-based backtesting; never random-split a time series without a justified method.
6. Evaluate at operational grains and rollups.
7. Measure both statistical error and business consequences.
8. Track data snapshot, code, parameters, environment, metrics, artifacts, model, and feature definitions in MLflow.
9. Validate the logged model in an isolated environment before deployment; MLflow recommends local model validation through `mlflow.models.predict()`.[^12]
10. Register a candidate, assign governed aliases after approval, and deploy batch or real-time inference according to the business latency.
11. Log predictions and outcomes, monitor drift and performance, and define retraining and rollback.

### Forecast evaluation

The evaluation set should include:

- Overall WAPE/WMAPE, MAE, RMSE, bias, and service-relevant metrics.
- Error by forecast horizon and forecast vintage.
- SKU-location, family, region, channel, and planner segment.
- ABC/XYZ or equivalent volume/variability segments.
- Stable, seasonal, intermittent, lumpy, new-product, and end-of-life demand.
- Peak, promotion, disruption, and stockout periods.
- Under-forecast and over-forecast costs.
- Comparison with naive baseline, statistical incumbent, planner forecast, and consensus plan.
- Prediction-interval coverage where uncertainty is produced.
- Runtime, feature freshness, inference cost, and late/missing-input behavior.

A model is not automatically valuable because aggregate WAPE improved. Promotion should be based on segment-level gains, bias, service/inventory impact, stability, and whether the planning process can consume the prediction.

### Traditional ML gotchas

- Logging a model is not registration; registration is not approval; an alias is not deployment; deployment is not monitoring.
- Experiment metrics can be misleading if each run uses a different time window or data snapshot.
- Leakage can arise from revised actuals, future plan versions, shipment outcomes, post-period attributes, or features computed after forecast origin.
- Forecast-vintage loss makes historical backtesting invalid.
- A single global metric can hide catastrophic performance on constrained or strategic items.
- Retraining on every new data point may cause instability and cost without material benefit.
- Batch inference is usually preferable when forecasts are produced on a scheduled planning cadence; Model Serving is justified when interactive or event-driven inference is needed.
- Prediction logging and inference tables enable monitoring, but sensitive payloads, retention, table permissions, and cost must be designed.[^13]
- Model aliases must be changed through a controlled approval process; clients should not depend on an unversioned artifact path.
- Data pipelines, feature generation, training, evaluation, registration, deployment, and monitoring need separate retry/idempotency rules.

## GenAI evaluation system

GenAI evaluation should combine **deterministic scorers, LLM judges, domain-expert feedback, operational metrics, and end-to-end task outcomes**. No one evaluator is sufficient.

MLflow supports built-in judges, guidelines judges, custom judges, and code-based scorers. Built-in judges accelerate common checks; custom judges encode domain criteria; code scorers are best for exact, programmatic requirements.[^14]

### Evaluation layers

| Layer | Example | Preferred evaluator |
|---|---|---|
| Contract | Valid response/tool JSON | Code scorer |
| Retrieval | Required record/doc retrieved | Ground-truth/code + retrieval judge |
| Grounding | Claims supported by retrieved evidence | Retrieval-groundedness judge + citations check |
| Factuality | Values match trusted data | Deterministic SQL comparison |
| Calculation | Variance and KPI are correct | Code/SQL scorer |
| Tool choice | Correct tool selected | Expected-tool code scorer or trace judge |
| Tool arguments | Correct SKU, location, period, version | Schema and exact/partial-match scorer |
| Supervisor routing | Correct specialist used | Routing confusion matrix + trace judge |
| Completeness | Required causes, impacts, next steps included | Guidelines/custom judge |
| Action policy | No action without required approval | Deterministic trace/state scorer |
| Safety | No prohibited or harmful content | Safety judge + policy code checks |
| Security | No data or permission boundary bypass | Adversarial tests and authorization integration tests |
| User value | Planner accepts or acts successfully | Human feedback and operational outcome |
| Operations | Latency, tokens, cost, failures | Trace metrics and platform telemetry |

Correctness against known expected facts can use MLflow’s Correctness judge, but supply-chain quantities, dates, versions, and calculations should also be verified deterministically whenever authoritative data exists.[^15]

### Evaluation datasets

MLflow evaluation datasets can include labeled examples with ground truth and unlabeled examples for rubric-based assessment. They can be assembled from production traces, manually authored golden cases, and targeted edge cases.[^16][^17]

Maintain multiple suites:

- **Smoke:** tiny, fast, runs on every change.
- **Golden:** business-critical questions with expected facts, SQL, tools, arguments, and outcomes.
- **Regression:** every confirmed production failure becomes a durable test.
- **Adversarial:** prompt injection, unauthorized requests, data exfiltration, tool abuse, malformed inputs, and ambiguous commands.
- **Long-tail:** rare product/location/calendar/exception combinations.
- **Performance:** latency, throughput, tokens, model-call count, SQL calls, and cost.
- **Action safety:** prepare/approve/execute/verify, stale records, duplicate requests, rollback, and partial external-system failures.
- **Model change:** repeatable suite for changing foundation model, prompt, tool, retrieval index, or Agent framework.

Evaluation data must not contain production secrets or unrestricted sensitive data. Access controls, retention, redaction, representative sampling, and the distinction between training, tuning, judge alignment, and final holdout evaluation must be documented.

## LLM-as-judge discipline

LLM judges are useful for nuanced criteria that deterministic code cannot assess easily. They are not objective ground truth.

### Judge design

A strong custom judge should specify:

- Exact evaluation object: response, trace, retrieval, tool call, or full task.
- Business context and user role.
- Evidence the judge is allowed to use.
- Clear criteria and exclusions.
- Output type and allowed values.
- Anchored rubric for each score/category.
- Examples of passing, failing, and borderline behavior.
- Required rationale.
- Handling of missing context.
- Judge model and version.

MLflow custom judges can inspect inputs, outputs, expected results, or complete traces and return Boolean, categorical, or numerical assessments.[^18]

### Judge gotchas

- Judge scores can change when the judge model, prompt, temperature, or provider changes.
- A judge may favor verbose responses, its own model family, familiar phrasing, or answers similar to references.
- A plausible rationale does not prove the score is correct.
- If the judge sees the expected answer, it may judge textual similarity rather than task validity unless the rubric is careful.
- The same model should not be assumed to be an unbiased sole judge of its own output.
- Run repeated judgments or multiple judges for high-variance/high-impact criteria where justified.
- Track judge latency and cost; evaluation can cost more than generation.
- Never ask an LLM judge to verify arithmetic, SQL result equality, authorization, state transitions, or idempotency when code can verify them exactly.
- Preserve a final human-labeled holdout set that was not used to rewrite prompts or align the judge.
- Treat experimental judge-optimization features as experiments, not invisible production dependencies.[^19]

### Human alignment

MLflow supports aligning judges with human feedback. Alignment requires traces containing both judge assessments and human feedback under the same assessment name; domain experts should use a documented rubric.[^20][^21]

For Milwaukee:

- Demand planners judge usefulness, assumptions, forecast semantics, and proposed actions.
- Supply planners judge shortage reasoning, constraints, and feasibility.
- Data owners judge metric and source correctness.
- Security/platform owners judge permission and data-handling behavior.
- Application owners judge workflow and action integrity.

Track agreement, false-pass rate, false-fail rate, and disagreement by category. A judge with high average agreement may still be unacceptable if it falsely passes unauthorized actions or incorrect numerical claims.

## Trace-first observability

MLflow traces capture the execution path of GenAI applications and can be evaluated after collection. Every production Agent request should produce a trace that links:[^22]

- App request and authenticated user.
- Agent and prompt versions.
- Supervisor routing.
- Specialist calls.
- Retrieval queries and document identifiers.
- SQL/function/tool calls and sanitized arguments.
- Model name and endpoint.
- Token, latency, and cost metadata.
- Output and citations.
- Feedback.
- Proposed action ID.
- Lakebase workflow ID.
- Approval and external execution correlation IDs.

Production tracing should be asynchronous where possible to avoid request latency, use sampling for high-volume traffic, and support automated quality evaluation and user feedback.[^23]

### Tracing gotchas

- Full tracing can leak sensitive prompts, retrieved rows, model outputs, tool arguments, or credentials. Redact before logging and govern trace access.
- Sampling reduces cost but can miss rare failures; always retain errors, safety violations, live-action attempts, and explicitly flagged interactions where policy permits.
- Async tracing can drop telemetry when queues overflow or processes terminate; monitor queue and export failures.
- The trace cannot replace the transactional action audit. MLflow observability and Lakebase/ERP audit records must correlate but serve different responsibilities.
- A trace that ends successfully does not prove the external action committed or was verified.
- Avoid high-cardinality or sensitive values in tags that are broadly searchable.
- Trace schemas and span names should be standardized across specialists so evaluators remain stable.

## Prompts as governed artifacts

MLflow Prompt Registry versions and reuses prompts, provides immutable prompt versions, diffing, and integration with tracing and evaluation.[^24][^25]

Every important prompt should have:

- Purpose and owner.
- Input/output schema.
- Supported user roles and tasks.
- Domain definitions.
- Tool policy.
- Refusal and escalation behavior.
- Version/alias.
- Evaluation-suite result.
- Approved model families.
- Change record.

### Prompt gotchas

- A prompt embedded in source code but not tagged in traces is difficult to audit.
- Changing a prompt can alter tool behavior even when application code is unchanged.
- Prompt aliases are mutable and require promotion controls similar to model aliases.
- Model migration can invalidate previously successful prompts; rerun the full evaluation suite for every model or major endpoint change.
- Automatic prompt optimization is experimental and should not optimize against a weak or gameable judge.[^26]
- Prompt instructions are not security controls. Tool permissions, authorization, schemas, and state transitions remain deterministic.

## Retrieval and grounding

RAG evaluation must separate:

1. **Retrieval correctness:** Did the system retrieve the required records or documents?
2. **Context quality:** Is the context relevant, sufficient, current, and authorized?
3. **Response groundedness:** Are claims supported by the supplied context?
4. **Answer correctness:** Does the final result match authoritative facts?
5. **Citation correctness:** Do references support the specific claims?

### Retrieval gotchas

- A grounded answer can still be wrong if the retrieved source is outdated or not authoritative.
- High retrieval relevance does not prove completeness.
- Chunking can separate definitions from exceptions, effective dates, or unit-of-measure context.
- Access control must be enforced before retrieval results enter the model context.
- Cache keys must include user/permission context and source version.
- Supply-chain facts often require structured SQL, not vector search. Use Vector Search for narrative knowledge and governed SQL/metric tools for quantitative truth.
- Do not let the model reconcile conflicting plan versions implicitly. A deterministic tool should select or expose forecast vintage, grain, and source.
- Index refresh lag and deleted documents need explicit monitoring.

## Tool engineering

Tools should be small, typed, permission-aware capabilities rather than broad escape hatches.

### Tool classes

| Tool class | Example | Default safety |
|---|---|---|
| Read | Get Actual vs Plan for SKU/location/week | Governed, bounded, parameterized |
| Explain | Retrieve KPI definition or procedure | Authorized retrieval with citations |
| Compute | Calculate deterministic variance | Code/SQL with exact tests |
| Simulate | Compare replenishment scenarios | Versioned assumptions, no write |
| Prepare | Create transfer proposal | Lakebase draft only |
| Approve | Approve action | User identity and role required |
| Execute | Call ERP/WMS API | Dedicated service principal, idempotent |
| Verify | Read back action result | Separate confirmation and reconciliation |

### Tool gotchas

- Tool names and descriptions influence selection; evaluate description changes like prompt changes.
- Validate every argument server-side with enums, ranges, business keys, effective dates, and authorization.
- Bound result size and redact unnecessary fields before returning tool output to the model.
- Separate read and write tools; never overload a read-looking function with side effects.
- Make retry semantics explicit. Read calls may be retryable; writes require idempotency keys and verified status.
- Timeouts, partial results, stale data, and source unavailability need typed outcomes the Agent can explain.
- Do not expose arbitrary SQL, Python, shell, HTTP, filesystem, or secret-reading tools to a production Agent.
- Apply policy before execution, not after observing the tool result.
- Record tool version because a changed implementation can alter Agent behavior without a model or prompt change.

## Production evaluation gates

### Development gate

- Interface and schema tests pass.
- Tracing is complete and redacted.
- Representative evaluation dataset exists.
- Deterministic scorers pass critical invariants.
- Baseline model/Agent comparison is available.
- Human reviewers approve domain behavior.

### Staging gate

- Full golden, regression, adversarial, and action-safety suites pass.
- LLM judges are validated against human labels.
- Latency, token, model-call, tool-call, and cost budgets pass.
- OBO/App identities and least-privilege grants are tested.
- Network and endpoint failure tests pass.
- Load, cancellation, retry, and duplicate-delivery tests pass.
- Model, Agent, prompt, tools, retrieval index, and dependencies are pinned.

### Production gate

- Approval record identifies deployed versions and evaluation evidence.
- Rollback target and procedure are proven.
- Production traces, feedback, alerts, and scheduled scorers are enabled.
- Safety-critical live actions retain all traces and transactional audits.
- Canary or limited-user release is used for meaningful changes.
- Kill switch disables action execution independently of read-only analysis.
- On-call ownership and incident classification are defined.

## Monitoring framework

Monitor three levels:

| Level | Measures |
|---|---|
| Platform | Endpoint health, 4xx/5xx, availability, throughput, queueing |
| AI system | Latency, tokens, cost, routing, retrieval, tool errors, refusal, judge scores |
| Business | Planner acceptance, action completion, exception resolution, service/inventory outcome |

MLflow can evaluate production traces, attach feedback, and configure scheduled scorers for automated monitoring. Model Serving inference tables and Databricks monitoring capabilities can support request/response analysis and drift/custom-metric dashboards.[^27][^24][^22][^13]

### Alert priorities

- Unauthorized or cross-user data exposure.
- Live action without valid approval.
- Duplicate or unverifiable external action.
- Incorrect authoritative quantity/date/version.
- Prompt injection reaching a privileged tool.
- Sudden decline in groundedness, correctness, routing, or tool success.
- Judge/human disagreement increase.
- Retrieval/index staleness.
- Latency or cost regression.
- Forecast bias or accuracy deterioration by strategic segment.

## Unity AI Gateway role

Unity AI Gateway provides centralized access control, routing, usage tracking, payload logging, security controls, and service policies/guardrails for models and Agents.[^28][^7]

### Gateway gotchas

- Gateway guardrails do not prove supply-chain factual correctness or action validity.
- Payload logging may capture sensitive operational data; configure access and retention intentionally.
- Rate limits must account for supervisor fan-out and evaluation traffic, not only end-user requests.
- Fallback routing can change model behavior; evaluate every allowed fallback model.
- A model endpoint permission does not grant underlying Unity Catalog, Lakebase, or external-system permissions.
- Separate development evaluation quotas from production user traffic where possible.
- Track cost by App, use case, user group, Agent, and environment.

## Framework-selection policy

No Agent framework should be adopted because it is fashionable. Compare:

- Compatibility with `ResponsesAgent`.
- Native trace quality and ability to customize spans.
- Streaming semantics.
- Typed tool support.
- State and checkpoint design.
- Human-approval interrupts.
- Multi-agent routing.
- Error, retry, timeout, and cancellation behavior.
- Testability without live LLM calls.
- Dependency and release stability.
- Deployment footprint and startup time.
- Security history and transitive dependencies.
- Portability and lock-in.

Pure Python may be best for a small deterministic loop. LangGraph or another orchestration framework may fit explicit stateful graphs. A managed Supervisor Agent may fit governed cross-Agent routing. The choice must follow complexity demonstrated by evaluation and operations—not architectural ambition.

## AI gotcha register

Every AI component should maintain a versioned register with:

| Field | Meaning |
|---|---|
| Component | Model, prompt, Agent, judge, tool, index, endpoint |
| Status | Proposed, validated, accepted risk, blocked, retired |
| Limitation | Specific behavior or product/framework constraint |
| Trigger | Conditions that expose the issue |
| Impact | Accuracy, security, latency, cost, action safety |
| Detection | Test, scorer, alert, or operational signal |
| Mitigation | Design or runbook response |
| Owner | Responsible engineering/business role |
| Evidence | Trace, evaluation run, test, incident, documentation |
| Revalidation | Version or date that requires retesting |

Minimum gotcha categories include:

- API/interface migration.
- Preview/Beta/experimental features.
- Model and provider behavior changes.
- Prompt and tool-description sensitivity.
- Judge variability and bias.
- Retrieval freshness and authorization.
- Trace privacy and sampling.
- App/endpoint identity and permissions.
- Dependency and build compatibility.
- Streaming, timeout, and cancellation.
- Supervisor loops and fan-out cost.
- Lakebase transaction and external action consistency.
- Evaluation-data contamination.
- Human feedback quality and reviewer disagreement.
- Rollback, kill switch, and incident recovery.

## Default project contract

For future Milwaukee AI work, the default delivery must include:

1. Traditional-ML versus GenAI responsibility decision.
2. Single-Agent versus supervisor/multi-agent decision.
3. `ResponsesAgent` interface and streaming contract for custom Agents.
4. Versioned model, prompt, tool, retrieval, and Agent artifacts.
5. MLflow traces in development, staging, and production.
6. Evaluation datasets covering golden, regression, adversarial, long-tail, performance, and action-safety cases.
7. Deterministic code/SQL scorers wherever truth is computable.
8. Built-in and custom LLM judges only where nuanced judgment is needed.
9. Human-domain-expert labeling and judge-alignment evidence.
10. Correctness, groundedness, retrieval, routing, tool-choice, tool-argument, policy, safety, latency, and cost metrics.
11. Forecast backtesting, baselines, bias, hierarchy, horizon, and business-impact evaluation for ML.
12. App, endpoint, Unity Catalog, Lakebase, and external-action identity/permission matrix.
13. Unity AI Gateway policy and usage monitoring.
14. Production scheduled scoring, feedback, drift, and outcome monitoring.
15. Canary, rollback, action kill switch, and incident runbook.
16. A maintained gotcha register for every product, library, model, prompt, judge, and tool.

The goal is not to use every MLflow feature. The goal is to create a measurable, reproducible, governed AI system in which a forecasting model, Agent response, supervisor route, recommendation, approval, and live action can each be tested and explained independently.

---

## References

1. [ResponsesAgent for Model Serving | MLflow AI Platform](https://mlflow.org/docs/latest/genai/serving/responses-agent/) - Use MLflow ResponsesAgent to serve generative AI models with tool calling, multi-turn dialogue, and ...

2. [ResponsesAgent Introduction | MLflow AI Platform](https://mlflow.org/docs/latest/genai/flavors/responses-agent-intro/) - ResponsesAgent is a subclass of PythonModel that provides a framework-agnostic way to create an agen...

3. [Tutorial: Custom LLM and AI Agent Models using ChatModel](https://mlflow.org/docs/latest/genai/flavors/chat-model-guide/) - Starting in MLflow 3.0.0, we recommend ResponsesAgent instead of ChatModel . See more details in the...

4. [Get started with agents | Databricks on Google Cloud](https://docs.databricks.com/gcp/en/agents/tutorials/agent-quickstart) - You can author agents using any framework. The key is wrapping your agent with MLflow ResponsesAgent...

5. [mlflow.types](https://mlflow.org/docs/latest/python_api/mlflow.types.html) - The mlflow.types module defines data types and utilities. Response object for ResponsesAgent. A sing...

6. [MLflow Agent Server](https://mlflow.org/docs/latest/genai/serving/agent-server/) - In this example, we'll use the openai-agents-sdk to define our Responses API compatible agent. See t...

7. [Build agents on Databricks](https://docs.databricks.com/aws/en/agents/) - - Build and deploy interactive UIs for your agents, such as chat apps and data entry forms.

8. [Use Supervisor Agent to create a coordinated multi ...](https://docs.databricks.com/aws/en/agents/agent-bricks/multi-agent-supervisor) - This page describes how to use Supervisor Agent to create a multi-agent supervisor system that orche...

9. [Model Registry Workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow/) - This guide walks you through using the MLflow Model Registry via both the UI and API. Learn how to r...

10. [ML Model Registry | MLflow AI Platform](https://mlflow.org/docs/latest/ml/model-registry/) - The MLflow Model Registry is a centralized model store, set of APIs and a UI designed to collaborati...

11. [ML for Traditional Machine Learning](https://mlflow.org/docs/latest/ml/traditional-ml/) - MLflow for ML Models provides comprehensive experiment tracking, model management, and deployment ca...

12. [ML Models | MLflow AI Platform](https://mlflow.org/docs/latest/ml/model/) - This file contains the name and version of the model referenced in the MLflow Model Registry, and wi...

13. [Databricks data science and ML capabilities](https://docs.databricks.com/gcp/en/machine-learning/concepts/ml-capabilities) - Databricks provides flexible evaluation for training and continuous monitoring for production. Real-...

14. [LLM Judges and Scorers](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/) - Learn about MLflow LLM judges and scorers for evaluating GenAI applications, including built-in judg...

15. [Correctness Judge | MLflow AI Platform](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/response-quality/correctness/) - The Correctness judge assesses whether your LLM application or AI agent's response is factually corr...

16. [Building Agent & LLM Evaluation Datasets](https://mlflow.org/docs/latest/genai/datasets/) - Create labeled and unlabeled evaluation datasets to systematically test and improve your agent and L...

17. [LLM and Agent Evaluation | MLflow AI Platform](https://mlflow.org/docs/latest/genai/eval-monitor/) - Evaluation Datasets provide a centralized repository for managing test cases, ground truth expectati...

18. [Custom Judges | MLflow AI Platform](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/custom-judges/) - Create custom LLM judges in MLflow with natural language guidelines using make_judge() or the Judge ...

19. [MemAlign Optimizer (Experimental) | MLflow AI Platform](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/memalign/) - MemAlign is an experimental optimizer that uses a dual-memory system inspired by human cognition to ...

20. [Judge Alignment: Teaching AI to Match Human Preferences](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/alignment/) - Judge alignment is the process of refining LLM judges to match human evaluation standards. Through s...

21. [End-to-End Judge Workflow](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/workflow/) - End-to-End Judge Workflow. This guide walks through the complete lifecycle of developing and optimiz...

22. [Evaluating (Production) Traces | MLflow AI Platform](https://mlflow.org/docs/latest/genai/eval-monitor/running-evaluation/traces/) - Evaluating traces is a powerful way to understand the performance of your LLM applications and get i...

23. [Production Tracing and Monitoring | MLflow AI Platform](https://mlflow.org/docs/latest/genai/tracing/prod-tracing/) - This guide covers how to configure MLflow Tracing for production environments—including automatic (o...

24. [mlflow.genai](https://mlflow.org/docs/latest/python_api/mlflow.genai.html) - A scheduled scorer configuration for automated monitoring of generative AI applications. Scheduled s...

25. [Prompt Registry | MLflow AI Platform](https://mlflow.org/docs/latest/genai/prompt-registry/) - It enables you to version, track, and reuse prompts across your organization, helping maintain consi...

26. [Auto-rewrite Prompts for New Models (Experimental)](https://mlflow.org/docs/latest/genai/prompt-registry/rewrite-prompts/) - API helps you automatically rewrite prompts to maintain output quality when switching models, using ...

27. [Enable measurement: Supporting infrastructure](https://docs.databricks.com/gcp/en/agents/tutorials/ai-cookbook/evaluate-enable-measurement) - Production traces are logged as part of the Inference Table. ... In Databricks, Agent Evaluation pro...

28. [AI governance with Unity AI Gateway | Databricks on AWS](https://docs.databricks.com/aws/en/ai-gateway/) - Unity AI Gateway governs enterprise AI on Databricks: control access to model APIs and external prov...

