from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SKILL_ROOT / "data"
RUNS_DIR = DATA_DIR / "runs"
GRAPH_PATH = DATA_DIR / "graph" / "graph-memory.json"
ERROR_INDEX_PATH = DATA_DIR / "errors" / "error-set.jsonl"
ERROR_CASES_DIR = DATA_DIR / "errors" / "cases"
REGRESSION_DIR = DATA_DIR / "regression" / "cases"
SCHEMA_PATH = SKILL_ROOT / "schema" / "schema.yaml"
OUTPUT_CONTRACT_PATH = SKILL_ROOT / "contracts" / "output.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    lines = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if text:
                lines.append(json.loads(text))
    return lines


def write_json_lines(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def load_schema() -> dict[str, Any]:
    return load_json(SCHEMA_PATH)


def load_output_contract() -> dict[str, Any]:
    return load_json(OUTPUT_CONTRACT_PATH)


def load_run(path: str | Path) -> dict[str, Any]:
    return load_json(Path(path))


def write_run(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)


def list_base_run_paths() -> list[Path]:
    paths = []
    for path in RUNS_DIR.glob("*.json"):
        if path.name.endswith(".review.json"):
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: load_json(item)["created_at"], reverse=True)


def find_run_path(run_id: str) -> Path:
    path = RUNS_DIR / f"{run_id}.json"
    if path.exists():
        return path
    for candidate in list_base_run_paths():
        run = load_json(candidate)
        if run["run_id"] == run_id:
            return candidate
    raise FileNotFoundError(run_id)


def normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"\s+", "", lowered)
    lowered = re.sub(r"[^\w\u4e00-\u9fff]", "", lowered)
    return lowered


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def index_by(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items}


def active_entities(run: dict[str, Any]) -> list[dict[str, Any]]:
    if run["mode"] == "coarse":
        return run["entities_coarse"]
    return run["entities_fine"]


def active_relations(run: dict[str, Any]) -> list[dict[str, Any]]:
    if run["mode"] == "coarse":
        return run["relations_coarse"]
    return run["relations_fine"]


def band_for_score(score: float, thresholds: dict[str, float]) -> str:
    if score < thresholds["low"]:
        return "low"
    if score < thresholds["medium"]:
        return "medium"
    return "high"


def targeted_issues(issues: list[dict[str, Any]], target_id: str) -> list[dict[str, Any]]:
    return [issue for issue in issues if target_id in issue["target_ids"]]


def clone_run(payload: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(payload)


def _entity_signature(entity: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entity["label"],
        entity["canonical_name"],
        entity["span"]["start"],
        entity["span"]["end"],
    )


def _relation_signature(relation: dict[str, Any]) -> tuple[Any, ...]:
    return (
        relation["type"],
        relation["head_id"],
        relation["tail_id"],
        relation["direction"],
    )


def calculate_review_summary(
    original_run: dict[str, Any], reviewed_run: dict[str, Any]
) -> dict[str, Any]:
    original_entities = index_by(active_entities(original_run), "entity_id")
    reviewed_entities = index_by(active_entities(reviewed_run), "entity_id")
    original_relations = index_by(active_relations(original_run), "relation_id")
    reviewed_relations = index_by(active_relations(reviewed_run), "relation_id")

    substantive_edits = 0
    changed_entities = []
    changed_relations = []

    all_entity_ids = sorted(set(original_entities) | set(reviewed_entities))
    for entity_id in all_entity_ids:
        original = original_entities.get(entity_id)
        reviewed = reviewed_entities.get(entity_id)
        if original is None or reviewed is None:
            substantive_edits += 1
            changed_entities.append(entity_id)
            continue
        if _entity_signature(original) != _entity_signature(reviewed):
            substantive_edits += 1
            changed_entities.append(entity_id)

    all_relation_ids = sorted(set(original_relations) | set(reviewed_relations))
    for relation_id in all_relation_ids:
        original = original_relations.get(relation_id)
        reviewed = reviewed_relations.get(relation_id)
        if original is None or reviewed is None:
            substantive_edits += 1
            changed_relations.append(relation_id)
            continue
        if _relation_signature(original) != _relation_signature(reviewed):
            substantive_edits += 1
            changed_relations.append(relation_id)

    total_items = len(original_entities) + len(original_relations)
    edit_ratio = 0 if total_items == 0 else substantive_edits / total_items
    return {
        "substantive_edits": substantive_edits,
        "edit_ratio": round(edit_ratio, 4),
        "changed_entities": changed_entities,
        "changed_relations": changed_relations,
        "total_items": total_items,
    }


def relation_tuple(
    relation: dict[str, Any], entity_lookup: dict[str, dict[str, Any]]
) -> tuple[str, str, str]:
    head = entity_lookup[relation["head_id"]]["canonical_name"]
    tail = entity_lookup[relation["tail_id"]]["canonical_name"]
    return (relation["type"], head, tail)


def summary_for_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "created_at": run["created_at"],
        "mode": run["mode"],
        "issue_count": len(run.get("issues", [])),
        "review_status": run.get("review_status", {}),
        "error_capture": run.get("error_capture", {}),
    }
