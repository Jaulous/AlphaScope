create extension if not exists pgcrypto;
do $$
begin
  if exists (
    select 1 from pg_available_extensions where name = 'timescaledb'
  ) then
    create extension if not exists timescaledb;
  end if;
end $$;

create table if not exists public.indicator_definitions (
  key text primary key,
  type text not null,
  name text not null,
  enabled boolean not null default true,
  config jsonb not null default '{}'::jsonb,
  description text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.daily_indicators (
  id bigint generated always as identity primary key,
  key text not null,
  indicator_date date not null,
  title text not null,
  type text not null,
  value_numeric numeric,
  value_text text,
  delta numeric,
  unit text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (key, indicator_date)
);

create index if not exists daily_indicators_date_idx on public.daily_indicators (indicator_date desc);
create index if not exists daily_indicators_key_idx on public.daily_indicators (key, indicator_date desc);

create table if not exists public.daily_themes_volume (
  id bigint generated always as identity primary key,
  indicator_date date not null,
  theme_name text not null,
  turnover numeric not null,
  rank integer not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique (indicator_date, theme_name)
);

create index if not exists daily_themes_volume_date_idx on public.daily_themes_volume (indicator_date desc);
create index if not exists daily_themes_volume_theme_idx on public.daily_themes_volume (theme_name, indicator_date desc);

create table if not exists public.board_documents (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  title text not null default 'Main Board',
  snapshot jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.stock_kline_daily (
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
  primary key (ts, symbol)
);

do $$
begin
  if exists (
    select 1 from pg_extension where extname = 'timescaledb'
  ) then
    perform create_hypertable(
      'public.stock_kline_daily',
      'ts',
      if_not_exists => true,
      migrate_data => true
    );
  end if;
end $$;

alter table public.indicator_definitions enable row level security;
alter table public.daily_indicators enable row level security;
alter table public.daily_themes_volume enable row level security;
alter table public.board_documents enable row level security;
alter table public.stock_kline_daily enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'indicator_definitions' and policyname = 'indicator_definitions_read'
  ) then
    create policy indicator_definitions_read on public.indicator_definitions
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'daily_indicators' and policyname = 'daily_indicators_read'
  ) then
    create policy daily_indicators_read on public.daily_indicators
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'daily_themes_volume' and policyname = 'daily_themes_volume_read'
  ) then
    create policy daily_themes_volume_read on public.daily_themes_volume
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'board_documents' and policyname = 'board_documents_read'
  ) then
    create policy board_documents_read on public.board_documents
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'daily_indicators'
  ) then
    alter publication supabase_realtime add table public.daily_indicators;
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'daily_themes_volume'
  ) then
    alter publication supabase_realtime add table public.daily_themes_volume;
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'board_documents'
  ) then
    alter publication supabase_realtime add table public.board_documents;
  end if;
end $$;
