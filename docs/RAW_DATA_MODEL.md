# Raw Data Model

## Purpose
Define a raw-layer architecture that can support a large future indicator library without repeatedly reshaping storage around a handful of current metrics.

## When To Update
- A raw table is added, removed, renamed, or has its grain changed.
- Ingestion starts preserving a new source payload shape or stops writing an old one.
- Runtime reads switch to a different canonical raw table or storage contract.
- A migration changes the Raw V2 schema, cutover path, or backfill assumptions.

## Why The Current Raw Layer Is Not Enough
- The current raw layer only stores four handpicked datasets: market snapshot, limit-up pool, concept boards, and a partial stock K-line subset.
- `raw_stock_kline_daily` is not a true market-wide raw history table. It only backfills a small tracked-symbol subset chosen by the current dashboard universe.
- The current tables are already normalized toward the first batch of indicators instead of preserving AkShare responses broadly enough for future reuse.
- There is no landing/audit layer that stores the original fetched records and fetch metadata in a replayable way.
- There is no canonical raw representation for common quant domains such as trade calendar, security master, index daily bars, board constituents, or full-market daily quotes.

## Design Goal
Support roughly `100+` daily indicators across market breadth, momentum, volatility, liquidity, leadership, board structure, sector rotation, and regime classification without redesigning raw storage for every new metric.

## Design Principles
- Preserve source truth: keep the original AkShare records available in a landing layer.
- Normalize by domain grain: one canonical table per stable analytical grain.
- Separate raw from serving: raw tables should not be shaped around the current dashboard only.
- Favor append-or-upsert daily facts over ad hoc JSON blobs scattered across serving tables.
- Keep the schema China-A-share-first, but extensible to indexes, ETFs, and future asset groups.

## Raw V2 Shape

### 1. Landing / Audit Layer
This layer stores fetch metadata and original payload rows with minimal interpretation.

#### `raw_ingestion_runs`
- Grain: one row per dataset fetch attempt.
- Purpose: operational audit, replay trace, source failure analysis.
- Key fields:
  - `id`
  - `trigger`
  - `dataset_key`
  - `source_name`
  - `market`
  - `as_of_date`
  - `request_params`
  - `status`
  - `row_count`
  - `error_message`
  - `started_at`
  - `finished_at`
  - `metadata`

#### `raw_dataset_batches`
- Grain: one row per fetched dataset batch persisted into raw storage.
- Purpose: identify the exact dataset snapshot used to produce canonical raw facts.
- Key fields:
  - `id`
  - `run_id`
  - `dataset_key`
  - `source_name`
  - `source_endpoint`
  - `market`
  - `as_of_date`
  - `snapshot_time`
  - `fetch_params`
  - `column_names`
  - `record_count`
  - `payload_sha256`
  - `metadata`

#### `raw_source_payload_rows`
- Grain: one row per original AkShare record inside a batch.
- Purpose: preserve source truth even when the normalized schema later changes.
- Key fields:
  - `batch_id`
  - `row_no`
  - `natural_key`
  - `payload`
  - `created_at`

### 2. Canonical Raw Facts Layer
This layer converts the landing data into stable, analysis-friendly raw facts.

#### `raw_trade_calendar`
- Grain: `market + trade_date`
- Supports:
  - market-day alignment
  - gap detection
  - startup backfill logic

#### `raw_security_master`
- Grain: `market + symbol`
- Stores stable reference attributes:
  - `exchange`
  - `security_type`
  - `name`
  - `board`
  - `industry`
  - `list_date`
  - `delist_date`
  - `status`
  - `source_payload`

#### `raw_equity_daily_quotes`
- Grain: `trade_date + symbol`
- This is the core table for most future indicators.
- Stores full-market daily stock facts:
  - `open / high / low / close / pre_close`
  - `change_amount / pct_change`
  - `volume / turnover`
  - `turnover_rate / amplitude / volume_ratio`
  - `pe_dynamic / pb / total_market_cap / float_market_cap`
  - `limit_up_price / limit_down_price`
  - `is_limit_up / is_limit_down / is_suspended`
  - `source_payload`
- Supports:
  - breadth
  - turnover concentration
  - momentum and reversal
  - volatility expansion / compression
  - leader identification
  - regime features

