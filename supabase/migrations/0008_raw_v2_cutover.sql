delete from public.raw_source_payload_rows
where batch_id in (
  select id
  from public.raw_dataset_batches
  where source_name = 'migration_v1_backfill'
);

delete from public.raw_dataset_batches
where source_name = 'migration_v1_backfill';

delete from public.raw_ingestion_runs
where source_name = 'migration_v1_backfill';

with all_dates as (
  select distinct snapshot_date as trade_date from public.raw_market_snapshot_daily
  union
  select distinct snapshot_date as trade_date from public.raw_limit_up_pool_daily
  union
  select distinct snapshot_date as trade_date from public.raw_concept_boards_daily
  union
  select distinct snapshot_date as trade_date from public.raw_stock_kline_daily
)
insert into public.raw_trade_calendar (
  market,
  trade_date,
  is_trading_day,
  source_name,
  source_payload,
  metadata
)
select
  'CN_A',
  trade_date,
  true,
  'migration_v1_backfill',
  jsonb_build_object('source_tables', jsonb_build_array(
    'raw_market_snapshot_daily',
    'raw_limit_up_pool_daily',
    'raw_concept_boards_daily',
    'raw_stock_kline_daily'
  )),
  '{}'::jsonb
from all_dates
on conflict (market, trade_date) do update
set
  is_trading_day = excluded.is_trading_day,
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = excluded.metadata;

with symbol_rows as (
  select
    symbol,
    nullif(name, '') as name,
    snapshot_date as observed_date
  from public.raw_market_snapshot_daily
  where symbol is not null
  union all
  select
    symbol,
    nullif(name, '') as name,
    snapshot_date as observed_date
  from public.raw_stock_kline_daily
  where symbol is not null
),
latest_symbols as (
  select distinct on (symbol)
    symbol,
    name,
    observed_date
  from symbol_rows
  order by symbol, observed_date desc, name desc nulls last
)
insert into public.raw_security_master (
  market,
  symbol,
  exchange,
  security_type,
  name,
  board,
  industry,
  list_date,
  delist_date,
  status,
  source_name,
  source_payload,
  metadata,
  updated_at
)
select
  'CN_A',
  symbol,
  case
    when symbol like '600%' or symbol like '601%' or symbol like '603%' or symbol like '605%' or symbol like '688%' or symbol like '689%' or symbol like '510%' or symbol like '511%' or symbol like '512%' or symbol like '513%' or symbol like '515%' or symbol like '518%' then 'SSE'
    when symbol like '000%' or symbol like '001%' or symbol like '002%' or symbol like '003%' or symbol like '300%' or symbol like '301%' or symbol like '159%' then 'SZSE'
    when symbol like '430%' or symbol like '800%' or symbol like '830%' or symbol like '831%' or symbol like '832%' or symbol like '833%' or symbol like '835%' or symbol like '836%' or symbol like '837%' or symbol like '838%' or symbol like '839%' then 'BSE'
    else null
  end,
  'equity',
  name,
  case
    when symbol like '688%' or symbol like '689%' then 'STAR'
    when symbol like '300%' or symbol like '301%' then 'ChiNext'
    when symbol like '430%' or symbol like '800%' or symbol like '830%' or symbol like '831%' or symbol like '832%' or symbol like '833%' or symbol like '835%' or symbol like '836%' or symbol like '837%' or symbol like '838%' or symbol like '839%' then 'Beijing'
    when symbol like '600%' or symbol like '601%' or symbol like '603%' or symbol like '605%' or symbol like '510%' or symbol like '511%' or symbol like '512%' or symbol like '513%' or symbol like '515%' or symbol like '518%' then 'Main'
    when symbol like '000%' or symbol like '001%' or symbol like '002%' or symbol like '003%' or symbol like '159%' then 'Main'
    else null
  end,
  null,
  null,
  null,
  'active',
  'migration_v1_backfill',
  jsonb_build_object('source_tables', jsonb_build_array('raw_market_snapshot_daily', 'raw_stock_kline_daily')),
  jsonb_build_object('last_observed_date', observed_date),
  timezone('utc', now())
from latest_symbols
on conflict (market, symbol) do update
set
  exchange = coalesce(excluded.exchange, public.raw_security_master.exchange),
  name = coalesce(excluded.name, public.raw_security_master.name),
  board = coalesce(excluded.board, public.raw_security_master.board),
  status = excluded.status,
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = excluded.metadata,
  updated_at = excluded.updated_at;

