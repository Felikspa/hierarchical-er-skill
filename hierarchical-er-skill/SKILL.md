---
name: hierarchical-er-skill
description: Hierarchical entity-relation extraction skill with coarse/standard/fine granularity control, evidence retention, deterministic constraint checks, local graph-memory updates, error-set capture, and review web panel refresh. Use when Codex needs to extract entities and relations from plain text, preserve evidence, normalize aliases across runs, record issues instead of hiding uncertainty, or refresh a local ER review/debug workflow.
---

# Hierarchical ER Skill

Follow this workflow whenever the skill triggers.

## Read these files deliberately

- Read `schema/schema.yaml` before assigning labels or relation directions.
- Read `contracts/output.schema.json` before writing any run JSON.
- Read `references/workflow.md` when deciding granularity, scoring, conflicts, or graph updates.
- Read `references/web-panel.md` before shaping review-facing fields or summaries.

## Enforce the three modes

- Use `coarse` only for high-level entities and relations.
- Use `standard` for business-readable granularity.
- Use `fine` for the most detailed output and always preserve evidence.
- If the user explicitly says `尽可能细` or asks to keep evidence, use `fine`.
- If the user explicitly says `粗粒度`, use `coarse`.
- Otherwise use `standard`.

## Produce a compliant run

- Write a run JSON that satisfies `contracts/output.schema.json`.
- Keep `entities_coarse` and `relations_coarse` populated for every mode.
- Keep `entities_fine` and `relations_fine` populated for `standard` and `fine`.
- Attach evidence ids to every extracted entity and relation.
- Record uncertainty, conflict, or missing support inside `issues`; do not suppress it.

## Execute the deterministic post-processing steps

Run the scripts in this order:

```powershell
python scripts/validate_output.py <run-json>
python scripts/check_constraints.py <run-json> --write
python scripts/score_confidence.py <run-json> --write
python scripts/update_graph_memory.py <run-json>
python scripts/capture_error_case.py <run-json>
python scripts/serve_review_app.py --port 8765
```

## Review discipline

- Refresh the local web panel after every run.
- Save human review edits into a revision JSON via the review API.
- If the review changes at least two extracted items, or changes 30% or more of extracted items, let the case enter the error set.

## Graph-memory discipline

- Normalize entities by canonical name, alias hits, compatible type, normalized string similarity, and known mappings.
- Append new relations only when the normalized pair and relation type are not already present for the same direction.
- Record all updates under `graph_updates`.

## Error-set discipline

- Capture a case if confidence falls below threshold.
- Capture a case if rules or evidence conflict.
- Capture a case after substantial manual review edits.
- Generate few-shot tags and prompt-improvement suggestions, but do not auto-edit the skill.

