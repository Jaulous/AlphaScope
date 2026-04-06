create table if not exists public.raw_ingestion_runs (
  id bigserial primary key,
  trigger text not null,
  dataset_key text not null,
  source_name text not null,
  market text not null default 'CN_A',
  as_of_date date,
  request_params jsonb not null default '{}'::jsonb,
  status text not null,
  row_count integer,
  error_message text,
  started_at timestamptz not null default timezone('utc', now()),
  finished_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists raw_ingestion_runs_dataset_date_idx
  on public.raw_ingestion_runs (dataset_key, as_of_date desc, started_at desc);

create table if not exists public.raw_dataset_batches (
  id bigserial primary key,
  run_id bigint references public.raw_ingestion_runs(id) on delete cascade,
  dataset_key text not null,
  source_name text not null,
  source_endpoint text,
  market text not null default 'CN_A',
  as_of_date date,
  snapshot_time timestamptz,
  fetch_params jsonb not null default '{}'::jsonb,
  column_names jsonb not null default '[]'::jsonb,
  record_count integer not null default 0,
  payload_sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists raw_dataset_batches_dataset_date_idx
  on public.raw_dataset_batches (dataset_key, as_of_date desc, created_at desc);

create table if not exists public.raw_source_payload_rows (
  batch_id bigint not null references public.raw_dataset_batches(id) on delete cascade,
  row_no integer not null,
  natural_key text,
  payload jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (batch_id, row_no)
);

create index if not exists raw_source_payload_rows_natural_key_idx
  on public.raw_source_payload_rows (natural_key);

create table if not exists public.raw_trade_calendar (
  market text not null default 'CN_A',
  trade_date date not null,
  is_trading_day boolean not null,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (market, trade_date)
);

create table if not exists public.raw_security_master (
  market text not null default 'CN_A',
  symbol text not null,
  exchange text,
  security_type text not null default 'equity',
  name text,
  board text,
  industry text,
  list_date date,
  delist_date date,
  status text,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default timezone('utc', now()),
  primary key (market, symbol)
);

create index if not exists raw_security_master_exchange_idx
  on public.raw_security_master (exchange, board);

create table if not exists public.raw_equity_daily_quotes (
  trade_date date not null,
  symbol text not null,
  market text not null default 'CN_A',
  exchange text,
  name text,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  pre_close numeric,
  change_amount numeric,
  pct_change numeric,
  volume numeric,
  turnover numeric,
  turnover_rate numeric,
  amplitude numeric,
  volume_ratio numeric,
  pe_dynamic numeric,
  pb numeric,
  total_market_cap numeric,
  float_market_cap numeric,
  limit_up_price numeric,
  limit_down_price numeric,
  is_limit_up boolean,
  is_limit_down boolean,
  is_suspended boolean,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (trade_date, symbol)
);

create index if not exists raw_equity_daily_quotes_symbol_idx
  on public.raw_equity_daily_quotes (symbol, trade_date desc);

create index if not exists raw_equity_daily_quotes_turnover_idx
  on public.raw_equity_daily_quotes (trade_date desc, turnover desc);

create table if not exists public.raw_equity_daily_limit_events (
  trade_date date not null,
  symbol text not null,
  event_side text not null,
  market text not null default 'CN_A',
  name text,
  board_count integer,
  seal_amount numeric,
  seal_volume numeric,
  turnover_rate numeric,
  open_times integer,
  first_limit_time text,
  last_limit_time text,
  limit_reason text,
  limit_type text,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (trade_date, symbol, event_side),
  constraint raw_equity_daily_limit_events_side_check
    check (event_side in ('up', 'down'))
);

create index if not exists raw_equity_daily_limit_events_symbol_idx
  on public.raw_equity_daily_limit_events (symbol, trade_date desc);

create table if not exists public.raw_concept_board_daily (
  trade_date date not null,
  board_type text not null default 'concept',
  board_name text not null,
  board_code text,
  turnover numeric,
  pct_change numeric,
  market_cap numeric,
  advancers integer,
  decliners integer,
  leader text,
  member_count integer,
  rank integer,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (trade_date, board_type, board_name)
);

create index if not exists raw_concept_board_daily_rank_idx
  on public.raw_concept_board_daily (trade_date desc, board_type, rank);

create table if not exists public.raw_concept_board_constituents_daily (
  trade_date date not null,
  board_type text not null default 'concept',
  board_name text not null,
  symbol text not null,
  market text not null default 'CN_A',
  name text,
  rank_in_board integer,
  weight numeric,
  contribution numeric,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (trade_date, board_type, board_name, symbol)
);

create index if not exists raw_concept_board_constituents_symbol_idx
  on public.raw_concept_board_constituents_daily (symbol, trade_date desc);

create table if not exists public.raw_index_daily_quotes (
  trade_date date not null,
  index_code text not null,
  market text not null default 'CN_A',
  index_name text,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  pre_close numeric,
  change_amount numeric,
  pct_change numeric,
  volume numeric,
  turnover numeric,
  amplitude numeric,
  source_name text not null default 'akshare',
  source_payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (trade_date, index_code)
);

create index if not exists raw_index_daily_quotes_code_idx
  on public.raw_index_daily_quotes (index_code, trade_date desc);

alter table public.raw_ingestion_runs enable row level security;
alter table public.raw_dataset_batches enable row level security;
alter table public.raw_source_payload_rows enable row level security;
alter table public.raw_trade_calendar enable row level security;
alter table public.raw_security_master enable row level security;
alter table public.raw_equity_daily_quotes enable row level security;
alter table public.raw_equity_daily_limit_events enable row level security;
alter table public.raw_concept_board_daily enable row level security;
alter table public.raw_concept_board_constituents_daily enable row level security;
alter table public.raw_index_daily_quotes enable row level security;
