# Sources & Provenance

This skill distills a set of discussion documents in which the user defined how they want
Databricks development done for the Milwaukee Electric Tool supply-chain project. The originals
live in the project's `development_pattern/` folder. This skill is the *operating distillation*;
the originals are the *source of record* (they include full reference-URL footnotes stripped from
the skill for brevity).

## Original documents → where they map in this skill

**Two source folders:** `development_pattern/` (how the user wants work done — the operating
pattern) and `customer_requirements/` (what to build — the authoritative requirement docs). The
requirement docs are the source of record for scope and always outrank the distilled summary.

| Requirement doc (`customer_requirements/…`) | Distilled into |
|---|---|
| `Actuals_Supply_Plan_Requirements.md` | `references/project-scope-and-delivery.md` (P1 — confirmed tables, decisions D1–D6, thresholds, backfill, open items) |
| `Red_Keychain_Supply_Planning_Requirements.md` | `references/project-scope-and-delivery.md` (P2 supply exceptions + P4 demand exceptions; 18-type taxonomy; broader ordering program noted as context) |
| `01_Requirements.md` (Demand Events) | `references/project-scope-and-delivery.md` (P3 — lifecycle, locking, disaggregation, Forecast Builder, output contract) |

| Source document (`development_pattern/…`) | Distilled into |
|---|---|
| `000_base_rule.md` | `../SKILL.md` guardrails; project `CLAUDE.md`; `mke-project-guardrails` memory |
| `Databricks-Centric Development Operating Pattern.md` | `../SKILL.md` core; `references/fit-for-purpose-decisions.md`; `references/governance-and-quality.md` |
| `Workspace-First Databricks Development and Bundle Promotion.md` | `references/workspace-first-promotion.md` |
| `MLflow and Databricks AI Engineering Playbook for Supply Chain.md` | `references/mlflow-ai-engineering.md` |
| `Is there a better way to direct a machine to do th.md` (multi-turn conversation) | roles/domain turns → `references/supply-chain-domain.md`; "no blind development" turn → `references/fit-for-purpose-decisions.md`; agentic-app + auth/networking turn → `references/frontend-fullstack.md`; requirements→Databricks turn (search / reverse-ETL / deterministic-vs-AI) → `references/fit-for-purpose-decisions.md`; granularity/Kimball/star-snowflake turn → `references/dimensional-modeling.md`; "run it the Databricks way" turn → `references/databricks-execution-craft.md`; medallion turn → `references/dimensional-modeling.md`; P1–P4 scope + shared deliverables + delivery-sequence + completion-package turns → `references/project-scope-and-delivery.md`; frontend/gotchas turn → `references/frontend-fullstack.md` (build/verify) + `references/platform-gotchas.md` (embedding/limits); control-tower/writeback + loops/modes/nervous-system turns → `references/supply-chain-domain.md`; latest-docs/DQX/Labs turn → `references/tooling-and-currency.md`; workshop retrospective + "past work as reference" turns → `references/lessons-and-evidence.md`; read-only guardrail turn → `../SKILL.md` + `CLAUDE.md` + memory |

## Non-negotiable base rules (verbatim intent, from `000_base_rule.md` + the read-only turn)

- Learn everything, but do not overengineer where it is not needed.
- Challenge yourself.
- When chat memory nears its threshold, write a detailed handoff document on the designs and
  decisions made.
- `prod_edw` and `prod_operations` are for READ only — no write.
- Writes go to `sandbox_operations.po_management`; Lakebase is used for transactional writes.

## Maintenance

When the user refines the operating pattern in a future session, update the matching reference
file here (and the guardrails in `../SKILL.md` / `CLAUDE.md` / memory if a rule changes), then
note the change so provenance stays traceable. Keep `SKILL.md` lean — depth belongs in
`references/`.
