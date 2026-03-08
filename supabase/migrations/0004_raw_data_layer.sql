create table if not exists public.raw_market_snapshot_daily (
  snapshot_date date not null,
  symbol text not null,
  name text,
  last_price numeric,
  pct_change numeric,
  change_amount numeric,
  volume numeric,
  turnover numeric,
  amplitude numeric,
  turnover_rate numeric,
  pe_dynamic numeric,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (snapshot_date, symbol)
);

create index if not exists raw_market_snapshot_daily_date_idx
  on public.raw_market_snapshot_daily (snapshot_date desc);

create table if not exists public.raw_limit_up_pool_daily (
  snapshot_date date not null,
  symbol text not null,
  name text,
  board_count integer,
  seal_funds numeric,
  turnover_rate numeric,
  first_limit_time text,
  last_limit_time text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (snapshot_date, symbol)
);

create index if not exists raw_limit_up_pool_daily_date_idx
  on public.raw_limit_up_pool_daily (snapshot_date desc);

create table if not exists public.raw_concept_boards_daily (
  snapshot_date date not null,
  theme_name text not null,
  turnover numeric,
  pct_change numeric,
  market_cap numeric,
  advancers integer,
  decliners integer,
  leader text,
  rank integer,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (snapshot_date, theme_name)
);

create index if not exists raw_concept_boards_daily_date_idx
  on public.raw_concept_boards_daily (snapshot_date desc);

create table if not exists public.raw_stock_kline_daily (
  snapshot_date date not null,
  ts timestamptz not null,
  symbol text not null,
  name text,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  volume numeric,
  turnover numeric,
  amplitude numeric,
  pct_change numeric,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (ts, symbol)
);

create index if not exists raw_stock_kline_daily_date_idx
  on public.raw_stock_kline_daily (snapshot_date desc);

alter table public.raw_market_snapshot_daily enable row level security;
alter table public.raw_limit_up_pool_daily enable row level security;
alter table public.raw_concept_boards_daily enable row level security;
alter table public.raw_stock_kline_daily enable row level security;
