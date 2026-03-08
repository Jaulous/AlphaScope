insert into public.indicator_definitions (key, type, name, enabled, config, description)
values (
  'n_shape_limit_up_count',
  'n_shape_limit_up_count',
  'N-Shape Limit-Up Count',
  true,
  '{"lookback_days": 30, "min_pullback_pct": 5.0, "min_gap_days": 2, "breakout_tolerance_pct": 0.0}'::jsonb,
  'Today''s limit-up stocks that also show a prior limit-up, a meaningful pullback, and a renewed breakout within the lookback window.'
)
on conflict (key) do update
set
  type = excluded.type,
  name = excluded.name,
  enabled = excluded.enabled,
  config = excluded.config,
  description = excluded.description,
  updated_at = timezone('utc', now());
