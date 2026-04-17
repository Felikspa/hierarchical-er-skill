from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import active_entities, active_relations, index_by, load_run, load_schema, write_run

GENERATED_CODES = {
    "UNKNOWN_RELATION_TYPE",
    "MISSING_ENTITY_REFERENCE",
    "INVALID_RELATION_PAIR",
    "DIRECTION_MISMATCH",
    "CROSS_SENTENCE_WINDOW",
    "DUPLICATE_RELATION",
}


def _base_issues(issues: list[dict]) -> list[dict]:
    return [issue for issue in issues if issue["code"] not in GENERATED_CODES]


def _normalize_relation_type(schema: dict, relation_type: str) -> str:
    return schema["relation_aliases"].get(relation_type, relation_type)


def _expected_direction(head_label: str, tail_label: str) -> str:
    return f"{head_label}->{tail_label}"


def _check_relation_set(
    schema: dict,
    entities: list[dict],
    relations: list[dict],
    prefix: str,
) -> list[dict]:
    entity_lookup = index_by(entities, "entity_id")
    issues: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for relation in relations:
        relation_id = relation["relation_id"]
        normalized_type = _normalize_relation_type(schema, relation["type"])
        if normalized_type not in schema["allowed_relation_pairs"]:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-unknown-type",
                    "level": "error",
                    "code": "UNKNOWN_RELATION_TYPE",
                    "message": f"{prefix}: unsupported relation type '{relation['type']}'",
                    "target_ids": [relation_id],
                }
            )
            continue

        head = entity_lookup.get(relation["head_id"])
        tail = entity_lookup.get(relation["tail_id"])
        if head is None or tail is None:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-missing-entity",
                    "level": "error",
                    "code": "MISSING_ENTITY_REFERENCE",
                    "message": f"{prefix}: relation references an unknown entity id",
                    "target_ids": [relation_id],
                }
            )
            continue

        pair = [head["label"], tail["label"]]
        allowed_pairs = schema["allowed_relation_pairs"][normalized_type]
        if pair not in allowed_pairs:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-invalid-pair",
                    "level": "error",
                    "code": "INVALID_RELATION_PAIR",
                    "message": f"{prefix}: pair {pair} is not allowed for relation '{normalized_type}'",
                    "target_ids": [relation_id],
                }
            )

        direction_rule = schema["direction_rules"][normalized_type]
        if head["label"] not in direction_rule["head"] or tail["label"] not in direction_rule["tail"]:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-direction",
                    "level": "error",
                    "code": "DIRECTION_MISMATCH",
                    "message": f"{prefix}: direction {relation['direction']} conflicts with schema",
                    "target_ids": [relation_id],
                }
            )

        expected = _expected_direction(head["label"], tail["label"])
        if relation["direction"] != expected:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-direction-string",
                    "level": "warning",
                    "code": "DIRECTION_MISMATCH",
                    "message": f"{prefix}: relation direction string should be '{expected}'",
                    "target_ids": [relation_id],
                }
            )

        window = schema["cross_sentence_windows"][normalized_type]
        if relation["sentence_distance"] > window:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-window",
                    "level": "warning",
                    "code": "CROSS_SENTENCE_WINDOW",
                    "message": f"{prefix}: sentence distance {relation['sentence_distance']} exceeds window {window}",
                    "target_ids": [relation_id],
                }
            )

        dedupe_key = (normalized_type, relation["head_id"], relation["tail_id"])
        if dedupe_key in seen:
            issues.append(
                {
                    "issue_id": f"issue-{relation_id}-duplicate",
                    "level": "warning",
                    "code": "DUPLICATE_RELATION",
                    "message": f"{prefix}: duplicate relation tuple detected",
                    "target_ids": [relation_id],
                }
            )
        seen.add(dedupe_key)

    return issues


def evaluate_constraints(run: dict) -> list[dict]:
    schema = load_schema()
    issues = _base_issues(run.get("issues", []))
    issues.extend(
        _check_relation_set(schema, run["entities_coarse"], run["relations_coarse"], "coarse")
    )
    issues.extend(
        _check_relation_set(schema, run["entities_fine"], run["relations_fine"], "fine")
    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ER schema constraints")
    parser.add_argument("run_json", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    run = load_run(args.run_json)
    run["issues"] = evaluate_constraints(run)

    if args.write:
        write_run(args.run_json, run)

    print(f"constraint issues: {len(run['issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
