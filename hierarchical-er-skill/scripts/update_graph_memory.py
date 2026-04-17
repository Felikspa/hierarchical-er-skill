from __future__ import annotations

import argparse
from difflib import SequenceMatcher
from pathlib import Path

from common import (
    GRAPH_PATH,
    active_entities,
    active_relations,
    index_by,
    load_json,
    load_run,
    now_iso,
    normalize_text,
    write_json,
    write_run,
)


def _next_entity_id(graph: dict) -> str:
    return f"g-entity-{len(graph['entities']) + 1:04d}"


def _next_relation_id(graph: dict) -> str:
    return f"g-relation-{len(graph['relations']) + 1:04d}"


def _match_entity(graph: dict, entity: dict) -> tuple[dict | None, str | None]:
    normalized_name = normalize_text(entity["canonical_name"])
    for existing in graph["entities"]:
        if normalize_text(existing["canonical_name"]) == normalized_name:
            return existing, "canonical_name"

    alias_lookup = {
        normalize_text(alias_entry["alias"]): alias_entry["graph_entity_id"]
        for alias_entry in graph["aliases"]
    }
    for alias in [entity["canonical_name"], *entity["aliases"], entity["text"]]:
        graph_id = alias_lookup.get(normalize_text(alias))
        if graph_id is not None:
            for existing in graph["entities"]:
                if existing["graph_entity_id"] == graph_id:
                    return existing, "alias"

    for existing in graph["entities"]:
        if existing["label"] != entity["label"]:
            continue
        similarity = SequenceMatcher(
            None,
            normalize_text(existing["canonical_name"]),
            normalized_name,
        ).ratio()
        if similarity >= 0.92:
            return existing, "normalized_similarity"

    return None, None


def _append_unique(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def update_graph_memory(run: dict) -> tuple[dict, dict]:
    graph = load_json(GRAPH_PATH)
    now = now_iso()
    entity_mapping: dict[str, str] = {}
    matched_entities = []
    new_entities = []
    new_relations = []

    for entity in active_entities(run):
        match, reason = _match_entity(graph, entity)
        if match is None:
            match = {
                "graph_entity_id": _next_entity_id(graph),
                "canonical_name": entity["canonical_name"],
                "label": entity["label"],
                "aliases": sorted(set([entity["text"], *entity["aliases"]])),
                "source_entity_ids": [entity["entity_id"]],
                "source_runs": [run["run_id"]],
                "last_seen_at": now,
            }
            graph["entities"].append(match)
            new_entities.append(
                {
                    "entity_id": entity["entity_id"],
                    "graph_entity_id": match["graph_entity_id"],
                }
            )
        else:
            _append_unique(match["source_entity_ids"], entity["entity_id"])
            _append_unique(match["source_runs"], run["run_id"])
            for alias in [entity["text"], entity["canonical_name"], *entity["aliases"]]:
                if alias and alias not in match["aliases"]:
                    match["aliases"].append(alias)
            match["aliases"].sort()
            match["last_seen_at"] = now
            matched_entities.append(
                {
                    "entity_id": entity["entity_id"],
                    "graph_entity_id": match["graph_entity_id"],
                    "match_reason": reason,
                }
            )

        entity_mapping[entity["entity_id"]] = match["graph_entity_id"]

    graph["aliases"] = []
    for entity in graph["entities"]:
        for alias in sorted(set([entity["canonical_name"], *entity["aliases"]])):
            graph["aliases"].append(
                {
                    "alias": alias,
                    "graph_entity_id": entity["graph_entity_id"],
                }
            )

    for relation in active_relations(run):
        head_graph_id = entity_mapping[relation["head_id"]]
        tail_graph_id = entity_mapping[relation["tail_id"]]
        exists = False
        for existing in graph["relations"]:
            if (
                existing["type"] == relation["type"]
                and existing["head_graph_id"] == head_graph_id
                and existing["tail_graph_id"] == tail_graph_id
            ):
                _append_unique(existing["source_runs"], run["run_id"])
                existing["last_seen_at"] = now
                exists = True
                break
        if exists:
            continue

        relation_record = {
            "relation_id": _next_relation_id(graph),
            "type": relation["type"],
            "head_graph_id": head_graph_id,
            "tail_graph_id": tail_graph_id,
            "source_runs": [run["run_id"]],
            "last_seen_at": now,
        }
        graph["relations"].append(relation_record)
        new_relations.append(relation_record)

    _append_unique(graph["source_runs"], run["run_id"])
    graph["last_updated"] = now
    write_json(GRAPH_PATH, graph)

    run["graph_updates"] = {
        "matched_entities": matched_entities,
        "new_entities": new_entities,
        "new_relations": new_relations,
        "summary": {
            "matched": len(matched_entities),
            "created": len(new_entities),
            "relations_created": len(new_relations),
        },
    }
    return run, graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Update graph memory from a run")
    parser.add_argument("run_json", type=Path)
    args = parser.parse_args()

    run, graph = update_graph_memory(load_run(args.run_json))
    write_run(args.run_json, run)
    print(
        {
            "entities": len(graph["entities"]),
            "relations": len(graph["relations"]),
            "last_updated": graph["last_updated"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
