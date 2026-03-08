do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'stock_kline_daily' and policyname = 'stock_kline_daily_read'
  ) then
    create policy stock_kline_daily_read on public.stock_kline_daily
      for select
      to anon, authenticated
      using (true);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'stock_kline_daily'
  ) then
    alter publication supabase_realtime add table public.stock_kline_daily;
  end if;
end $$;
