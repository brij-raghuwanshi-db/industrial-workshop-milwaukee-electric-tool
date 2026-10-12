# AI / Quick Decision-Making: Turning Data into Trustworthy Decisions

## Executive Summary

Even with a mature medallion + semantic layer (01_medallion_foundation.md), a planner asking "which low-stock items need action this week?" requires 15+ SQL queries, joins across 3+ tables, context-switching between tools, and manual interpretation of results. Milwaukee's AI strategy turns **certified metric views → Genie Agents + AI Functions + Evaluation + Lakebase Search** into a decision-making stack where:

1. **Planners ask in English** (Genie Agent) → certified SQL runs immediately → ranked answer + evidence in <5 seconds
2. **Root-cause hypotheses** (AI Functions: classify, extract, summarize) → enriched exception cases with context
3. **Similar-case lookup** (Lakebase Search BM25) → retrieve historical incidents, notes, policy matches inline
4. **Forecast baseline** (AI Functions: ai_forecast) → quick "what-if" without retraining
5. **Reliability gates** (MLflow evaluation) → catches drift, prevents a bad agent recommendation from becoming a PO

**Critical Rule**: LLM EXPLAINS and COORDINATES reliable tools. It does NOT replace math, constraints, permissions, or deterministic rules. Variance = SQL; safety-stock = deterministic; PO feasibility = typed approval; forecast = ML-assisted; root-cause = hybrid retrieval + grounding.

---

## 1. Deterministic vs. AI: Our Real Examples

This section is **foundational**. It separates what an LLM must never decide from what it should coordinate.

### The $0.0134 Carbide Illusion

**The Pain**: A planner saw "17.6M-unit breach" in the top-10 exceptions list and escalated. Investigation: a low-cost carbide part. Cost-weighted ABC priority would have ranked it ~#2,847 for action. An LLM that says "here are the top 10 by quantity" would repeat this mistake daily.

**Deterministic Rule** (NEVER AI): Priority scoring = ABC classification × lead-time-risk × forecast-error, weighted by your known domain trade-offs. This goes in SQL as a computed column on `gold_supply_exceptions`:

```sql
-- Deterministic priority in Gold, not an LLM guess
ALTER TABLE sandbox_operations.gold_supply_exceptions ADD COLUMN
  priority_score AS (
    CASE abc_category
      WHEN 'A' THEN 100
      WHEN 'B' THEN 50
      WHEN 'C' THEN 10
    END
    * (1.0 + GREATEST(0, forecast_error_pct / 100.0))  -- Amplify if forecast is bad
    * (CASE WHEN lead_time_days > 30 THEN 2.0 ELSE 1.0 END)
  );
```

**AI Role**: Genie Agent reads this column and ranks by it. LLM explains why case #47 is #3 (high value + slow supplier + risky forecast). No LLM invents thresholds.

### The Frozen-Zone Policy

**The Pain**: A supplier has a 2-week frozen window before order cutoff. Orders within 7 days of cutoff are locked; no quantity increases allowed. A planner submitted a PO +50-unit increase with 5 days to cutoff—caught by humans, rejected. Downstream, it would have caused rework.

**Deterministic Rule** (NEVER AI): Frozen-zone rules are coded as validation gates:

```sql
-- Deterministic freeze logic in a UC function, not an LLM check
CREATE OR REPLACE FUNCTION sandbox_operations.check_po_feasibility(
  po_number STRING,
  requested_qty_delta INT,
  supplier_id STRING,
  cutoff_date DATE
)
RETURNS STRUCT<is_feasible BOOLEAN, reason STRING>
LANGUAGE SQL
AS $$
  SELECT
    CASE
      WHEN DATEDIFF(CURRENT_DATE, cutoff_date) <= 7 THEN
        (FALSE, 'Within frozen zone: no qty changes after cutoff - 7 days')
      WHEN requested_qty_delta < 0 THEN
        (TRUE, 'Qty decrease always allowed')
      WHEN (SELECT lead_time_days FROM sandbox_operations.gold_supplier_master WHERE id = supplier_id) > 14 THEN
        (FALSE, 'Long lead-time supplier: frozen after -14 days')
      ELSE
        (TRUE, 'Qty increase feasible')
    END
$$;
```

**AI Role**: Genie Agent calls this function as a guardrail. It tells the user "frozen: reason X". No LLM overrides the function.

### The MOQ Constraint

**The Pain**: Milwaukee has minimum order quantities (MOQ) for each supplier×item pair (e.g., 500-unit MOQ on a specialty bolt). An LLM suggesting a 300-unit order looks plausible but is infeasible. Purchasing has to rework it.

**Deterministic Rule** (NEVER AI):

```sql
-- Deterministic MOQ in UC function
CREATE OR REPLACE FUNCTION sandbox_operations.get_moq_for_item(
  item_id STRING,
  supplier_id STRING
)
RETURNS INT
LANGUAGE SQL
AS $$
  SELECT COALESCE(
    (SELECT moq_qty FROM sandbox_operations.gold_supplier_item_master
     WHERE item_id = $1 AND supplier_id = $2),
    1  -- Default MOQ = 1 if not configured
  )
$$;
```

**AI Role**: If a Genie Agent is composing a PO recommendation, it calls this function and reports back: "Recommended quantity: 500 (minimum order quantity for this supplier)." The constraint is **enforced** before the LLM even formulates the suggestion.

### Forecast Baseline (ML-Assisted, Not ML-Decided)

**The Pattern**: A planner sees a demand forecast for a new product line (low history, high variance). They ask Genie: "What should we stock for Tier 2 demand assuming 80% service level?"

