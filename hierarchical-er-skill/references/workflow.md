# Workflow Reference

## Seven-step execution order

1. Parse the user request and map it to `coarse`, `standard`, or `fine`.
2. Read the relevant entity/relation view from `schema/schema.yaml`.
3. Extract entities, relations, evidence, and chunk references.
4. Run deterministic constraint checks and keep every conflict in `issues`.
5. Score confidence with the fixed hybrid formula.
6. Update graph memory and evaluate error-case capture.
7. Write run data, refresh the web panel, and review if needed.

## Confidence definition

Use the fixed weighted formula:

```text
final = 0.45 * model_score
      + 0.25 * evidence_score
      + 0.20 * rule_score
      + 0.10 * (1 - conflict_penalty)
```

Band mapping:

- `low` when `final < 0.65`
- `medium` when `0.65 <= final < 0.85`
- `high` when `final >= 0.85`

## Deterministic conflict checks

- Flag relations whose label pair is not in `allowed_relation_pairs`.
- Flag direction mismatches against `direction_rules`.
- Flag cross-sentence relations that exceed the configured window.
- Flag duplicate relations with identical normalized `(type, head_id, tail_id)`.
- Keep every flagged item in `issues`; never silently rewrite user-visible facts.

## Graph-memory update rules

Normalize in this order:

1. Canonical name exact match
2. Alias hit
3. Compatible label and normalized string match
4. Known alias mapping already stored in graph memory

Only add a new graph entity when all four checks fail.

## Error-case rules

Capture a case when any of these is true:

- at least one confidence item is `low`
- at least one issue is a conflict or invalid-pair error
- review causes `>= 2` substantive edits
- review edit ratio is `>= 0.3`