insert into public.raw_equity_daily_quotes (
  trade_date,
  symbol,
  market,
  exchange,
  name,
  close,
  change_amount,
  pct_change,
  volume,
  turnover,
  turnover_rate,
  amplitude,
  pe_dynamic,
  is_limit_up,
  is_limit_down,
  is_suspended,
  source_name,
  source_payload,
  metadata
)
select
  snapshot_date,
  symbol,
  'CN_A',
  case
    when symbol like '600%' or symbol like '601%' or symbol like '603%' or symbol like '605%' or symbol like '688%' or symbol like '689%' or symbol like '510%' or symbol like '511%' or symbol like '512%' or symbol like '513%' or symbol like '515%' or symbol like '518%' then 'SSE'
    when symbol like '000%' or symbol like '001%' or symbol like '002%' or symbol like '003%' or symbol like '300%' or symbol like '301%' or symbol like '159%' then 'SZSE'
    when symbol like '430%' or symbol like '800%' or symbol like '830%' or symbol like '831%' or symbol like '832%' or symbol like '833%' or symbol like '835%' or symbol like '836%' or symbol like '837%' or symbol like '838%' or symbol like '839%' then 'BSE'
    else null
  end,
  nullif(name, ''),
  last_price,
  change_amount,
  pct_change,
  volume,
  turnover,
  turnover_rate,
  amplitude,
  pe_dynamic,
  exists (
    select 1
    from public.raw_limit_up_pool_daily lup
    where lup.snapshot_date = ms.snapshot_date
      and lup.symbol = ms.symbol
  ) or coalesce(pct_change >= 9.8, false),
  coalesce(pct_change <= -9.8, false),
  false,
  'migration_v1_market_snapshot',
  jsonb_build_object('source_table', 'raw_market_snapshot_daily'),
  '{}'::jsonb
from public.raw_market_snapshot_daily ms
on conflict (trade_date, symbol) do update
set
  exchange = coalesce(excluded.exchange, public.raw_equity_daily_quotes.exchange),
  name = coalesce(excluded.name, public.raw_equity_daily_quotes.name),
  close = coalesce(excluded.close, public.raw_equity_daily_quotes.close),
  change_amount = coalesce(excluded.change_amount, public.raw_equity_daily_quotes.change_amount),
  pct_change = coalesce(excluded.pct_change, public.raw_equity_daily_quotes.pct_change),
  volume = coalesce(excluded.volume, public.raw_equity_daily_quotes.volume),
  turnover = coalesce(excluded.turnover, public.raw_equity_daily_quotes.turnover),
  turnover_rate = coalesce(excluded.turnover_rate, public.raw_equity_daily_quotes.turnover_rate),
  amplitude = coalesce(excluded.amplitude, public.raw_equity_daily_quotes.amplitude),
  pe_dynamic = coalesce(excluded.pe_dynamic, public.raw_equity_daily_quotes.pe_dynamic),
  is_limit_up = coalesce(excluded.is_limit_up, public.raw_equity_daily_quotes.is_limit_up),
  is_limit_down = coalesce(excluded.is_limit_down, public.raw_equity_daily_quotes.is_limit_down),
  is_suspended = coalesce(excluded.is_suspended, public.raw_equity_daily_quotes.is_suspended),
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = public.raw_equity_daily_quotes.metadata || excluded.metadata;

insert into public.raw_equity_daily_quotes (
  trade_date,
  symbol,
  market,
  exchange,
  name,
  open,
  high,
  low,
  close,
  volume,
  turnover,
  amplitude,
  pct_change,
  source_name,
  source_payload,
  metadata
)
select
  snapshot_date,
  symbol,
  'CN_A',
  case
    when symbol like '600%' or symbol like '601%' or symbol like '603%' or symbol like '605%' or symbol like '688%' or symbol like '689%' or symbol like '510%' or symbol like '511%' or symbol like '512%' or symbol like '513%' or symbol like '515%' or symbol like '518%' then 'SSE'
    when symbol like '000%' or symbol like '001%' or symbol like '002%' or symbol like '003%' or symbol like '300%' or symbol like '301%' or symbol like '159%' then 'SZSE'
    when symbol like '430%' or symbol like '800%' or symbol like '830%' or symbol like '831%' or symbol like '832%' or symbol like '833%' or symbol like '835%' or symbol like '836%' or symbol like '837%' or symbol like '838%' or symbol like '839%' then 'BSE'
    else null
  end,
  nullif(name, ''),
  open,
  high,
  low,
  close,
  volume,
  turnover,
  amplitude,
  pct_change,
  'migration_v1_stock_kline',
  jsonb_build_object('source_table', 'raw_stock_kline_daily'),
  '{}'::jsonb