**AI Role (Deterministic)**: SQL computes the service-level stock-out probability given the forecast distribution:

```sql
-- Deterministic service-level calculation from forecast + std_dev
CREATE OR REPLACE FUNCTION sandbox_operations.safety_stock_for_service_level(
  forecast_qty INT,
  forecast_std_dev DOUBLE,
  service_level DOUBLE  -- 0.80 = 80%
)
RETURNS INT
LANGUAGE SQL
AS $$
  SELECT CAST(
    forecast_qty + (z_score_for_service_level(service_level) * forecast_std_dev)
    AS INT
  )
$$;
```

**AI Role (ML-Assisted)**: `ai_forecast` is called to generate an initial baseline forecast + confidence intervals. Then the above function computes safety stock deterministically:

```sql
SELECT
  item_id,
  (SELECT response FROM ai_forecast(
    TABLE(SELECT date, demand FROM prod_edw.demand_history WHERE item_id = $1),
    horizon => DATE_ADD(CURRENT_DATE, 90),
    prediction_interval_width => 0.8
  )) AS forecast_baseline,
  sandbox_operations.safety_stock_for_service_level(
    (forecast_baseline.forecast_qty),
    (forecast_baseline.upper - forecast_baseline.lower) / (2 * 1.96),  -- Approx std_dev
    0.80
  ) AS recommended_safety_stock
FROM ...;
```

**No AI overrides the safety-stock formula.** If the forecast is bad, the interval widens, safety stock increases. Deterministic.

---

## 2. Genie Agents: The Cure for Search Pain

**The Problem**: Planners face 15+ known grain traps, semi-additivity errors, and key mismatches when querying raw data. Every user re-pays the cost weekly. A planner asking "top 10 low-stock items" in SQL must know:
- Which table has on-hand? (silver_on_hand_weekly, not prod_edw fact)
- How to join item master without duplicating rows? (SCD2 dedup rules)
- What time-window context? (last 12 weeks to avoid single-snapshot blindness)
- How to weight by cost? (ABC category from gold_actuals_weekly_summary)

**The Cure**: **One focused Genie Agent per priority**, curated on certified Metric Views + Gold tables, with sample questions + instructions that bake in the domain knowledge.

### Four Genie Agents (P1–P4)

| Priority | Agent Name | Queries | Backed By | Domain Knowledge |
|----------|------------|---------|-----------|------------------|
| **P1 Actuals** | Ask Actuals | Top items by received qty, cost, ABC; trends; on-time performance | `supply_metrics` (Metric View) + `gold_actuals_weekly_summary` | Weekly received quantities always point-in-time; cost always included; ABC ranks all items |
| **P2 Supply Exceptions** | Ask Exceptions | Low-stock items (WOC < 2), overstock (WOC > 26), late POs | `gold_supply_exceptions` + `gold_supplier_master` | Exception history retained; filtered by status (open/resolved); frozen-zone policy embedded in reason text |
| **P3 Demand Events** | Ask Demand | Forecast vs actual, demand spikes, plan changes | `gold_demand_events` + `gold_forecast_baseline` | Forecast includes confidence interval; spikes trigger event records; plan version history |
| **P4 Demand Exceptions** | Ask Demand Exceptions | Demand > forecast, demand < forecast (demand-side shortfalls) | `gold_demand_exceptions` + P3 tables | Root-cause classification (seasonal, supply-chain event, demand shift); suggestions grounded in historical analogs |

### Example: Ask Exceptions Agent (P2)

**Configured On**: Certified Metric View + Gold Table

```yaml
# genie_space_ask_exceptions.json
version: 2
config:
  sample_questions:
    - id: "10000000000000000000000000000001"
      question: ["What are the top 10 low-stock items that need action this week?"]
    - id: "10000000000000000000000000000002"
      question: ["Which items in the A category are below 2 weeks of cover?"]
    - id: "10000000000000000000000000000003"
      question: ["Show me items with late POs in the last 3 weeks"]
    - id: "10000000000000000000000000000004"
      question: ["Which overstock items (WOC > 26) can we reduce?"]
    - id: "10000000000000000000000000000005"
      question: ["What's the total at-risk value for low-stock exceptions?"]

data_sources:
  tables:
    - identifier: "sandbox_operations.gold_supply_exceptions"
    - identifier: "sandbox_operations.gold_supplier_master"
    - identifier: "sandbox_operations.supply_metrics"  # Metric View

instructions:
  example_question_sqls:
    - id: "20000000000000000000000000000001"
      question: ["Top 10 low-stock items by at-risk value"]
      sql:
        - "SELECT\n"
        - "  item_code,\n"
        - "  organization_id,\n"
        - "  on_hand_qty,\n"
        - "  weeks_of_cover,\n"
        - "  on_hand_qty * standard_cost AS at_risk_value,\n"
        - "  exception_type\n"
        - "FROM sandbox_operations.gold_supply_exceptions\n"
        - "WHERE exception_type = 'low_stock'\n"
        - "  AND week_end_date = CURRENT_DATE - INTERVAL 1 WEEK\n"
        - "ORDER BY at_risk_value DESC\n"
        - "LIMIT 10"

    - id: "20000000000000000000000000000002"
      question: ["Items with late POs (ordered > 14 days ago, not yet received)"]
      sql:
        - "SELECT\n"
        - "  po_number,\n"
        - "  item_code,\n"
        - "  quantity_ordered,\n"
        - "  DATEDIFF(CURRENT_DATE, order_date) AS days_outstanding,\n"
        - "  supplier_name,\n"
        - "  reason  -- Reason from the late_po_flag table\n"
        - "FROM sandbox_operations.gold_supply_exceptions\n"
        - "WHERE exception_type = 'late_po'\n"
        - "  AND DATEDIFF(CURRENT_DATE, order_date) > 14\n"
        - "  AND received_date IS NULL\n"
        - "ORDER BY days_outstanding DESC"

  text_instructions:
    - id: "30000000000000000000000000000001"
      content:
        - "Supply exceptions data is curated from gold_supply_exceptions and gold_supplier_master.\n"
        - "low_stock exception: weeks_of_cover < 2 for the item at end-of-week snapshot.\n"
        - "overstock exception: weeks_of_cover > 26.\n"
        - "late_po exception: PO ordered > 14 days ago, not yet received. Check supplier lead_time to assess urgency.\n"
        - "frozen_zone_flag: TRUE if within 7 days of supplier cutoff. If frozen, quantity increases NOT allowed (deterministic check in PO submission).\n"
        - "When asked about 'action needed': Filter to low_stock + NOT frozen_zone_flag + abc_category IN ('A', 'B'). Sort by at_risk_value DESC.\n"
        - "When asked about 'overstock': Filter to overstock exception. Highlight suppliers with cost-reduction opportunities (long lead-time or high-margin suppliers benefit from lower working capital).\n"
        - "All on_hand_qty and weeks_of_cover are point-in-time snapshots at week-end (Monday). Do NOT sum across weeks; instead, show trend by week.\n"

  benchmarks:
    - id: "40000000000000000000000000000001"
      question: ["How many low-stock items are there now?"]
      response: ["15 low-stock items (weeks of cover < 2) as of the latest week. Top 3 at-risk: Item A ($42.5K), Item B ($18.3K), Item C ($11.7K)."]
```

