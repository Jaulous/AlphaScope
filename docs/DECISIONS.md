# Decisions

## Purpose
Record important decisions with rationale and impact.

## When To Update
- A significant technical or product decision is made, changed, or rolled back.

## Minimum Sections
- Decision Log
- Decision Entry Template

## Decision Log
| ID | Date | Status | Decision | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| D-001 | 2026-03-15 | Accepted | Use a unified `quant-core` architecture for ingestion, universes, indicators, and engine execution | Daily market computations need one synchronized context instead of fragmented scripts | Indicator and universe logic share a deterministic execution model |
| D-002 | 2026-03-15 | Accepted | Position AlphaScope as a quant indicator observation platform, not an editable whiteboard | Indicator computation and synchronized market context are the core product value; editable canvas behavior diluted the product shape | UI is a read-only observation surface and whiteboard behavior is non-canonical |
| D-003 | 2026-03-15 | Accepted | Persist both raw and serving market data in Supabase | Stored raw inputs enable reuse, reproducibility, and safer recovery from partial source failures | Dashboard serving depends on Supabase and the `raw_*` plus serving tables |
| D-004 | 2026-03-15 | Accepted | Standardize the repo on `SOUL.md`, `AGENTS.md`, and `docs/` core documents | Humans and agents need one predictable read path and maintained source of truth | Documentation upkeep becomes part of normal repo changes |
| D-005 | 2026-04-06 | Accepted | Redesign the raw layer as `landing/audit + canonical raw facts` instead of keeping only a few indicator-specific raw tables | A future library of `100+` indicators needs broad source preservation and stable domain-grain raw tables, not a narrow cache shaped around the first dashboard metrics | Raw V2 becomes the target schema; current Raw V1 tables are transitional until ingestion is cut over |
| D-006 | 2026-04-09 | Accepted | Evolve AlphaScope's next phase into a research-engine monitoring and decision dashboard with a dashboard entrypoint, not a hypothesis-workbench-first product | The current raw-data and `quant-core` foundation already makes indicator computation the durable advantage, so the next product constraint is to optimize for pre-market planning, post-market review, and cross-day tracking instead of richer editing surfaces | Future iteration prioritizes rapid indicator definition, computation, combination, validation, and basic display over heavy UI/editor features |

## Decision Entry Template
- **ID**: `D-XXX`
- **Date**: `YYYY-MM-DD`
- **Status**: Proposed / Accepted / Superseded
- **Decision**: One sentence.
- **Rationale**: Why this is the best current choice.
- **Impact**: What changes because of this decision.
- **Supersedes**: Optional, older decision ID.
