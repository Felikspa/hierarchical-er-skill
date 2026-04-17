from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    REGRESSION_DIR,
    RUNS_DIR,
    active_entities,
    active_relations,
    index_by,
    load_json,
    relation_tuple,
)


def evaluate_case(case_path: Path) -> dict:
    case = load_json(case_path)
    run = load_json(RUNS_DIR / case["run_fixture"])
    entity_names = {entity["canonical_name"] for entity in active_entities(run)}
    entity_lookup = index_by(active_entities(run), "entity_id")
    relation_tuples = {relation_tuple(relation, entity_lookup) for relation in active_relations(run)}

    expected_names = set(case["expected"]["entity_canonical_names"])
    expected_relations = {tuple(item) for item in case["expected"]["relation_tuples"]}

    return {
        "case_id": case["case_id"],
        "pass": entity_names == expected_names and relation_tuples == expected_relations,
        "missing_entities": sorted(expected_names - entity_names),
        "extra_entities": sorted(entity_names - expected_names),
        "missing_relations": sorted(expected_relations - relation_tuples),
        "extra_relations": sorted(relation_tuples - expected_relations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report regression status")
    parser.parse_args()

    results = [evaluate_case(path) for path in sorted(REGRESSION_DIR.glob("*.json"))]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