**Deploy**:

```bash
# 1. Create the agent
databricks workspace mkdirs /Users/me@example.com/ask_exceptions_agent
databricks genie create-space --json '{
  "warehouse_id": "sql-warehouse-prod",
  "title": "Ask Exceptions",
  "description": "Natural language Q&A over supply exceptions (P2 priority)",
  "parent_path": "/Users/me@example.com/ask_exceptions_agent",
  "serialized_space": '"$(cat genie_space_ask_exceptions.json | jq -c . | jq -Rs .)"'
}'

# 2. Test a query
databricks genie start-conversation --no-wait SPACE_ID "Top 10 low-stock items by cost?"
```

**Why This Works**:
- **Certified tables**: gold_supply_exceptions is SDP-governed, Expectations-gated, lineage-traced
- **Metric Views**: supply_metrics enforces additivity; users can't misgroup
- **Sample Q&A**: Genie learns intent from examples (low-stock, late PO, overstock patterns)
- **Text instructions**: Domain rules embedded (frozen-zone policy, MOQ checks, ABC thresholds)
- **Result**: Planner asks → SQL runs → ranked answer + evidence in <5 seconds, no grain traps possible

---

## 3. AI Functions: Batch Intelligence in SQL

**Use Case**: Classify exception root-cause from movement ledger + comments; summarize a planner's queue; extract supplier lead-time from unstructured notes; quick forecast baseline.

### Pattern: Classify Root-Cause

**Data**: `sandbox_operations.gold_supply_exceptions` has columns:
- `exception_reason` (free text: "PO delayed by customs", "Supplier quality hold", "Demand spike")
- `notes` (planner comments)
- `movement_history` (receipts, transfers, adjustments in the past 4 weeks)

**Deterministic Classifier** (batch, once per exception):

```sql
-- Enrich exceptions with LLM-assisted root-cause classification
CREATE OR REPLACE TABLE sandbox_operations.supply_exceptions_classified AS
SELECT
  exception_id,
  item_id,
  on_hand_qty,
  exception_reason,
  -- AI function: classify into one of 5 root-cause categories
  ai_classify(
    CONCAT(exception_reason, '\n', COALESCE(notes, ''), '\n', movement_history),
    '["supplier_delay", "demand_spike", "quality_hold", "forecast_miss", "system_error"]',
    MAP('version', '2.0')
  ):response[0]::STRING AS root_cause_class,
  
  -- Store the full response for debugging
  ai_classify(...):response AS classification_metadata,
  
  CURRENT_TIMESTAMP() AS classified_at
FROM sandbox_operations.gold_supply_exceptions
WHERE classified_at IS NULL  -- Idempotent: only classify new exceptions
;
```

**Result**: Exceptions are classified, then a deterministic rule routes them:

```sql
-- Deterministic routing (NOT AI)
SELECT
  item_id,
  root_cause_class,
  CASE root_cause_class
    WHEN 'supplier_delay' THEN 'Contact supplier; check lead time vs plan'
    WHEN 'demand_spike' THEN 'Escalate to sales; consider expedite'
    WHEN 'quality_hold' THEN 'Work with quality team on release timeline'
    WHEN 'forecast_miss' THEN 'Replan next 4 weeks; adjust forecast'
    ELSE 'Investigate manually'
  END AS next_action
FROM sandbox_operations.supply_exceptions_classified
WHERE root_cause_class IS NOT NULL
;
```

**Why**: LLM extracts signal (root-cause hypothesis) from messy text. Deterministic rules turn hypothesis into action.

### Pattern: Quick Forecast Baseline

**Use**: Planner asks "quick forecast for next 90 days" without waiting for a retraining job.

```sql
-- ai_forecast: baseline forecast with confidence interval
SELECT * FROM ai_forecast(
  observed => TABLE(
    SELECT date, demand_qty FROM sandbox_operations.gold_demand_history
    WHERE item_id = 'ITEM-ABC'
      AND date >= DATE_SUB(CURRENT_DATE, 365)  -- Last year of history
  ),
  horizon => '2026-12-31',
  time_col => 'date',
  value_col => 'demand_qty',
  prediction_interval_width => 0.8  -- 80% confidence
)
;
```

