# AlphaScope Status

As of `2026-04-09`, this repository is no longer in the original editable-whiteboard shape. It is running as a read-only market dashboard backed by persisted Supabase data.

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

- `raw_ingestion_runs`
- `raw_dataset_batches`
- `raw_source_payload_rows`
- `raw_trade_calendar`
- `raw_security_master`
- `raw_equity_daily_quotes`
- `raw_equity_daily_limit_events`
- `raw_concept_board_daily`
- `raw_concept_board_constituents_daily`
- `raw_index_daily_quotes`

## Raw Layer Status

- The runtime is now written against Raw V2 only.
- The schema introduction lives in [`supabase/migrations/0007_raw_data_layer_v2.sql`](./supabase/migrations/0007_raw_data_layer_v2.sql).
- The V1-to-V2 backfill plus drop step lives in [`supabase/migrations/0008_raw_v2_cutover.sql`](./supabase/migrations/0008_raw_v2_cutover.sql).
- The production Supabase project was cut over to Raw V2 on `2026-04-09`; the legacy Raw V1 raw tables were backfilled and then dropped.
- Runtime writes canonical Raw V2 storage for:
  - `raw_trade_calendar`
  - `raw_security_master`
  - `raw_equity_daily_quotes`
  - `raw_equity_daily_limit_events`
  - `raw_concept_board_daily`
  - `raw_concept_board_constituents_daily`
  - `raw_index_daily_quotes`
- Daily concept-board-constituent ingestion is bounded to the top 100 ranked concept boards for the day, and each board fetch runs in an isolated subprocess with a hard timeout so one stalled upstream call cannot block the whole daily job.
- Runtime also writes landing/audit records for fetched daily datasets:
  - `raw_ingestion_runs`
  - `raw_dataset_batches`
  - `raw_source_payload_rows`
- The runtime read path uses canonical Raw V2 reads for:
  - active theme universe
  - tracked equities universe
  - `market_turnover`
  - `decliner_count`
  - `active_capital_ratio`
  - `up_limit_count`
  - `down_limit_count`
  - `highest_board`
  - `n_shape_limit_up_count` for current and historical limit-event inputs
- Tracked-stock and limit-event stock history now rebuild from `raw_equity_daily_quotes`.
- Concept board constituents remain best-effort because the upstream AkShare constituent endpoint can intermittently disconnect or stall.

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

## Verified Remote Raw Snapshot

Verified against the production Supabase project on `2026-04-09`:

- Raw V1 raw tables are gone:
  - `raw_market_snapshot_daily`
  - `raw_limit_up_pool_daily`
  - `raw_concept_boards_daily`
  - `raw_stock_kline_daily`
- Raw V2 / landing counts:
  - `raw_ingestion_runs`: `105`
  - `raw_dataset_batches`: `105`
  - `raw_source_payload_rows`: `164912`
  - `raw_trade_calendar`: `37`
  - `raw_security_master`: `11335`
  - `raw_equity_daily_quotes`: `127804`
  - `raw_equity_daily_limit_events`: `1219`
  - `raw_concept_board_daily`: `11224`
  - `raw_index_daily_quotes`: `6`
  - `raw_concept_board_constituents_daily`: `0`

The remaining zero-count table is still `raw_concept_board_constituents_daily`. Its upstream source remains the slowest AkShare dependency, so that dataset is still treated as best-effort even after the runtime was bounded with per-board subprocess timeouts.

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
- Stabilize concept-board-constituent ingestion with stronger retry and fallback handling.
