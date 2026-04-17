from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import load_output_contract, load_run


def _validate_entity(entity: dict, prefix: str, errors: list[str]) -> None:
    required = ["entity_id", "label", "text", "canonical_name", "span", "aliases", "evidence_ids"]
    for key in required:
        if key not in entity:
            errors.append(f"{prefix}: missing key '{key}'")
    if "span" in entity:
        for key in ["chunk_id", "start", "end"]:
            if key not in entity["span"]:
                errors.append(f"{prefix}.span: missing key '{key}'")


def _validate_relation(relation: dict, prefix: str, errors: list[str]) -> None:
    required = ["relation_id", "type", "head_id", "tail_id", "direction", "evidence_ids", "sentence_distance"]
    for key in required:
        if key not in relation:
            errors.append(f"{prefix}: missing key '{key}'")


def _validate_top_level(run: dict, errors: list[str]) -> None:
    contract = load_output_contract()
    for key in contract["required"]:
        if key not in run:
            errors.append(f"root: missing key '{key}'")
    if run.get("mode") not in {"coarse", "standard", "fine"}:
        errors.append("root.mode must be one of coarse|standard|fine")
    for collection_key in ["entities_coarse", "entities_fine"]:
        for index, entity in enumerate(run.get(collection_key, [])):
            _validate_entity(entity, f"{collection_key}[{index}]", errors)
    for collection_key in ["relations_coarse", "relations_fine"]:
        for index, relation in enumerate(run.get(collection_key, [])):
            _validate_relation(relation, f"{collection_key}[{index}]", errors)
    for index, chunk in enumerate(run.get("chunks", [])):
        for key in ["chunk_id", "text", "start", "end", "sentence_start", "sentence_end"]:
            if key not in chunk:
                errors.append(f"chunks[{index}]: missing key '{key}'")
    for index, evidence in enumerate(run.get("evidence", [])):
        for key in ["evidence_id", "chunk_id", "text", "start", "end", "sentence_index"]:
            if key not in evidence:
                errors.append(f"evidence[{index}]: missing key '{key}'")
    confidence = run.get("confidence", {})
    for key in ["thresholds", "entities", "relations", "summary"]:
        if key not in confidence:
            errors.append(f"confidence: missing key '{key}'")
    review = run.get("review_status", {})
    for key in ["status", "substantive_edits", "edit_ratio", "revised_run_path", "last_reviewed_at"]:
        if key not in review:
            errors.append(f"review_status: missing key '{key}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate hierarchical ER run output")
    parser.add_argument("run_json", type=Path)
    args = parser.parse_args()

    run = load_run(args.run_json)
    errors: list[str] = []
    _validate_top_level(run, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated {args.run_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

