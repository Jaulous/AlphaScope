# Documentation Index

## Purpose
Single map of project docs for humans and agents.

## When To Update
- A doc is added, removed, renamed, or moved.
- Read order changes.
- The entry layer, core governance chain, or update responsibilities change.

## Entry Layer
Read these before diving into the core project docs:

1. `../README.md`
2. `../SOUL.md`
3. `../AGENTS.md`
4. `./DOCS_INDEX.md`

## Core Read Order
1. `./PRD.md`
2. `./ARCHITECTURE.md`
3. `./RAW_DATA_MODEL.md`
4. `./WORKFLOW.md`
5. `./DECISIONS.md`
6. `./REFERENCE.md`

## Core Files
| File | Purpose | Update Trigger |
| --- | --- | --- |
| `PRD.md` | Product definition, target users, user stories, acceptance criteria, and success metrics. | Product scope, goals, requirements, or priorities change. |
| `ARCHITECTURE.md` | System boundaries, components, data/control flows. | Design, dependencies, interfaces, or infrastructure change. |
| `RAW_DATA_MODEL.md` | Raw-layer structure, table grains, migration intent, and storage contracts. | Raw tables, grains, source preservation strategy, or ingestion-to-raw mappings change. |
| `WORKFLOW.md` | Preferred working patterns, operator/agent pitfall notes, build/test/run/release guidance. | Toolchain, recurring pitfalls, or process guidance change. |
| `DECISIONS.md` | Major technical/product decisions and rationale. | Significant decisions are made or reversed. |
| `REFERENCE.md` | Stable reference facts: repo map, env vars, external systems. | Reference facts change. |

## Optional OSS Files
If this is an open-source repo, also keep these up to date:
- `../CONTRIBUTING.md`
- `../CODE_OF_CONDUCT.md`
- `../SECURITY.md`
- `../SUPPORT.md`

## Supporting Docs
- `../README.md`: human-first project overview and quick start.
- `../SOUL.md`: repo-wide execution rules and response style.
- `../AGENTS.md`: agent entrypoint and required documentation-loading contract.
- `../CHANGELOG.md`: major project change log for backtracking and historical context.
- `../STATUS.md`: last verified runtime snapshot and current operational state.
- `../TROUBLESHOOTING.md`: incident-oriented debugging guidance.