from public.raw_stock_kline_daily
on conflict (trade_date, symbol) do update
set
  exchange = coalesce(excluded.exchange, public.raw_equity_daily_quotes.exchange),
  name = coalesce(excluded.name, public.raw_equity_daily_quotes.name),
  open = coalesce(excluded.open, public.raw_equity_daily_quotes.open),
  high = coalesce(excluded.high, public.raw_equity_daily_quotes.high),
  low = coalesce(excluded.low, public.raw_equity_daily_quotes.low),
  close = coalesce(excluded.close, public.raw_equity_daily_quotes.close),
  volume = coalesce(excluded.volume, public.raw_equity_daily_quotes.volume),
  turnover = coalesce(excluded.turnover, public.raw_equity_daily_quotes.turnover),
  amplitude = coalesce(excluded.amplitude, public.raw_equity_daily_quotes.amplitude),
  pct_change = coalesce(excluded.pct_change, public.raw_equity_daily_quotes.pct_change),
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = public.raw_equity_daily_quotes.metadata || excluded.metadata;

insert into public.raw_equity_daily_limit_events (
  trade_date,
  symbol,
  event_side,
  market,
  name,
  board_count,
  seal_amount,
  turnover_rate,
  first_limit_time,
  last_limit_time,
  limit_type,
  source_name,
  source_payload,
  metadata
)
select
  snapshot_date,
  symbol,
  'up',
  'CN_A',
  nullif(name, ''),
  board_count,
  seal_funds,
  turnover_rate,
  first_limit_time,
  last_limit_time,
  'pool',
  'migration_v1_limit_up_pool',
  jsonb_build_object('source_table', 'raw_limit_up_pool_daily'),
  '{}'::jsonb
from public.raw_limit_up_pool_daily
on conflict (trade_date, symbol, event_side) do update
set
  name = coalesce(excluded.name, public.raw_equity_daily_limit_events.name),
  board_count = coalesce(excluded.board_count, public.raw_equity_daily_limit_events.board_count),
  seal_amount = coalesce(excluded.seal_amount, public.raw_equity_daily_limit_events.seal_amount),
  turnover_rate = coalesce(excluded.turnover_rate, public.raw_equity_daily_limit_events.turnover_rate),
  first_limit_time = coalesce(excluded.first_limit_time, public.raw_equity_daily_limit_events.first_limit_time),
  last_limit_time = coalesce(excluded.last_limit_time, public.raw_equity_daily_limit_events.last_limit_time),
  limit_type = excluded.limit_type,
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = public.raw_equity_daily_limit_events.metadata || excluded.metadata;

insert into public.raw_equity_daily_limit_events (
  trade_date,
  symbol,
  event_side,
  market,
  name,
  turnover_rate,
  limit_type,
  source_name,
  source_payload,
  metadata
)
select
  snapshot_date,
  symbol,
  'down',
  'CN_A',
  nullif(name, ''),
  turnover_rate,
  'threshold_proxy',
  'migration_v1_market_snapshot',
  jsonb_build_object('source_table', 'raw_market_snapshot_daily'),
  jsonb_build_object('pct_change', pct_change)
from public.raw_market_snapshot_daily
where coalesce(pct_change <= -9.8, false)
on conflict (trade_date, symbol, event_side) do update
set
  name = coalesce(excluded.name, public.raw_equity_daily_limit_events.name),
  turnover_rate = coalesce(excluded.turnover_rate, public.raw_equity_daily_limit_events.turnover_rate),
  limit_type = excluded.limit_type,
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = public.raw_equity_daily_limit_events.metadata || excluded.metadata;

insert into public.raw_concept_board_daily (
  trade_date,
  board_type,
  board_name,
  turnover,
  pct_change,
  market_cap,
  advancers,
  decliners,
  leader,
  member_count,
  rank,
  source_name,
  source_payload,
  metadata
)
select
  snapshot_date,
  'concept',
  theme_name,
  turnover,
  pct_change,
  market_cap,
  advancers,
  decliners,
  leader,
  case
    when advancers is not null or decliners is not null then coalesce(advancers, 0) + coalesce(decliners, 0)
    else null
  end,
  rank,
  'migration_v1_concept_boards',
  jsonb_build_object('source_table', 'raw_concept_boards_daily'),
  '{}'::jsonb
