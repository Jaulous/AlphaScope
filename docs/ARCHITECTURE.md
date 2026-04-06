# Architecture

## Purpose
Explain how the system is structured and why.

## When To Update
- Components, interfaces, data flows, infra, or runtime boundaries change.

## Minimum Sections
- System Context
- Key Components
- Data and Control Flow
- Quality Attributes
- Known Risks and Tradeoffs

## System Context
- External source: AkShare provides market snapshot, limit-up pool, concept board, and stock K-line datasets.
- Persistence layer: Supabase Postgres stores both raw ingestion tables and serving tables.
- Backend boundary: `apps/server` owns API routes, scheduled/manual fetch orchestration, and Supabase persistence.
- Quant boundary: `packages/quant-core` owns data provider adapters, universe selection, indicator registry, and execution engine.
- Frontend boundary: `apps/web` renders a read-only indicator observation surface from backend APIs.

## Key Components
- `apps/server/src/limitboard_server/api/routes.py`: FastAPI routes for health, dashboard snapshot, definitions, tracked stock history, and fetch trigger.
- `apps/server/src/limitboard_server/tasks/fetch_data.py`: canonical daily fetch pipeline. Resolves target trading day, fetches/reuses raw sources, preserves existing serving snapshots when critical raw data is missing, computes indicators, and records fetch runs.
- `apps/server/src/limitboard_server/db/supabase_store.py`: persistence adapter for raw tables, serving tables, indicator definitions, and `fetch_runs`.
- `apps/server/src/limitboard_server/scheduler.py`: scheduled execution wrapper around `run_daily_fetch()` plus startup backfill for missed trading days in long-running deployments.
- `apps/web/vercel.json`: frontend-local Vercel config used when the Next.js app is deployed from the monorepo root with root directory `apps/web`.
- `api/index.py`, repository-root `requirements.txt`, and repository-root `vercel.json`: Vercel backend entrypoint, dependency manifest, cron registration, and `/api* -> /api/index.py` rewrite config for the production Python deployment.
- `packages/quant-core/src/quant_core/engine.py`: unified execution engine that builds indicator requirements, selects active themes and tracked equities, and computes results from a synchronized context.
- `packages/quant-core/src/quant_core/universe/active_themes.py`: active theme selection policy. This is the place for rolling-window, ranking, persistence, or expiration logic changes.
- `packages/quant-core/src/quant_core/universe/tracked_equities.py`: tracked stock universe logic for dashboard K-line coverage.
- `apps/web/app/page.tsx` and `apps/web/components/dashboard-shell.tsx`: dashboard presentation of indicators, active themes, tracked stocks, and ingestion status.
- `supabase/migrations/0007_raw_data_layer_v2.sql` and [`docs/RAW_DATA_MODEL.md`](./RAW_DATA_MODEL.md): the new raw-layer target architecture for large-scale indicator growth.

## Data and Control Flow
1. In a long-running deployment, backend startup kicks off a background backfill job that compares stored serving dates against the trade calendar and fills missed trading days up to the latest expected scheduled market date without blocking API readiness.
2. In a self-hosted deployment, the embedded scheduler triggers daily fetches after market close.
3. In a Vercel backend deployment, Vercel Cron Jobs trigger `/api/cron/fetch`, which backfills missed trading days through the FastAPI app.
4. The backend resolves the current reference date and maps it to the latest valid market date.
5. Raw datasets are fetched from AkShare with retry and selective reuse of already stored raw data for the same trading day.
6. Current runtime persists into Raw V1 tables (`raw_market_snapshot_daily`, `raw_limit_up_pool_daily`, `raw_concept_boards_daily`, `raw_stock_kline_daily`).
7. Raw V2 is the target shape: a landing/audit layer (`raw_ingestion_runs`, `raw_dataset_batches`, `raw_source_payload_rows`) plus canonical raw domain tables (`raw_trade_calendar`, `raw_security_master`, `raw_equity_daily_quotes`, `raw_equity_daily_limit_events`, `raw_concept_board_daily`, `raw_concept_board_constituents_daily`, `raw_index_daily_quotes`).
8. Phase 1 runtime now dual-writes part of Raw V2 alongside Raw V1: trade calendar, security master, equity daily quotes, daily limit events, and concept board daily facts are written best-effort without blocking serving generation.
9. For fetched daily datasets (`market_snapshot`, `limit_up_pool`, `concept_boards`), the runtime also writes Raw V2 landing/audit records into `raw_ingestion_runs`, `raw_dataset_batches`, and `raw_source_payload_rows`.
10. `quant-core` builds an execution plan from enabled indicator definitions, loads any needed history, and reconstructs a single `IndicatorContext`.
11. During the Raw V2 migration, the runtime now tries to read canonical Raw V2 tables back into the execution context (`raw_equity_daily_quotes`, `raw_equity_daily_limit_events`, `raw_concept_board_daily`) and only falls back to Raw V1 field mapping when those reads are unavailable.
12. The active theme universe is selected first, then the tracked equities universe, then indicator computation runs against the synchronized context.
13. The first migrated read-path batch now prefers Raw V2 for:
  - active theme universe
  - tracked equities universe
  - `market_turnover`
  - `decliner_count`
  - `active_capital_ratio`
  - `up_limit_count`
  - `down_limit_count`
14. Serving outputs are persisted into `daily_indicators`, `daily_themes_volume`, and `stock_kline_daily`. Fetch metadata is stored in `fetch_runs`.
15. `GET /api/dashboard/latest` reads the latest persisted dashboard snapshot first and serves it immediately when available. It only falls back to on-demand fetch when there is no usable stored snapshot, so the customer read path does not block on AkShare or a full recompute.
16. Dashboard snapshot assembly is bounded to the latest snapshot's indicator keys, theme names, and tracked stock symbols instead of scanning every historical stock row, so the read path stays responsive as data grows.
17. Next.js renders the dashboard from the API response and does not compute market state on the client.

## Quality Attributes
- Determinism: market snapshot, universe selection, and indicators share one aligned daily context.
- Reliability: retries, raw-data reuse, and serving snapshot preservation reduce the chance of empty dashboards on partial source failure.
- Operability: `fetch_runs` records latest trigger status, warnings, per-source outcomes, and counts for debugging.
- Portability: the unified `quant-core` layout is closer to a Lean-style quant engine than scattered ad hoc scripts.
- Simplicity: storage and serving currently standardize on Supabase instead of supporting multiple persistence backends.

## Known Risks and Tradeoffs
- AkShare schema drift or latency remains the main external reliability risk.
- Supabase is a hard dependency for current dashboard serving; local-only fallback storage is not implemented.
- Vercel cron timing is UTC and may be imprecise on Hobby, so exact post-close execution timing is weaker there than on a self-hosted scheduler.
- Legacy naming still exists in some package/module identifiers (`limitboard_*`), even though the canonical product is AlphaScope.
- Stock K-line name normalization is still imperfect for some symbols because upstream raw data is inconsistent.
- Multiprocessing in `quant-core` improves throughput for larger indicator sets but increases runtime complexity and requires module-safe entrypoints.
- The current production runtime is only partially migrated: a first indicator/universe batch now prefers Raw V2 reads, but the full engine has not yet cut over and still relies on Raw V1 compatibility fallback for the remaining metrics.