#### `raw_equity_daily_limit_events`
- Grain: `trade_date + symbol + event_side`
- Stores limit-up/down event facts:
  - `event_side`
  - `board_count`
  - `seal_amount / seal_volume`
  - `first_limit_time / last_limit_time`
  - `open_times`
  - `turnover_rate`
  - `limit_reason`
  - `source_payload`
- Supports:
  - up/down limit breadth
  -连板结构
  -炸板率
  -封单质量
  -N 字 / 反包 / 高标跟踪

#### `raw_concept_board_daily`
- Grain: `trade_date + board_type + board_name`
- Stores theme / concept / industry board daily facts:
  - `board_code`
  - `turnover`
  - `pct_change`
  - `market_cap`
  - `advancers / decliners`
  - `leader`
  - `member_count`
  - `rank`
  - `source_payload`
- Supports:
  - theme rotation
  - hot-board persistence
  - board breadth
  - leader concentration

#### `raw_concept_board_constituents_daily`
- Grain: `trade_date + board_type + board_name + symbol`
- Stores daily board membership snapshots.
- Supports:
  - theme breadth decomposition
  - constituent overlap
  - board internal leader concentration
  - board-to-stock signal tracing

#### `raw_index_daily_quotes`
- Grain: `trade_date + index_code`
- Stores major index daily OHLCV-style facts.
- Supports:
  - relative strength vs benchmark
  - regime and risk-on/risk-off features
  - breadth confirmation against index direction

## Why This Supports 100+ Indicators Better
- Most daily technical, breadth, liquidity, volatility, and regime indicators can be derived from `raw_equity_daily_quotes`.
- Event-driven limit statistics belong in `raw_equity_daily_limit_events`, not in derived serving payloads.
- Theme and sector indicators need both board-level facts and constituent snapshots; one without the other is not enough.
- Landing tables decouple ingestion completeness from schema completeness, so new AkShare columns can be preserved immediately even before canonical normalization is expanded.

## Migration Strategy
### Phase 1
- Introduce Raw V2 tables and keep Raw V1 stable while the code path is being migrated.

### Phase 2
- Move ingestion and runtime reads onto Raw V2 canonical tables.
- Replace the Raw V1 stock-kline cache path with Raw V2 quote-history reconstruction.

### Phase 3
- Backfill stored Raw V1 data into Raw V2 landing/audit plus canonical tables.
- Drop the Raw V1 raw tables after the backfill is complete.

## Current Runtime Reality
- The runtime writes Raw V2 canonical storage for:
  - `raw_trade_calendar`
  - `raw_security_master`
  - `raw_equity_daily_quotes`
  - `raw_equity_daily_limit_events`
  - `raw_concept_board_daily`
  - `raw_concept_board_constituents_daily`
  - `raw_index_daily_quotes`
- Daily concept-board-constituent ingestion is currently bounded to the top 100 ranked concept boards and each board fetch is isolated behind a hard timeout so stalled upstream requests do not block the whole daily run.
- The runtime also writes landing/audit records for fetched daily datasets:
  - `raw_ingestion_runs`
  - `raw_dataset_batches`
  - `raw_source_payload_rows`
- The runtime reads canonical Raw V2 tables for:
  - active theme universe
  - tracked equities universe
  - `market_turnover`
  - `decliner_count`
  - `active_capital_ratio`
  - `up_limit_count`
  - `down_limit_count`
  - `highest_board`
  - `n_shape_limit_up_count` for current and historical limit-event inputs
- Raw-source reuse reads canonical Raw V2 mappings for `market_snapshot`, `limit_up_pool`, historical limit-up-pool reads, and `concept_boards`.
- Dashboard breadth reads canonical Raw V2 quote rows.
- Stock-kline history is reconstructed from Raw V2 quote history instead of a dedicated Raw V1 table.
- `supabase/migrations/0008_raw_v2_cutover.sql` is the cutover step that preserves V1 data by backfilling Raw V2 landing/audit and canonical tables before dropping the V1 tables.
- The production Supabase project was cut over to Raw V2 on `2026-04-09`; the legacy Raw V1 raw tables no longer exist there.
