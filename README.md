# LimitBoard

LimitBoard is a read-only short-term market dashboard built as a Turborepo monorepo. It uses a unified `quant-core` engine to pull raw market data from AkShare, persist the raw layer into Supabase, compute serving indicators from the stored raw data, and present the result as a backend-driven display surface instead of an editable whiteboard.

## Documentation

- [`STATUS.md`](./STATUS.md): current verified project state and operational notes
- [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md): runtime troubleshooting guide

## Product Direction

- The frontend is a display dashboard, not an editing canvas.
- All metric cards, theme rankings, and tracked equities are computed by the backend.
- AkShare is the primary live market data source.
- Supabase is the system of record for dashboard data.

## Stack

- Monorepo: Turborepo + pnpm
- Frontend: Next.js 15, TypeScript, Tailwind, shared UI components
- Backend: FastAPI, APScheduler, AkShare, pandas, numpy, supabase-py
- Quant core: unified `ingestion + universe + indicators + engine`
- Storage: Supabase Postgres with separate raw and serving layers

## Runtime Model

- `AkShare -> raw tables -> quant-core -> serving tables -> FastAPI -> Next.js`
- Supabase credentials are required in `.env`
- The backend persists raw market snapshots before computing indicators
- Requests are evaluated against the latest market date, so weekends fall back to the most recent trading day
- If one AkShare source is blocked, the fetch job retries first, then reuses stored raw data for the same trading day when available
- Existing correct serving data is preserved if critical raw sources are missing

## Current Verified State

Verified on `2026-03-08`:

- frontend and backend both start locally
- `dashboard/latest` returns stored data successfully
- latest persisted snapshot date is `2026-03-06`
- current verified serving volume is `7` indicators, `20` active themes, and `40` tracked stock entries
- the dashboard now exposes the latest ingestion run and per-source statuses from `fetch_runs`

## Monorepo Layout

```text
apps/
  web/                 Next.js read-only market dashboard
  server/              FastAPI API and scheduler
packages/
  quant-core/          Unified quant engine and AkShare ingestion
  db-types/            Shared API / DB typings
  ui/                  Shared UI primitives
supabase/migrations/   Persistence schema
```

## Storage Layout

### Raw tables

- `raw_market_snapshot_daily`
- `raw_limit_up_pool_daily`
- `raw_concept_boards_daily`
- `raw_stock_kline_daily`

### Serving tables

- `daily_indicators`
- `daily_themes_volume`
- `stock_kline_daily`
- `indicator_definitions`
- `board_documents`
- `fetch_runs`

## Quick Start

### 1. Load the project Node toolchain

```bash
nvm use
corepack enable
corepack prepare pnpm@10.6.2 --activate
```

### 2. Install frontend dependencies

```bash
pnpm install
```

### 3. Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/quant-core -e apps/server
```

### 4. Create `.env`

Supabase credentials are required:

```bash
cp .env.example .env
```

### 5. Start the app

```bash
pnpm dev
```

Open `http://localhost:3000`.

## Environment Variables

### Required

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `SUPABASE_BOARD_SLUG`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `SERVER_HOST`
- `SERVER_PORT`
- `SERVER_CORS_ORIGINS`
- `SCHEDULER_TIMEZONE`
- `ENGINE_PARALLELISM`
- `TRACKING_TOP_TURNOVER_COUNT`
- `TRACKING_LIMIT_UP_POOL_COUNT`
- `TRACKING_INCLUDE_SYMBOLS`

## API Overview

### `GET /api/health`

Service health and storage mode.

### `GET /api/dashboard/latest`

Returns the dashboard snapshot.

- Reads from persisted Supabase data
- If the latest market date is missing, the backend triggers a fetch, persists the result, then serves the stored snapshot
- If the fetch can only compute partial data, that partial raw and serving result is what gets persisted and served

### `GET /api/definitions`

Returns the active indicator definitions.

### `GET /api/stocks/{symbol}/kline`

Returns tracked stock daily K-line data.

### `POST /api/fetch/run`

Runs the daily fetch pipeline manually.

- Results are persisted into Supabase
- On non-trading days it targets the latest confirmed trading day and records a warning instead of writing an invalid date

## Data Flow

1. FastAPI receives a dashboard request.
2. The backend reads persisted serving snapshots from Supabase first.
3. If the latest market date is missing, the backend runs a fetch job.
4. The fetch job resolves the latest market date and pulls AkShare raw datasets.
5. Raw datasets are written into the `raw_*` tables.
6. `quant-core` rebuilds the market context from the stored raw tables.
7. Indicators, active themes, and tracked equities are computed from that stored context.
8. Serving results are written into `daily_indicators`, `daily_themes_volume`, and `stock_kline_daily`.
9. The frontend renders a read-only dashboard from the persisted serving data.

## Ingestion Safety

- Scheduler runs are skipped on non-trading days and logged as `skipped_non_trading_day`.
- Manual and on-demand runs on non-trading days backfill the latest trading day instead of fabricating a new one.
- Raw sources are retried with backoff before failure is declared.
- If a raw source still fails, the job reuses stored raw data for the same trading day when that data already exists.
- If critical raw data is unavailable and a serving snapshot already exists, that serving snapshot is preserved and not overwritten by partial data.
- Every ingestion attempt is recorded in `fetch_runs`, and the dashboard exposes the latest run status plus per-source outcomes.

## Quant Architecture

LimitBoard uses a unified Lean-style `quant-core` architecture:

- ingestion
- universe
- indicators
- engine

This keeps daily execution deterministic and avoids splitting market snapshot, theme selection, and indicator logic across unrelated layers.

## Adding Indicators

1. Create a new Python file in `packages/quant-core/src/quant_core/indicators/`.
2. Subclass `BaseIndicator` and define `indicator_key`.
3. Implement `compute(self, context, definition)`.
4. Add a matching row to `indicator_definitions` if you want custom config.

## What Changed From The Old Product Shape

- The frontend is no longer treated as a whiteboard.
- The page no longer depends on user-edited canvas operations.
- The primary job of the UI is to present backend-computed market state.
- Supabase is required for persistence and serving dashboard data.
