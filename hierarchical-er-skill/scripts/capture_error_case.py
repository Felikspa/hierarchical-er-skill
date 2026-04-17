from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    ERROR_CASES_DIR,
    ERROR_INDEX_PATH,
    active_entities,
    active_relations,
    calculate_review_summary,
    clone_run,
    load_json,
    load_json_lines,
    load_run,
    load_schema,
    now_iso,
    write_json,
    write_json_lines,
    write_run,
)

CONFLICT_CODES = {
    "UNKNOWN_RELATION_TYPE",
    "MISSING_ENTITY_REFERENCE",
    "INVALID_RELATION_PAIR",
    "DIRECTION_MISMATCH",
    "CROSS_SENTENCE_WINDOW",
    "DUPLICATE_RELATION",
}


def _suggestions(run: dict, reasons: list[str]) -> dict:
    tags = set()
    prompt_points = set()

    if "low_confidence" in reasons:
        tags.add("low-confidence")
        prompt_points.add("要求每条关系必须给出最小证据片段，并解释证据与关系之间的语义连接。")
    if "constraint_conflict" in reasons:
        tags.add("constraint-conflict")
        prompt_points.add("先根据 schema 验证 head/tail 实体类型，再输出关系方向与 relation type。")
    if "review_substantive_edit" in reasons:
        tags.add("human-corrected")
        prompt_points.add("输出前自检 canonical name、关系方向和实体归一是否与原文一致。")

    relation_types = {relation["type"] for relation in active_relations(run)}
    for relation_type in sorted(relation_types):
        tags.add(f"rel:{relation_type}")

    return {
        "few_shot_tags": sorted(tags),
        "prompt_optimizations": sorted(prompt_points),
    }


def build_case_payload(
    run: dict,
    reasons: list[str],
    reviewed_run: dict | None,
    edit_summary: dict,
) -> dict:
    case_id = f"case-{run['run_id']}"
    suggestions = _suggestions(run, reasons)
    return {
        "case_id": case_id,
        "run_id": run["run_id"],
        "captured_at": now_iso(),
        "reasons": reasons,
        "input_text": run["input_text"],
        "original_result": {
            "mode": run["mode"],
            "entities": active_entities(run),
            "relations": active_relations(run),
        },
        "issues": run["issues"],
        "confidence_summary": run["confidence"]["summary"],
        "reviewed_result": None
        if reviewed_run is None
        else {
            "entities": active_entities(reviewed_run),
            "relations": active_relations(reviewed_run),
        },
        "edit_summary": edit_summary,
        "few_shot_tags": suggestions["few_shot_tags"],
        "prompt_optimization_points": suggestions["prompt_optimizations"],
    }


def persist_case(case_payload: dict) -> None:
    case_path = ERROR_CASES_DIR / f"{case_payload['case_id']}.json"
    write_json(case_path, case_payload)

    rows = load_json_lines(ERROR_INDEX_PATH)
    index_row = {
        "case_id": case_payload["case_id"],
        "run_id": case_payload["run_id"],
        "captured_at": case_payload["captured_at"],
        "reasons": case_payload["reasons"],
    }
    replaced = False
    for idx, row in enumerate(rows):
        if row["case_id"] == case_payload["case_id"]:
            rows[idx] = index_row
            replaced = True
            break
    if not replaced:
        rows.append(index_row)
    write_json_lines(ERROR_INDEX_PATH, rows)


def evaluate_capture(run: dict, reviewed_run: dict | None = None) -> tuple[dict, dict | None]:
    schema = load_schema()
    reasons: list[str] = []
    low_threshold = schema["confidence_thresholds"]["low"]
    substantive_threshold = schema["review_thresholds"]["substantive_edits"]
    ratio_threshold = schema["review_thresholds"]["edit_ratio"]

    if any(item["final"] < low_threshold for item in run["confidence"]["entities"] + run["confidence"]["relations"]):
        reasons.append("low_confidence")

    if any(issue["code"] in CONFLICT_CODES for issue in run["issues"]):
        reasons.append("constraint_conflict")

    edit_summary = {
        "substantive_edits": 0,
        "edit_ratio": 0,
        "changed_entities": [],
        "changed_relations": [],
        "total_items": len(active_entities(run)) + len(active_relations(run)),
    }
    if reviewed_run is not None:
        edit_summary = calculate_review_summary(run, reviewed_run)
        if (
            edit_summary["substantive_edits"] >= substantive_threshold
            or edit_summary["edit_ratio"] >= ratio_threshold
        ):
            reasons.append("review_substantive_edit")

    if not reasons:
        suggestions = _suggestions(run, [])
        return (
            {
                "should_capture": False,
                "reasons": [],
                "case_id": None,
                "suggestions": suggestions,
            },
            None,
        )

    case_payload = build_case_payload(run, reasons, reviewed_run, edit_summary)
    return (
        {
            "should_capture": True,
            "reasons": reasons,
            "case_id": case_payload["case_id"],
            "suggestions": {
                "few_shot_tags": case_payload["few_shot_tags"],
                "prompt_optimizations": case_payload["prompt_optimization_points"],
            },
        },
        case_payload,
    )


def evaluate_and_capture(run_path: Path, reviewed_run: dict | None = None) -> dict:
    run = load_run(run_path)
    capture_payload, case_payload = evaluate_capture(run, reviewed_run)
    run["error_capture"] = capture_payload
    write_run(run_path, run)
    if case_payload is not None:
        persist_case(case_payload)
    return capture_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture ER error cases")
    parser.add_argument("run_json", type=Path)
    parser.add_argument("--review-json", type=Path)
    args = parser.parse_args()

    reviewed = None if args.review_json is None else load_json(args.review_json)
    capture = evaluate_and_capture(args.run_json, reviewed)
    print(capture)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

