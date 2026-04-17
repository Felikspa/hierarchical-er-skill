# Web Panel Reference

## Product goal

Provide a compact, professional, local-first review surface for entity-relation extraction runs.

## Required information architecture

- Run history rail
- Original text and chunk view
- Entity and relation result view
- Evidence cards
- Confidence segmentation
- Issue list
- Graph-memory delta summary
- Error-set capture summary
- Review editor

## Interaction rules

- Selecting an entity must highlight its evidence and linked relations.
- Selecting a relation must highlight its head, tail, and evidence.
- Mode tabs must switch between `coarse`, `standard`, and `fine`.
- Filters must support low confidence, conflicts, and edited items.
- Saving review must write a revision JSON and refresh error-case evaluation.

## Visual direction

- Light theme by default.
- Use calm neutrals with one restrained accent color.
- Preserve strong hierarchy with typography, spacing, borders, and subtle motion.
- Optimize for scanability over decoration.

## Data flow

- Read run data from `data/runs/`.
- Read graph memory from `data/graph/graph-memory.json`.
- Read error summaries from `data/errors/`.
- Do not execute extraction in the browser.
- Send review saves to the local Python server, which writes data files.
