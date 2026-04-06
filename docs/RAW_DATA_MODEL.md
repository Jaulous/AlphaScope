# Raw Data Model

## Purpose
Define a raw-layer architecture that can support a large future indicator library without repeatedly reshaping storage around a handful of current metrics.

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
- Add Raw V2 tables without breaking the current runtime.
- Keep current `raw_*_daily` tables in place so production serving stays stable.

### Phase 2
- Rewrite ingestion to write both landing-layer batches and canonical raw facts.
- Expand stock daily ingestion from tracked-symbol subset to full-market daily quote storage.

### Phase 3
- Move indicator implementations to depend on Raw V2 canonical tables.
- Keep old raw tables only as transitional compatibility views or deprecate them.

## Transitional Reality
- Current production code still reads and writes the older Raw V1 tables.
- Raw V2 is now the target architecture and schema direction, not yet the active runtime data path.
