create table if not exists public.fetch_runs (
  id bigint generated always as identity primary key,
  trigger text not null,
  reference_date date not null,
  target_date date not null,
  status text not null,
  skipped_reason text,
  source_statuses jsonb not null default '{}'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  counts jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists fetch_runs_target_date_idx
  on public.fetch_runs (target_date desc, created_at desc);

alter table public.fetch_runs enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'fetch_runs' and policyname = 'fetch_runs_read'
  ) then
    create policy fetch_runs_read on public.fetch_runs
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;
