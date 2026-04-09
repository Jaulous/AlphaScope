Before doing any work, read and follow `./SOUL.md`.

# AGENTS

## Role
This file is the agent entrypoint for this repository.

## Required Read Order
1. `./SOUL.md`
2. `./docs/DOCS_INDEX.md`
3. Every core file listed in `./docs/DOCS_INDEX.md`, in order.
4. Read `./STATUS.md` before debugging, deployment validation, or production-facing runtime work.
5. Read `./TROUBLESHOOTING.md` before incident or hotfix work.

## Trigger Contract
When an agent reads this file, it must:
- Load the current product definition, architecture, raw data model, workflow guidance, decisions, and reference facts from docs before editing code.
- Treat `./docs/*.md` as the maintained source of truth for repo behavior and operating constraints.
- Update docs in the same change when architecture, workflow, runtime contracts, or operating guidance changes.
- Update `./docs/RAW_DATA_MODEL.md` in the same change when raw tables, grains, ingestion-to-raw mappings, or storage contracts change.
- Update `./CHANGELOG.md` in the same change whenever an important milestone is completed, and record the entry with an exact timestamp.

## Project-Specific Notes
- AlphaScope is a quant indicator observation platform for short-term market analysis, not an editable whiteboard product.
- The canonical system shape is `AkShare -> raw Supabase tables -> quant-core -> serving tables -> FastAPI -> Next.js`, with indicator computation as the product center.
- `quant-core` follows a unified Lean-style architecture: `ingestion + universe + indicators + engine`.
- Active theme policy changes belong in `packages/quant-core/src/quant_core/universe/active_themes.py`, not in indicator implementations.
- Tracked equity coverage is controlled from `packages/quant-core/src/quant_core/universe/tracked_equities.py` and the tracking env vars.
- Local Node usage on this machine must prefer `nvm` Node `v24.14.0` and `corepack`-managed `pnpm`.
- Git workflow is branch-first: never push directly to `main`; major completed changes must be verified and then pushed to a remote feature branch.
- Important milestones are defined in `./docs/WORKFLOW.md`; they are based on changed system facts, not agent judgment by feel, and the same threshold applies to Git maintenance and `CHANGELOG.md` updates.
- Important project changes must be traceable in `CHANGELOG.md`.