from public.raw_concept_boards_daily
on conflict (trade_date, board_type, board_name) do update
set
  turnover = coalesce(excluded.turnover, public.raw_concept_board_daily.turnover),
  pct_change = coalesce(excluded.pct_change, public.raw_concept_board_daily.pct_change),
  market_cap = coalesce(excluded.market_cap, public.raw_concept_board_daily.market_cap),
  advancers = coalesce(excluded.advancers, public.raw_concept_board_daily.advancers),
  decliners = coalesce(excluded.decliners, public.raw_concept_board_daily.decliners),
  leader = coalesce(excluded.leader, public.raw_concept_board_daily.leader),
  member_count = coalesce(excluded.member_count, public.raw_concept_board_daily.member_count),
  rank = coalesce(excluded.rank, public.raw_concept_board_daily.rank),
  source_name = excluded.source_name,
  source_payload = excluded.source_payload,
  metadata = public.raw_concept_board_daily.metadata || excluded.metadata;

with grouped as (
  select snapshot_date as as_of_date, count(*) as row_count
  from public.raw_market_snapshot_daily
  group by snapshot_date
),
runs as (
  insert into public.raw_ingestion_runs (
    trigger,
    dataset_key,
    source_name,
    market,
    as_of_date,
    request_params,
    status,
    row_count,
    started_at,
    finished_at,
    metadata
  )
  select
    'migration_v1_backfill',
    'market_snapshot',
    'migration_v1_backfill',
    'CN_A',
    as_of_date,
    '{}'::jsonb,
    'backfilled',
    row_count,
    timezone('utc', now()),
    timezone('utc', now()),
    jsonb_build_object('source_table', 'raw_market_snapshot_daily')
  from grouped
  returning id, as_of_date
),
batches as (
  insert into public.raw_dataset_batches (
    run_id,
    dataset_key,
    source_name,
    source_endpoint,
    market,
    as_of_date,
    snapshot_time,
    fetch_params,
    column_names,
    record_count,
    payload_sha256,
    metadata
  )
  select
    runs.id,
    'market_snapshot',
    'migration_v1_backfill',
    'raw_market_snapshot_daily',
    'CN_A',
    runs.as_of_date,
    timezone('utc', now()),
    '{}'::jsonb,
    '["snapshot_date","symbol","name","last_price","pct_change","change_amount","volume","turnover","amplitude","turnover_rate","pe_dynamic","metadata"]'::jsonb,
    grouped.row_count,
    null,
    jsonb_build_object('source_table', 'raw_market_snapshot_daily')
  from runs
  join grouped on grouped.as_of_date = runs.as_of_date
  returning id, as_of_date
)
insert into public.raw_source_payload_rows (batch_id, row_no, natural_key, payload)
select
  batches.id,
  row_number() over (partition by batches.id order by t.symbol),
  concat('symbol=', t.symbol, '|snapshot_date=', t.snapshot_date),
  to_jsonb(t)
from batches
join public.raw_market_snapshot_daily t
  on t.snapshot_date = batches.as_of_date;

with grouped as (
  select snapshot_date as as_of_date, count(*) as row_count
  from public.raw_limit_up_pool_daily
  group by snapshot_date
),
runs as (
  insert into public.raw_ingestion_runs (
    trigger,
    dataset_key,
    source_name,
    market,
    as_of_date,
    request_params,
    status,
    row_count,
    started_at,
    finished_at,
    metadata
  )
  select
    'migration_v1_backfill',
    'limit_up_pool',
    'migration_v1_backfill',
    'CN_A',
    as_of_date,
    '{}'::jsonb,
    'backfilled',
    row_count,
    timezone('utc', now()),
    timezone('utc', now()),
    jsonb_build_object('source_table', 'raw_limit_up_pool_daily')
  from grouped
  returning id, as_of_date
),
batches as (
  insert into public.raw_dataset_batches (
    run_id,
    dataset_key,
    source_name,
    source_endpoint,
    market,
    as_of_date,
    snapshot_time,
    fetch_params,
    column_names,
    record_count,
    payload_sha256,
    metadata
  )
  select
    runs.id,
    'limit_up_pool',
    'migration_v1_backfill',
    'raw_limit_up_pool_daily',
    'CN_A',
    runs.as_of_date,
    timezone('utc', now()),
    '{}'::jsonb,
    '["snapshot_date","symbol","name","board_count","seal_funds","turnover_rate","first_limit_time","last_limit_time","metadata"]'::jsonb,
    grouped.row_count,
    null,
    jsonb_build_object('source_table', 'raw_limit_up_pool_daily')
  from runs
  join grouped on grouped.as_of_date = runs.as_of_date
  returning id, as_of_date
)
insert into public.raw_source_payload_rows (batch_id, row_no, natural_key, payload)
select
  batches.id,
  row_number() over (partition by batches.id order by t.symbol),
  concat('symbol=', t.symbol, '|snapshot_date=', t.snapshot_date),
  to_jsonb(t)
