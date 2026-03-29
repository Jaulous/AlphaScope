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

## Decision Entry Template
- **ID**: `D-XXX`
- **Date**: `YYYY-MM-DD`
- **Status**: Proposed / Accepted / Superseded
- **Decision**: One sentence.
- **Rationale**: Why this is the best current choice.
- **Impact**: What changes because of this decision.
- **Supersedes**: Optional, older decision ID.
