# AlphaScope Status

As of `2026-03-08`, this repository is no longer in the original editable-whiteboard shape. It is running as a read-only market dashboard backed by persisted Supabase data.

## Current Product State

- Frontend: read-only dashboard on `http://127.0.0.1:3000`
- Backend: FastAPI on `http://127.0.0.1:8000`
- Data source: AkShare
- System of record: Supabase Postgres
- Storage model: `raw -> compute -> serving`

## Implemented Architecture

1. AkShare raw datasets are fetched by `quant-core` ingestion providers.
2. Raw datasets are written into Supabase `raw_*` tables.
3. `quant-core` rebuilds a synchronized market context from stored raw data.
4. Indicators, active themes, and tracked equities are computed from that stored context.
5. Serving results are written into `daily_indicators`, `daily_themes_volume`, and `stock_kline_daily`.
6. FastAPI serves the latest stored dashboard snapshot to Next.js.

## Raw Tables

- `raw_market_snapshot_daily`
- `raw_limit_up_pool_daily`
- `raw_concept_boards_daily`
- `raw_stock_kline_daily`

## Raw Layer Redesign Status

- The current production runtime still writes the Raw V1 tables listed above and still reads them for indicator computation.
- A Raw V2 schema has now been introduced in [`supabase/migrations/0007_raw_data_layer_v2.sql`](./supabase/migrations/0007_raw_data_layer_v2.sql) and documented in [`docs/RAW_DATA_MODEL.md`](./docs/RAW_DATA_MODEL.md).
- Phase 1 ingestion now also writes part of Raw V2 canonical storage:
  - `raw_trade_calendar`
  - `raw_security_master`
  - `raw_equity_daily_quotes`
  - `raw_equity_daily_limit_events`
  - `raw_concept_board_daily`
- Phase 1 ingestion now also writes landing/audit records for fetched daily datasets:
  - `raw_ingestion_runs`
  - `raw_dataset_batches`
  - `raw_source_payload_rows`
- The runtime read path now prefers canonical Raw V2 reads for:
  - active theme universe
  - tracked equities universe
  - `market_turnover`
  - `decliner_count`
  - `active_capital_ratio`
  - `up_limit_count`
  - `down_limit_count`
  - `highest_board`
  - `n_shape_limit_up_count` for current and historical limit-event inputs
- When canonical Raw V2 rows are unavailable, the runtime falls back to deterministic Raw V1-to-V2 field mapping so serving generation stays stable during the migration.
- Raw V2 adds:
  - landing/audit tables for original AkShare payload preservation
  - canonical domain-grain raw fact tables designed to support a future indicator library of roughly `100+` metrics
- Ingestion has not yet been fully cut over to Raw V2, so the system is currently in dual-write plus partial-read transition rather than full Raw V2 operation.

## Serving Tables

- `daily_indicators`
- `daily_themes_volume`
- `stock_kline_daily`
- `indicator_definitions`
- `fetch_runs`

## Ingestion Safety Rules

- Scheduler runs are skipped on non-trading days.
- Manual and on-demand fetches on non-trading days target the latest confirmed trading day.
- Raw sources are retried with backoff before failure is declared.
- If a raw source still fails, stored raw data for the same trading day is reused when available.
- If critical raw sources are unavailable but a correct serving snapshot already exists, the serving snapshot is preserved and not overwritten.
- Every fetch attempt is recorded in `fetch_runs`.

## Verified Runtime Snapshot

Verified locally on `2026-03-08`:

- `GET /api/health`: success
- `GET /api/dashboard/latest`: success
- latest `as_of`: `2026-03-06`
- latest indicator count: `7`
- latest theme count: `20`
- latest tracked stock count: `40`
- latest fetch run status: `success_with_warnings`
- latest fetch target date: `2026-03-06`

That warning state is expected on a Sunday. The system correctly backfilled the latest trading day instead of writing a non-trading-day snapshot.

## Current UI State

- The dashboard includes:
  - computed market indicator cards
  - active theme ranking
  - tracked equity watchlist
  - ingestion status card with per-source statuses from `fetch_runs`
- The UI is not an editing surface and no longer depends on manual canvas operations.

## Known Limitations

- AkShare source stability is still the main external risk. Some sources can be slow or intermittently fail.
- Stock rows currently have incomplete name fields for some symbols because the raw K-line source does not always provide normalized names consistently.
- Project docs and runtime currently assume Supabase is required. There is no alternate local Postgres adapter.

## Recommended Operational Checks

1. `curl http://127.0.0.1:8000/api/health`
2. `curl http://127.0.0.1:8000/api/dashboard/latest`
3. Inspect the `latest_run` block in the dashboard response.
4. Check `fetch_runs` when validating scheduler behavior or source failures.

## Immediate Next Work

- Add a historical ingestion runs page or endpoint, not only the latest run summary.
- Normalize tracked stock names in the serving layer.
- Add stronger source-level observability for AkShare latency and fallback usage.
- Expand Raw V2 beyond event/quote/board facts by introducing canonical replacements for the remaining Raw V1-only stock K-line history path.
