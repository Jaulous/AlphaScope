# Changelog

## Purpose
Record important project changes so humans and agents can quickly reconstruct what changed, why it mattered, and when it landed.

## Update Rule
- Add an entry whenever a major product, architecture, deployment, data-pipeline, or customer-facing UX change is completed.
- Update this file in the same change set as the underlying implementation.
- Every entry header must include an exact timestamp in ISO 8601 form with timezone offset, for example `2026-04-06T18:02:00+08:00`.
- Keep entries concise and factual. This is a high-signal project log, not a full commit mirror.

## Entries

### 2026-04-06T21:33:23+08:00
- Extended the Raw V2 read migration to the remaining limit-event-driven indicators by moving `highest_board` and the limit-event parts of `n_shape_limit_up_count` onto canonical Raw V2 datasets.
- Added historical Raw V2 limit-event reads so `n_shape_limit_up_count` no longer depends on Raw V1 limit-up-pool history for prior-limit detection.
- Hardened `n_shape_limit_up_count` against sparse K-line schemas and timezone mismatches during historical comparisons.

### 2026-04-06T21:28:27+08:00
- Moved the first computation batch off Raw V1-only reads by teaching the runtime to load canonical Raw V2 quote, limit-event, and concept-board tables back into the execution context.
- Migrated the active-theme universe, tracked-equities universe, and five base indicators to prefer Raw V2 data with deterministic Raw V1 compatibility fallback when canonical rows are unavailable.
- Added quant-core tests that assert indicators and universe selection really consume Raw V2 datasets instead of only preserving the old market-snapshot path.

### 2026-04-06T21:00:40+08:00
- Extended the Raw V2 transition beyond canonical fact dual-write by adding landing/audit writes for fetched daily datasets.
- Market snapshot, limit-up pool, and concept-board fetches now record `raw_ingestion_runs`, `raw_dataset_batches`, and `raw_source_payload_rows` alongside their normalized raw tables.
- Kept the migration safe: Raw V1 remains the runtime read path for indicator computation, while landing/audit persistence failures only emit warnings and do not block serving generation.

### 2026-04-06T20:55:23+08:00
- Started the Raw V2 runtime refactor by extending the daily fetch pipeline to dual-write core canonical raw tables while preserving the existing Raw V1 and serving path.
- Added best-effort runtime writes for `raw_trade_calendar`, `raw_security_master`, `raw_equity_daily_quotes`, `raw_equity_daily_limit_events`, and `raw_concept_board_daily` so the new raw architecture begins accumulating usable data immediately.
- Added backend tests for the new Raw V2 quote and limit-event persistence logic and updated architecture/status docs to reflect the transition state accurately.

### 2026-04-06T20:44:03+08:00
- Redesigned the raw-layer target architecture to support a future indicator library on the order of `100+` metrics instead of keeping only a few indicator-specific raw tables.
- Introduced a non-breaking Raw V2 schema with landing/audit tables for original AkShare payload preservation plus canonical raw fact tables for trade calendar, security master, daily equity quotes, limit events, boards, constituents, and indexes.
- Documented the transition state explicitly: production still runs on Raw V1 ingestion, while Raw V2 is now the target schema and migration path.

### 2026-04-06T19:53:03+08:00
- Redesigned the serving metrics experience toward a market-terminal style using TradingView's chart-and-panel density and Polymarket's market-row structure as visual references.
- Reworked the core indicator rows into a continuous terminal panel with richer metadata, state readouts, and a dedicated right-side market-readout column instead of plain stacked cards.
- Upgraded the per-indicator chart controls and top monitor chips so the full dashboard reads like a trading surface rather than a generic BI board.

### 2026-04-06T19:35:49+08:00
- Corrected the serving-metrics homepage layout from a horizontal rail to a stacked one-row-per-indicator list while preserving the existing dark dashboard visual language.
- Added per-indicator trend panels with explicit zoom-in, zoom-out, reset controls, plus an ECharts slider for detailed history inspection.
- Removed the remaining horizontal-rail product copy so the page structure now matches the intended monitoring workflow.

### 2026-04-06T18:26:08+08:00
- Restructured the homepage around four clearer layers while preserving the existing dark dashboard language: top-core monitor chips, runtime strip, horizontally scrollable serving-metrics rail, and theme tracking block.
- Replaced the old split `core metrics / additional metrics` stack with a single horizontally scrollable indicator rail so future serving-layer line-chart indicators can scale without breaking page height.
- Kept tracked equities as a separate lower module and retained the current visual system instead of introducing a new theme.

### 2026-04-06T18:02:00+08:00
- Standardized the changelog format on exact timestamps instead of date-only entries.
- Required future important-change entries to record precise local time with timezone offset for reliable backtracking.

### 2026-04-06T15:14:16+08:00
- Hardened production dashboard loading and snapshot reads.
- Changed `GET /api/dashboard/latest` to serve stored snapshots first instead of blocking customer reads on AkShare freshness checks or on-demand recompute.
- Reduced dashboard snapshot query cost by reading only the latest snapshot's indicator keys, active theme names, and tracked stock symbols, then loading bounded history for those entities.
- Fixed `stock_kline_daily` time-window filtering to use `Asia/Shanghai` market-day boundaries so tracked stocks render correctly in production.
- Split frontend loading, timeout, empty, and unavailable states so the page no longer shows a misleading wall of empty panels while data is still loading or when upstream reads fail.
- Redeployed both Vercel projects and verified the production homepage shows indicators, themes, and tracked stocks.

### 2026-03-30T12:09:30+08:00
- Restored the production data pipeline on Vercel.
- Standardized backend Supabase server credentials around `SUPABASE_SECRET_KEY` with compatible Python client support.
- Fixed Vercel backend routing and frontend API proxying so `/api/dashboard/latest` resolves through the deployed backend.
- Sanitized `NaN` values before Supabase writes and moved startup backfill off the blocking startup path.

### 2026-03-29T17:30:35+08:00
- Deployed AlphaScope to Vercel as two projects: `alphascope-web` and `alphascope-api`.
- Added repository-root Vercel backend entrypoint and production routing config.
- Brought monorepo Next.js deployment into a stable Vercel shape.

### 2026-03-08T20:06:47+08:00
- Repositioned AlphaScope as a quant indicator observation platform instead of an editable whiteboard.
- Established the canonical architecture as `AkShare -> raw Supabase -> quant-core -> serving tables -> FastAPI -> Next.js`.
- Rebuilt the project documentation system around `SOUL.md`, `AGENTS.md`, and maintained docs in `docs/`.