**Output**:
```
| date       | demand_forecast | lower_bound | upper_bound |
|------------|-----------------|-------------|-------------|
| 2026-09-07 | 450             | 380         | 520         |
| 2026-09-14 | 480             | 390         | 570         |
| 2026-09-21 | 460             | 370         | 550         |
```

**Feed into Safety Stock**:

```sql
SELECT
  item_id,
  (SELECT MAX(demand_forecast) FROM above) AS avg_weekly_demand,
  (SELECT (MAX(upper_bound) - MIN(lower_bound)) / (2 * 1.96) FROM above) AS demand_std_dev,
  sandbox_operations.safety_stock_for_service_level(
    (SELECT MAX(demand_forecast) FROM above),
    (SELECT (MAX(upper_bound) - MIN(lower_bound)) / (2 * 1.96) FROM above),
    0.85  -- 85% service level
  ) AS safety_stock_85pct
;
```

**Cost**: <1 second per item. Lightweight. No retraining required.

### Pattern: Summarize Planner Queue

**Use**: A planner says "summarize my action queue from last week."

```sql
-- Batch summarize planner's recent actions (free-form summary + highlights)
CREATE OR REPLACE TABLE sandbox_operations.planner_action_queue_summary AS
SELECT
  planner_id,
  week_end_date,
  COUNT(*) AS action_count,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
  -- AI function: summarize all notes in one pass
  ai_summarize(
    CONCAT_WS('\n', COLLECT_LIST(action_note)),
    max_words => 100
  ) AS week_summary,
  -- Extract key metrics
  SUM(po_quantity) AS total_po_qty,
  SUM(po_value) AS total_po_value
FROM sandbox_operations.po_action_log
WHERE week_end_date >= DATE_SUB(CURRENT_DATE, 7)
GROUP BY planner_id, week_end_date
;
```

**Why**: The summary is brief, highlights what was done, no hand-writing of status reports.

---

## 4. Agent Bricks: Knowledge Assistant + Supervisor (Optional Coordinator)

**When to Use**: After Genie Agents are deployed and stable, if a single unified interface is desired.

### Knowledge Assistant: Policy & SOP Docs

**Use Case**: A planner asks "What's the frozen-zone policy?" instead of searching Confluence.

1. **Upload SOP docs to a UC Volume**:

```bash
databricks workspace mkdirs /Workspace/Volumes/sandbox_operations/docs
# Upload PDFS: frozen_zone_policy.pdf, supplier_terms.pdf, ABC_classification_rules.pdf
```

2. **Create Knowledge Assistant**:

```bash
databricks knowledge-assistants create-knowledge-assistant "MKE Supply Chain Ops" "Policies and standard operating procedures"

# Add knowledge source (docs from Volume)
databricks knowledge-assistants create-knowledge-source \
  "knowledge-assistants/{ka_id}" \
  --json '{
    "display_name": "SOP Docs",
    "description": "Frozen-zone, MOQ, lead-time policies",
    "source_type": "files",
    "files": {"path": "/Volumes/sandbox_operations/docs/"}
  }'

# Sync
databricks knowledge-assistants sync-knowledge-sources "knowledge-assistants/{ka_id}"
```

3. **Query via Conversation API**:

```bash
databricks knowledge-assistants start-conversation --no-wait \
  "knowledge-assistants/{ka_id}" \
  "What suppliers are in frozen-zone starting tomorrow?"
```

**Output**: Policy excerpt + answer, grounded in uploaded docs.

### Supervisor Agent: Route Across Genie Agents (Optional, Project Prefers Focused Agents)

**Pattern** (if unified assistant is desired later):

```bash
# Create supervisor agent
databricks supervisor-agents create-supervisor-agent "MKE Supply Chain Advisor" \
  --description "Routes to Actuals, Exceptions, Demand Events, Demand Exceptions agents"

# Attach Genie Agents as tools
databricks supervisor-agents create-tool supervisor-agents/{id} actuals_tool --json '{
  "tool_type": "genie_space",
  "description": "Query actual receipts, costs, and trends",
  "genie_space": {"id": "SPACE_ID_P1"}
}'

databricks supervisor-agents create-tool supervisor-agents/{id} exceptions_tool --json '{
  "tool_type": "genie_space",
  "description": "Query supply exceptions and low-stock items",
  "genie_space": {"id": "SPACE_ID_P2"}
}'

# Attach Knowledge Assistant
databricks supervisor-agents create-tool supervisor-agents/{id} docs_tool --json '{
  "tool_type": "knowledge_assistant",
  "description": "Look up policies and SOPs",
  "knowledge_assistant": {"knowledge_assistant_id": "KA_ID"}
}'
```

