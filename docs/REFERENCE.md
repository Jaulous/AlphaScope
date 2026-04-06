# Reference

## Purpose
Store stable reference facts needed for implementation and operations.

## When To Update
- Repo structure, env vars, external dependencies, or interfaces change.

## Minimum Sections
- Repository Map
- Runtime and Environment
- External Systems
- Glossary

## Repository Map
- `apps/web/`: Next.js dashboard app and UI composition.
- `apps/web/vercel.json`: frontend-local Vercel config for monorepo deployments.
- `apps/server/`: FastAPI API, scheduler, fetch orchestration, Supabase persistence adapter, and tests.
- `api/`: repository-root Vercel Python entrypoint used for the production backend deployment.
- `packages/quant-core/`: unified quant engine, data providers, universes, indicators, and engine tests.
- `packages/db-types/`: shared TypeScript database and API types.
- `packages/ui/`: shared React UI primitives.
- `supabase/migrations/`: database schema and seed migrations for raw, serving, and fetch-run tables.
- `supabase/migrations/0007_raw_data_layer_v2.sql`: non-breaking Raw V2 schema introduction for landing/audit tables plus canonical raw fact tables.
- `requirements.txt`: repository-root Python dependency manifest for the Vercel backend deployment.
- `vercel.json`: repository-root Vercel cron and Python function bundling config.
- `.python-version`: Vercel backend Python runtime pin.
- `docs/`: maintained project documentation for context, architecture, workflow, decisions, and reference facts.
- `CHANGELOG.md`: high-signal log of important project changes for human and agent backtracking.
- `docs/RAW_DATA_MODEL.md`: detailed raw-layer redesign doc and migration path.
- `STATUS.md`: last verified runtime state.
- `TROUBLESHOOTING.md`: operational debugging guide.

## Runtime and Environment
- Node.js: use `nvm` with Node `v24.14.0` on this machine.
- Package manager: `corepack`-managed `pnpm`, repo packageManager `pnpm@10.6.2`.
- Python: `>=3.11`.
- Monorepo orchestrator: Turborepo.
- Root scripts:
  - `pnpm dev`
  - `pnpm build`
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
- Key env vars:
  - `SUPABASE_URL`
  - `SUPABASE_SECRET_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY` (legacy fallback only)
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
  - `NEXT_PUBLIC_SERVER_URL`
  - `SERVER_HOST`
  - `SERVER_PORT`
  - `SERVER_CORS_ORIGINS`
  - `SCHEDULER_TIMEZONE`
  - `ENGINE_PARALLELISM`
  - `ADMIN_API_KEY`
  - `TRACKING_TOP_TURNOVER_COUNT`
  - `TRACKING_LIMIT_UP_POOL_COUNT`
  - `TRACKING_INCLUDE_SYMBOLS`

## External Systems
- AkShare: primary market data source for snapshots, concept boards, limit-up pool, and stock K-line data.
- Supabase Postgres: system of record for raw datasets, serving snapshots, definitions, board documents, and ingestion run logs.
- FastAPI: backend API surface.
- Next.js: frontend rendering surface.

## Raw Storage Notes
- Raw V1 tables currently used by production ingestion:
  - `raw_market_snapshot_daily`
  - `raw_limit_up_pool_daily`
  - `raw_concept_boards_daily`
  - `raw_stock_kline_daily`
- Raw V2 tables introduced for the next architecture phase:
  - landing/audit:
    - `raw_ingestion_runs`
    - `raw_dataset_batches`
    - `raw_source_payload_rows`
  - canonical raw facts:
    - `raw_trade_calendar`
    - `raw_security_master`
    - `raw_equity_daily_quotes`
    - `raw_equity_daily_limit_events`
    - `raw_concept_board_daily`
    - `raw_concept_board_constituents_daily`
    - `raw_index_daily_quotes`
- Phase 1 runtime now writes a subset of Raw V2 canonical tables:
  - `raw_trade_calendar`
  - `raw_security_master`
  - `raw_equity_daily_quotes`
  - `raw_equity_daily_limit_events`
  - `raw_concept_board_daily`
- Landing/audit tables and the remaining canonical tables are schema-ready but not yet populated by the runtime.
- Indicator computation still reads Raw V1 today; Raw V2 is not yet the canonical runtime read path.

## Glossary
- `raw_* tables`: persisted source-of-truth ingestion tables used to rebuild market context.
- `serving tables`: query-oriented output tables used by the dashboard API.
- `active themes`: theme universe selected from concept board turnover with configurable filtering.
- `tracked equities`: stock universe chosen for dashboard K-line coverage.
- `fetch_runs`: operational log of manual, scheduler, and on-demand ingestion attempts.
- `as_of`: target market date for a given snapshot, which may differ from the current calendar day on non-trading days.
