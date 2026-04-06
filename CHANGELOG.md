# Changelog

## Purpose
Record important project changes so humans and agents can quickly reconstruct what changed, why it mattered, and when it landed.

## Update Rule
- Add an entry whenever a major product, architecture, deployment, data-pipeline, or customer-facing UX change is completed.
- Update this file in the same change set as the underlying implementation.
- Every entry header must include an exact timestamp in ISO 8601 form with timezone offset, for example `2026-04-06T18:02:00+08:00`.
- Keep entries concise and factual. This is a high-signal project log, not a full commit mirror.

## Entries

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