**Why Project Prefers Focused Agents**: Focused agents are simpler to tune, evaluate, and debug. A single supervisor adds latency and confusion (planner doesn't know which agent was used). Ship focused agents first; add supervisor only if user feedback demands it.

---

## 5. ML Training + Model Serving: Only Where Justified

**Critical**: Do NOT train an ML model just because data exists. Train only when:
1. Deterministic rules are exhausted or insufficient
2. Historical labeled data exists (not a one-time prediction)
3. The model's uncertainty is useful (e.g., forecast confidence intervals inform safety stock, not replace it)
4. Evaluation can prove it's better than a baseline (not assumed)

### Pattern: Late-Supplier Probability (Justified)

**Deterministic Baseline**: "Any supplier not receiving 100% on-time over 13 weeks is late-prone" = 52% of suppliers flagged. Too noisy.

**ML Addition**: Train a classifier on 2-year supplier history:

```python
# Databricks notebook: train_late_supplier_model
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment("/Users/me@example.com/ml_models/late_supplier_model")

# Features: lead-time, on-time rate (13-week), geography, supplier_tier, volume
df = spark.sql("""
  SELECT
    supplier_id,
    DATEDIFF(CURRENT_DATE, CURRENT_DATE - 90) AS lead_time_days,
    COUNT(CASE WHEN received_date <= due_date THEN 1 END) * 100.0 / COUNT(*) AS on_time_pct,
    CASE WHEN country IN ('US', 'CA') THEN 0 ELSE 1 END AS non_na,
    supplier_tier,  -- Encoded: 1=Tier1, 2=Tier2, 3=Tier3
    SUM(po_value) / 1e6 AS volume_millions,
    -- Label: received_date > due_date in the NEXT 4 weeks (0=on_time, 1=late)
    MAX(CASE WHEN received_date > due_date THEN 1 ELSE 0 END) AS is_late_next_4w
  FROM sandbox_operations.gold_supplier_po_history
  WHERE po_date >= DATE_SUB(CURRENT_DATE, 730)  -- 2 years of history
  GROUP BY supplier_id
""").toPandas()

# Train-test split
train = df[df['po_date'] < DATE_SUB(CURRENT_DATE, 28)]  # Exclude last 4 weeks
test = df[df['po_date'] >= DATE_SUB(CURRENT_DATE, 28)]

X_train = train[['lead_time_days', 'on_time_pct', 'non_na', 'supplier_tier', 'volume_millions']]
y_train = train['is_late_next_4w']
X_test = test[['lead_time_days', 'on_time_pct', 'non_na', 'supplier_tier', 'volume_millions']]
y_test = test['is_late_next_4w']

# Train
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

mlflow.sklearn.autolog()
model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
with mlflow.start_run(run_name="late_supplier_rf"):
  model.fit(X_train_scaled, y_train)
  train_acc = model.score(X_train_scaled, y_train)
  test_acc = model.score(X_test_scaled, y_test)
  mlflow.log_metric("test_accuracy", test_acc)
  
  # Register to UC
  mlflow.sklearn.log_model(
    model,
    "model",
    registered_model_name="ai_demo_gen.supply_chain.late_supplier_model",
  )

print(f"Test accuracy: {test_acc:.3f}")
```

**Deploy as UDF**:

```sql
-- Register model as Spark UDF
CREATE OR REPLACE FUNCTION sandbox_operations.predict_late_supplier(
  lead_time_days INT,
  on_time_pct DOUBLE,
  non_na INT,
  supplier_tier INT,
  volume_millions DOUBLE
)
RETURNS DOUBLE
LANGUAGE PYTHON
AS $$
import mlflow

model = mlflow.pyfunc.load_model("models:/ai_demo_gen.supply_chain.late_supplier_model@prod")
features = [[lead_time_days, on_time_pct, non_na, supplier_tier, volume_millions]]
return model.predict(features)[0]
$$;
```

**Use in Genie Agent as Context**:

```sql
-- Enrich exceptions with late-supplier probability
SELECT
  supplier_id,
  on_time_pct,
  sandbox_operations.predict_late_supplier(
    lead_time_days, on_time_pct, non_na, supplier_tier, volume_millions
  ) AS late_prob,  -- 0.0 = unlikely late, 1.0 = very likely late
  CASE
    WHEN late_prob > 0.7 THEN 'High risk: consider expedite or fallback supplier'
    WHEN late_prob > 0.4 THEN 'Moderate risk: monitor closely'
    ELSE 'Low risk'
  END AS supplier_risk_action
FROM sandbox_operations.gold_supplier_master
WHERE active_flag = 1
;
```

**Evaluation** (done once at deploy, repeated quarterly):

```python
import mlflow

results = mlflow.evaluate(
  model="models:/ai_demo_gen.supply_chain.late_supplier_model@prod",
  data=test_df,
  targets="is_late_next_4w",
  evaluators=["default"],
  model_type="classifier",
  evaluator_config={"log_model_explainability": True}
)

# MLflow evaluation produces: accuracy, precision, recall, F1, ROC-AUC
# If any metric drops >5% vs baseline, alert the data team
```

**Why ML, Not Rules**: Lead-time + on-time history + tier + volume have non-linear interactions (e.g., Tier-3 suppliers with high volume are riskier than their on-time % alone suggests). Historical data proves this. Deterministic rule ("tier >= 3 → risky") is too crude.

---

## 6. Lakebase Search: Exact + Keyword Retrieval (NOT Vector Search)

**The Problem**: A planner investigating a new low-stock exception asks "Show me similar incidents where we had to expedite from this supplier." They need:
- Exact SKU / PO / supplier matches (keyword)
- BM25 ranking (recent, high-value cases first)
- Structured filters (supplier, date range, status)
- Speed (<1 second)

**Why NOT Vector Search**: Vector Search is optimized for narrative/semantic similarity ("find articles about supply-chain disruption"). Milwaukee's use case is exact-match + keyword on transactional case data (SKU, PO, supplier, policy term, note text). Lakebase Search (BM25 + Postgres `lakebase_text`) lives in the app's Postgres, co-located with exception transactional state (locks, comments, approvals).

**Architecture**:

```
gold_supply_exceptions (Delta, read via Lakebase)
  ├── case_id (PK)
  ├── item_id
  ├── supplier_id
  ├── exception_type
  ├── on_hand_qty
  ├── notes (free text, searchable)
  ├── status (open/resolved/archived)
  └── created_at

    ↓ [Lakebase Read-Only Sync]

exception_cases (Lakebase Postgres table)
  ├── case_id (PK)
  ├── item_id, supplier_id, exception_type, ...
  ├── notes_text (Postgres tsvector for BM25)
  └── indexed for full-text search
```

**Query: Similar Cases (BM25 + Structured Filters)**:

```sql
-- Hybrid search in Lakebase: BM25 ranking + structured SQL filters
SELECT
  case_id,
  item_id,
  supplier_id,
  exception_type,
  on_hand_qty,
  notes,
  status,
  created_at,
  -- BM25 relevance score (0.0–1.0)
  ts_rank(notes_text, plainto_tsquery('expedite supplier')) AS bm25_score
FROM exception_cases
WHERE
  -- Structured filters (SQL)
  supplier_id = 'SUPP-001'
  AND exception_type = 'low_stock'
  AND created_at >= DATE_SUB(CURRENT_DATE, 365)
  -- Keyword search (BM25)
  AND notes_text @@ plainto_tsquery('expedite OR emergency OR rush')
  AND status IN ('resolved', 'completed')  -- Learn from closed cases
ORDER BY bm25_score DESC, created_at DESC
LIMIT 10
;
```

**Why This Beats Vector Search**:
1. **Exact matching**: SQLite + Postgres WHERE clause is instant. Vector search would need to embed "SUPP-001" and hope semantic distance finds it.
2. **Keyword + Boolean**: BM25 ranks by term frequency + inverse document frequency. "expedite" in a case title scores higher than once in body. Natural for policy/SOP terms.
3. **Deterministic**: Same query → same results every time. Vector embeddings can drift with model updates.
4. **Co-located**: Lives in the app's Postgres, no separate vector index to maintain/sync. Already backed by Lakebase CDC from Delta.

**Integration with Genie + AI Functions**:

When Genie Agent runs a query on exceptions and classifies the root-cause with `ai_classify`, the results can trigger a Lakebase search:

```python
# Lakebase client (via Databricks Python SDK)
from databricks.sql import sql

def find_similar_cases(supplier_id, exception_type):
    query = """
    SELECT case_id, item_id, notes, status, ts_rank(...) AS score
    FROM exception_cases
    WHERE supplier_id = ? AND exception_type = ? AND status = 'resolved'
    ORDER BY score DESC LIMIT 5
    """
    return sql.execute(query, [supplier_id, exception_type])

# In Genie Agent prompt
similar_cases = find_similar_cases(current_exception['supplier_id'], current_exception['exception_type'])
context = f"Similar past cases: {similar_cases}\n"
genie_response = genie_agent.ask(context + user_query)
```

**No Vector Search in MKE Project**: Deferred. If future use cases require narrative similarity ("find cases where demand spiked due to competitor event"), Vector Search can be added. For now, Lakebase Search BM25 is sufficient and operational.

---

## 7. MLflow Evaluation: Trustworthy AI

**Critical**: Before a Genie Agent or AI Function goes to production, it MUST be evaluated on a held-out dataset with a predetermined success metric.

### Pattern: Evaluate Genie Agent Accuracy

**Dataset**: 50 hand-labeled Q&A pairs (planners asking real questions, expected answers):

```sql
-- Eval dataset (in sandbox_operations.qa_eval_dataset)
| question | expected_answer | expected_rank_col | domain |
|----------|-----------------|-------------------|--------|
| Top 10 low-stock items? | item_id, on_hand_qty, woc | priority_score DESC | P2 |
| Items with late POs? | po_number, supplier, days_late | days_late DESC | P2 |
| What's our forecast for Item X? | forecast_qty, confidence_interval | date ASC | P3 |
```

**Evaluation**:

```python
import mlflow
import mlflow.genai

# Each evaluation run tests the Genie Agent on the eval dataset
eval_dataset = spark.table("sandbox_operations.qa_eval_dataset").toPandas()

results = []
for _, row in eval_dataset.iterrows():
    # Call Genie Agent
    genie_response = databricks_genie.ask_space(
        space_id="SPACE_ID_P2",
        query=row['question']
    )
    
    # Score: Did the response rank by the expected column?
    # LLM judge: "Is this answer correct and well-ranked?"
    judge_input = f"""
    Question: {row['question']}
    Expected: Show results ranked by {row['expected_rank_col']}
    Actual: {genie_response['answer']}
    SQL used: {genie_response['sql']}
    Is this answer correct? Rate 1–5.
    """
    
    score = mlflow.genai.evaluate_with_judge(
        model="databricks-claude-sonnet-4",
        judging_prompt=judge_input,
        scoring_rubric="Correctness: 1=wrong SQL/grain, 5=exact answer"
    )
    
    results.append({
        'question': row['question'],
        'score': score,
        'domain': row['domain']
    })

# Summary metrics
import pandas as pd
df_results = pd.DataFrame(results)
accuracy = (df_results['score'] >= 4).sum() / len(df_results)
print(f"Accuracy (score >= 4): {accuracy:.1%}")

# Log to MLflow
mlflow.log_metric("genie_accuracy_p2", accuracy)
mlflow.log_artifact(df_results.to_csv(), "eval_results")

# Guardrail: Fail if accuracy < 85%
assert accuracy >= 0.85, f"Genie accuracy {accuracy:.1%} below 85% threshold"
```

**Production Rule**: Genie Agents go live only if eval accuracy >= 85%. Quarterly re-evaluation on fresh test sets. If accuracy drops below 80%, agent is marked `BETA` and notifications alert the team.

---

## 8. Decision → AI Product Table

Maps each decision/question type to the right Databricks AI product, with guardrails.

| Decision | Question Type | Databricks Product | Why | What It MUST NOT Do |
|----------|---------------|-------------------|-----|-------------------|
| **P1: Actuals Trend** | "Top 10 items by received value last 4 weeks?" | Genie Agent (Ask Actuals) backed by Metric Views | One query → ranked list with trend. Metric View prevents semi-additivity error. | Must NOT invent thresholds; ABC weighting is deterministic (not LLM). |
| **P2: Low-Stock Alert** | "Which items below 2 weeks of cover need action?" | Genie Agent (Ask Exceptions) + Lakebase Search | Genie finds items. Lakebase search surface similar-past-cases for context. | Must NOT override frozen-zone policy; must NOT guess MOQ; must NOT invent priority formula. |
| **P2: PO Feasibility Check** | "Can I increase this PO by 50 units?" | UC Function (deterministic) → App → User | Frozen-zone rule, MOQ rule, lead-time rule in typed UC function. No LLM involved. | Must NOT allow PO within frozen-zone or below MOQ; must NOT speculate. |
| **P2: Investigate Root-Cause** | "Why is this low-stock?" | AI Function (`ai_classify`) + Genie Agent | Classify from movement ledger + notes into 5 categories. Genie surfaces similar past cases. | Must NOT recommend action until deterministic feasibility checks pass. |
| **P3: Demand Forecast** | "Quick 90-day forecast for Item X?" | AI Function (`ai_forecast`) | Fast baseline with confidence intervals. Feed into safety-stock formula. | Must NOT be used directly for replenishment; must be paired with deterministic safety-stock formula. |
| **P3: Demand Surge Detector** | "Which items have demand > forecast?" | Genie Agent (Ask Demand Events) | Query historical demand vs forecast. Trend visible week-over-week. | Must NOT claim causation (e.g., "demand spiked because…"); must NOT recommend action without P2/P4 context. |
| **P4: Demand Exception Root** | "Why is demand > forecast for Item Y?" | AI Function (`ai_extract` + `ai_classify`) on unstructured notes | Extract context (seasonal flag, competitor event, supply-chain mention) from notes. Classify. | Must NOT invent root causes; must be grounded in text. |
| **P4: Policy Lookup** | "What's the frozen-zone policy?" | Knowledge Assistant (Lakebase Search BM25 on policy docs) | Search uploaded SOPs, return policy excerpt. | Must NOT override policy; must reference the doc section it came from. |
| **Forecast Tuning** | "Should we raise safety stock for Item Z?" | Deterministic formula (UC function) + optional late-supplier ML model | Lead-time + forecast variance + supplier late-prob → safety stock. ML model is input, not decision-maker. | Must NOT change thresholds without data-eng approval; must NOT bypass audit trail. |
| **Report Generation** | "Summarize this week's actions?" | AI Function (`ai_summarize`) | Batch-generate action summaries from planner notes. Save time. | Must NOT be the system-of-record; must tag as AI-generated; must allow planner to override. |

---

## 9. How This Collapses the Search Pain

**Before (Pain: ~15 queries, ~15 min per planner-user per week)**:
1. Query 1: "Which POs received this week?" (find 20_supply_daily table, join to po_detail, sum by po_number) ✗ Forgot to filter on item_id
2. Query 2: "Redo, filter by item_id" ✓ (50 rows, confused by grain)
3. Query 3: "Group by item_id, not po_number" ✓ (but now missing item_code)
4. Query 4–12: Join item master (dedup SCD2 rows?), cost enrichment, ABC classification, week-end grain… "Is this on-hand or received?" Confusion.
5. Final: Manual de-duplication, ABC sort by cost (not units), compile email. 15 min elapsed.

**After (Solution: <5 seconds, certified result)**:

```
User: "Top 10 low-stock items that need action this week?"

Genie Agent:
  1. Recognize: "low-stock" = exception_type, "action" = NOT frozen
  2. Run SQL (auto-generated from example_question_sqls):
     SELECT item_id, on_hand_qty, weeks_of_cover, priority_score, frozen_zone_flag
     FROM gold_supply_exceptions
     WHERE exception_type = 'low_stock' AND frozen_zone_flag = FALSE
     ORDER BY priority_score DESC LIMIT 10
  3. Return: 10 items, ranked, with cost + ABC visible, frozen-zone status clear

Result: Excel-ready, certified by Metric Views, no grain traps possible.
```

**Impact**:
- **Planner time**: 15 min → 30 seconds (30x faster)
- **Error rate**: ~2–3 per planner per week (wrong grain, missing cost, old PO) → 0
- **Trust**: Planners know the answer is certified (Expectations-gated, Metric View verified)

---

## 10. Governance & Reliability Checklist

Before deploying any Genie Agent, AI Function, or model to production:

| Item | Owner | Pass/Fail |
|------|-------|-----------|
| **Data Quality** | Data Eng | Are underlying Gold tables SDP-governed + Expectations-passing? Is Metric View schema validated? |
| **Evaluation** | Data Scientist | Has Genie Agent been tested on 50+ labeled Q&A pairs? Accuracy >= 85%? |
| **Guardrails** | App Eng | Do UC Functions enforce frozen-zone, MOQ, lead-time checks before any PO is submitted? |
| **Lineage** | Data Eng | Can we trace prod_edw → sandbox medallion → Genie query → user action in system.access? |
| **Alerts** | Data Eng | Does the pipeline alert if Expectations fail? Is there a SLA (e.g., "Genie must respond in <10 seconds")? |
| **Docs** | Product Mgmt | Is it clear which Genie Agent to use for each question (Ask Actuals vs Ask Exceptions)? Are sample questions visible to users? |
| **Audit** | Compliance | Are PO actions traced back to Genie recommendation + user approval? |

---

## 11. AI Products Summary

| Product | MKE Use | DBR / Cluster | Cost Model | Deployed? |
|---------|---------|---------------|-----------|-----------|
| **Genie Agent (Ask Actuals, Exceptions, Demand, Demand Exceptions)** | 4 focused agents per priority; users ask in English; answers backed by Metric Views | SQL Warehouse (Pro/Serverless) | Per-token (foundation model) | ✓ Phase 1 |
| **AI Functions (classify, extract, summarize, forecast)** | Batch-enrich exceptions with root-cause; quick forecast baseline; summarize queues | DBR 15.4 ML LTS (batch jobs) | Per-token (foundation model) | ✓ Phase 2 |
| **Lakebase Search (BM25)** | Similar-case retrieval by supplier + exception type; co-located with transactional state in app Postgres | Lakebase Postgres | Serverless Postgres pricing | ✓ Phase 2 |
| **Knowledge Assistant (Policy Q&A)** | "What's the frozen-zone policy?" on SOP docs; RAG over PDFs | Genie (serverless) | Per-token | ✓ Phase 3 (optional) |
| **Supervisor Agent** | Optional single entry point if 4 Genie Agents feel fragmented | Genie (serverless) | Per-token | Phase 4 (deferred; project prefers focused agents) |
| **ML Model Serving (late-supplier probability)** | Inform safety stock; used as context in Genie Agent; no independent decision | Model Serving endpoint (serverless) | Per-request (cheap; <1ms/item) | ✓ Phase 3 (optional; only if late-supplier prediction adds value) |
| **MLflow Evaluation** | Quarterly eval of Genie Agent accuracy; watchdog for drift | DBR 15.4 (batch job) | Compute time | ✓ Ongoing |
| **Vector Search** | NOT used in MKE Phase 1–3. Deferred. If future use case requires semantic narrative matching, can be added. | VS endpoint (storage-optimized) | Per-token (embedding) | ✗ Deferred |

---

## 12. Timeline & Rollout

| Phase | Focus | Genie Agents | AI Functions | Lakebase | Evaluation | Duration |
|-------|-------|--------------|--------------|----------|------------|----------|
| **Phase 1** | P1 + P2 agents live | Ask Actuals, Ask Exceptions (2 agents) | — | — | Manual (50-item eval set) | Week 1–2 |
| **Phase 2** | P3 + P4 agents; batch AI functions | + Ask Demand, Ask Demand Exceptions | `ai_classify` root-cause; `ai_forecast` baseline | Lakebase BM25 similar cases | MLflow eval loop; quarterly re-eval | Week 3–4 |
| **Phase 3** | Optional ML model + docs | (stable, no changes) | `ai_summarize` planner queue | (stable) | Late-supplier model eval; quarterly Genie re-eval | Week 5–6 |
| **Phase 4** | Supervisor (optional) | Add Supervisor Agent if feedback demands single entry | (stable) | (stable) | (stable) | Week 7+ (optional) |

---

## 13. Example Planner Workflow (End-to-End)

**Scenario**: Monday morning, planner opens the MKE Supply Chain app.

1. **Dashboard shows**: Top 10 low-stock items (via Genie Agent Ask Exceptions, backed by Metric Views)
2. **Planner clicks Item #3** ("BOLT-XYZ, 1.2 weeks of cover, $18.5K at-risk value"):
   - **Lakebase Search** surfaces 3 similar past cases:
     - Case 847 (same supplier SUPP-001): "Expedited via airfreight; cost +$2.3K" (resolved)
     - Case 621 (same item): "Demand spike due to new customer; planned for next quarter" (completed)
     - Case 1103 (same supplier, different item): "Quality hold; released after 3-day inspection" (resolved)
3. **Planner reviews** → Decides: "This time, let's try expedite like Case 847."
4. **Planner submits PO (+500 units, expedited shipping)**:
   - **UC Function checks**:
     - ✓ Not in frozen-zone (14 days to cutoff)
     - ✓ 500 >= MOQ (100)
     - ✓ Supplier (SUPP-001) lead-time 28 days, OK for expedite window
   - ✓ **PO submitted**, tagged with "similar_case_847", logged in audit trail
5. **App generates summary**: "Action: Expedited PO-XYZ, +500 BOLT-XYZ from SUPP-001. Context: Similar to Case 847 (successful expedite). Estimated delivery: +3 days."
6. **AI Function `ai_summarize`** rolls this + other week's actions into: "Week Summary: 7 POs submitted, 5 expedited (high-cost), 2 standard. At-risk value mitigated: $47.2K → $8.3K."

**No grain errors, no semi-additivity, no magnitude illusion. Planner made a data-informed decision in 3 minutes.**

---

## Conclusion

This AI/decision-making architecture **collapses the search pain** by:

1. **Genie Agents** (4 focused) answer 80% of planner questions in <5 seconds, certified by Metric Views
2. **AI Functions** (classify, extract, summarize, forecast) enrich exceptions and reduce manual work
3. **Lakebase Search** (BM25) surfaces similar cases for context without maintaining a separate vector index
4. **UC Functions** (deterministic: frozen-zone, MOQ, lead-time) enforce constraints before any action
5. **MLflow Evaluation** keeps Genie agents trustworthy; quarterly re-eval catches drift
6. **No LLM decides**: LLM explains, coordinates, and grounds recommendations in data + similar cases + deterministic rules

**The rule is simple**: Deterministic constraints + math → in SQL/UC Functions. Variance, narrative, hypothesis, explanation → AI Functions + Genie (grounded, evaluated). No fusion, no guessing. Just faster, trustworthy decisions.
