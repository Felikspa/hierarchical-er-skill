from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    active_entities,
    active_relations,
    band_for_score,
    load_run,
    load_schema,
    targeted_issues,
    write_run,
)

LOW_CONFIDENCE_CODE = "LOW_CONFIDENCE"


def _base_issues(issues: list[dict]) -> list[dict]:
    return [issue for issue in issues if issue["code"] != LOW_CONFIDENCE_CODE]


def _model_score_entity(entity: dict) -> float:
    score = 0.62 + 0.12 * min(2, len(entity["evidence_ids"]))
    if entity["aliases"]:
        score += 0.03
    return min(score, 0.95)


def _model_score_relation(relation: dict) -> float:
    score = 0.58 + 0.12 * min(2, len(relation["evidence_ids"])) - 0.05 * relation["sentence_distance"]
    return max(0.2, min(score, 0.95))


def _evidence_score(evidence_ids: list[str]) -> float:
    return min(1.0, 0.45 + 0.2 * len(evidence_ids))


def _issue_penalty(issues: list[dict]) -> tuple[float, float]:
    errors = sum(1 for issue in issues if issue["level"] == "error")
    warnings = sum(1 for issue in issues if issue["level"] == "warning")
    rule_score = max(0.0, 1.0 - 0.25 * errors - 0.1 * warnings)
    conflict_penalty = min(1.0, 0.35 * errors + 0.15 * warnings)
    return rule_score, conflict_penalty


def _score_item(kind: str, item: dict, issues: list[dict], thresholds: dict[str, float]) -> dict:
    if kind == "entity":
        model_score = _model_score_entity(item)
    else:
        model_score = _model_score_relation(item)
    evidence_score = _evidence_score(item["evidence_ids"])
    rule_score, conflict_penalty = _issue_penalty(issues)
    final = (
        0.45 * model_score
        + 0.25 * evidence_score
        + 0.20 * rule_score
        + 0.10 * (1 - conflict_penalty)
    )
    final = round(final, 4)
    return {
        "target_id": item["entity_id"] if kind == "entity" else item["relation_id"],
        "kind": kind,
        "model_score": round(model_score, 4),
        "evidence_score": round(evidence_score, 4),
        "rule_score": round(rule_score, 4),
        "conflict_penalty": round(conflict_penalty, 4),
        "final": final,
        "band": band_for_score(final, thresholds),
    }


def score_run(run: dict) -> dict:
    schema = load_schema()
    thresholds = schema["confidence_thresholds"]
    entity_scores = []
    relation_scores = []

    for entity in active_entities(run):
        entity_scores.append(
            _score_item(
                "entity",
                entity,
                targeted_issues(run["issues"], entity["entity_id"]),
                thresholds,
            )
        )

    for relation in active_relations(run):
        relation_scores.append(
            _score_item(
                "relation",
                relation,
                targeted_issues(run["issues"], relation["relation_id"]),
                thresholds,
            )
        )

    summary = {"low": 0, "medium": 0, "high": 0}
    for item in entity_scores + relation_scores:
        summary[item["band"]] += 1

    issues = _base_issues(run.get("issues", []))
    for item in entity_scores + relation_scores:
        if item["band"] == "low":
            issues.append(
                {
                    "issue_id": f"issue-{item['target_id']}-low-confidence",
                    "level": "warning",
                    "code": LOW_CONFIDENCE_CODE,
                    "message": f"{item['kind']} {item['target_id']} scored low confidence ({item['final']})",
                    "target_ids": [item["target_id"]],
                }
            )

    run["issues"] = issues
    run["confidence"] = {
        "thresholds": thresholds,
        "entities": entity_scores,
        "relations": relation_scores,
        "summary": summary,
    }
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description="Score ER confidence")
    parser.add_argument("run_json", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    run = score_run(load_run(args.run_json))
    if args.write:
        write_run(args.run_json, run)
    print(run["confidence"]["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

