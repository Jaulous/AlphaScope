# Changelog

## Purpose
Record important project changes so humans and agents can quickly reconstruct what changed, why it mattered, and when it landed.

## Update Rule
- Add an entry whenever a major product, architecture, deployment, data-pipeline, or customer-facing UX change is completed.
- Update this file in the same change set as the underlying implementation.
- Keep entries concise and factual. This is a high-signal project log, not a full commit mirror.

## Entries

### 2026-04-06
- Hardened production dashboard loading and snapshot reads.
- Changed `GET /api/dashboard/latest` to serve stored snapshots first instead of blocking customer reads on AkShare freshness checks or on-demand recompute.
- Reduced dashboard snapshot query cost by reading only the latest snapshot's indicator keys, active theme names, and tracked stock symbols, then loading bounded history for those entities.
- Fixed `stock_kline_daily` time-window filtering to use `Asia/Shanghai` market-day boundaries so tracked stocks render correctly in production.
- Split frontend loading, timeout, empty, and unavailable states so the page no longer shows a misleading wall of empty panels while data is still loading or when upstream reads fail.
- Redeployed both Vercel projects and verified the production homepage shows indicators, themes, and tracked stocks.

### 2026-03-30
- Restored the production data pipeline on Vercel.
- Standardized backend Supabase server credentials around `SUPABASE_SECRET_KEY` with compatible Python client support.
- Fixed Vercel backend routing and frontend API proxying so `/api/dashboard/latest` resolves through the deployed backend.
- Sanitized `NaN` values before Supabase writes and moved startup backfill off the blocking startup path.

### 2026-03-29
- Deployed AlphaScope to Vercel as two projects: `alphascope-web` and `alphascope-api`.
- Added repository-root Vercel backend entrypoint and production routing config.
- Brought monorepo Next.js deployment into a stable Vercel shape.

### 2026-03-16
- Repositioned AlphaScope as a quant indicator observation platform instead of an editable whiteboard.
- Established the canonical architecture as `AkShare -> raw Supabase -> quant-core -> serving tables -> FastAPI -> Next.js`.
- Rebuilt the project documentation system around `SOUL.md`, `AGENTS.md`, and maintained docs in `docs/`.
