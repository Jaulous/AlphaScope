# Documentation Index

## Purpose
Single map of project docs for humans and agents.

## When To Update
- A doc is added, removed, renamed, or moved.
- Read order changes.

## Core Read Order
1. `./PROJECT_CONTEXT.md`
2. `./ARCHITECTURE.md`
3. `./WORKFLOW.md`
4. `./DECISIONS.md`
5. `./REFERENCE.md`

## Core Files
| File | Purpose | Update Trigger |
| --- | --- | --- |
| `PROJECT_CONTEXT.md` | Problem, goals, scope, constraints. | Product scope or goals change. |
| `ARCHITECTURE.md` | System boundaries, components, data/control flows. | Design, dependencies, interfaces, or infrastructure change. |
| `WORKFLOW.md` | Build/test/run/release commands and quality gates. | Toolchain or process changes. |
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
- `./PRD.md`: current product requirements for the indicator observation platform.
- `../STATUS.md`: last verified runtime snapshot and current operational state.
- `../TROUBLESHOOTING.md`: incident-oriented debugging guidance.