from batches
join public.raw_limit_up_pool_daily t
  on t.snapshot_date = batches.as_of_date;

with grouped as (
  select snapshot_date as as_of_date, count(*) as row_count
  from public.raw_concept_boards_daily
  group by snapshot_date
),
runs as (
  insert into public.raw_ingestion_runs (
    trigger,
    dataset_key,
    source_name,
    market,
    as_of_date,
    request_params,
    status,
    row_count,
    started_at,
    finished_at,
    metadata
  )
  select
    'migration_v1_backfill',
    'concept_boards',
    'migration_v1_backfill',
    'CN_A',
    as_of_date,
    '{}'::jsonb,
    'backfilled',
    row_count,
    timezone('utc', now()),
    timezone('utc', now()),
    jsonb_build_object('source_table', 'raw_concept_boards_daily')
  from grouped
  returning id, as_of_date
),
batches as (
  insert into public.raw_dataset_batches (
    run_id,
    dataset_key,
    source_name,
    source_endpoint,
    market,
    as_of_date,
    snapshot_time,
    fetch_params,
    column_names,
    record_count,
    payload_sha256,
    metadata
  )
  select
    runs.id,
    'concept_boards',
    'migration_v1_backfill',
    'raw_concept_boards_daily',
    'CN_A',
    runs.as_of_date,
    timezone('utc', now()),
    '{}'::jsonb,
    '["snapshot_date","theme_name","turnover","pct_change","market_cap","advancers","decliners","leader","rank","metadata"]'::jsonb,
    grouped.row_count,
    null,
    jsonb_build_object('source_table', 'raw_concept_boards_daily')
  from runs
  join grouped on grouped.as_of_date = runs.as_of_date
  returning id, as_of_date
)
insert into public.raw_source_payload_rows (batch_id, row_no, natural_key, payload)
select
  batches.id,
  row_number() over (partition by batches.id order by t.rank, t.theme_name),
  concat('theme_name=', t.theme_name, '|snapshot_date=', t.snapshot_date),
  to_jsonb(t)
from batches
join public.raw_concept_boards_daily t
  on t.snapshot_date = batches.as_of_date;

with grouped as (
  select snapshot_date as as_of_date, count(*) as row_count
  from public.raw_stock_kline_daily
  group by snapshot_date
),
runs as (
  insert into public.raw_ingestion_runs (
    trigger,
    dataset_key,
    source_name,
    market,
    as_of_date,
    request_params,
    status,
    row_count,
    started_at,
    finished_at,
    metadata
  )
  select
    'migration_v1_backfill',
    'stock_kline',
    'migration_v1_backfill',
    'CN_A',
    as_of_date,
    '{}'::jsonb,
    'backfilled',
    row_count,
    timezone('utc', now()),
    timezone('utc', now()),
    jsonb_build_object('source_table', 'raw_stock_kline_daily')
  from grouped
  returning id, as_of_date
),
batches as (
  insert into public.raw_dataset_batches (
    run_id,
    dataset_key,
    source_name,
    source_endpoint,
    market,
    as_of_date,
    snapshot_time,
    fetch_params,
    column_names,
    record_count,
    payload_sha256,
    metadata
  )
  select
    runs.id,
    'stock_kline',
    'migration_v1_backfill',
    'raw_stock_kline_daily',
    'CN_A',
    runs.as_of_date,
    timezone('utc', now()),
    '{}'::jsonb,
    '["snapshot_date","ts","symbol","name","open","high","low","close","volume","turnover","amplitude","pct_change","metadata"]'::jsonb,
    grouped.row_count,
    null,
    jsonb_build_object('source_table', 'raw_stock_kline_daily')
  from runs
  join grouped on grouped.as_of_date = runs.as_of_date
  returning id, as_of_date
)
insert into public.raw_source_payload_rows (batch_id, row_no, natural_key, payload)
select
  batches.id,
  row_number() over (partition by batches.id order by t.ts, t.symbol),
  concat('symbol=', t.symbol, '|ts=', t.ts),
  to_jsonb(t)
from batches
join public.raw_stock_kline_daily t
  on t.snapshot_date = batches.as_of_date;

drop table if exists public.raw_market_snapshot_daily;
drop table if exists public.raw_limit_up_pool_daily;
drop table if exists public.raw_concept_boards_daily;
drop table if exists public.raw_stock_kline_daily;
