insert into public.indicator_definitions (key, type, name, enabled, config, description)
values
  (
    'up_limit_count',
    'up_limit_count',
    'Daily Up Limit Count',
    true,
    '{"threshold": 9.8}'::jsonb,
    'Number of stocks closing at or near up-limit threshold.'
  ),
  (
    'highest_board',
    'highest_board',
    'Highest Board',
    true,
    '{}'::jsonb,
    'Highest consecutive board count from daily limit-up pool.'
  ),
  (
    'down_limit_count',
    'down_limit_count',
    'Daily Down Limit Count',
    true,
    '{"threshold": -9.8}'::jsonb,
    'Number of stocks closing at or near down-limit threshold.'
  ),
  (
    'decliner_count',
    'decliner_count',
    'Decliner Count',
    true,
    '{}'::jsonb,
    'Number of stocks with negative daily percentage change.'
  ),
  (
    'active_capital_ratio',
    'active_capital_ratio',
    'Active Capital Ratio',
    true,
    '{"top_percent": 0.1}'::jsonb,
    'Share of total turnover concentrated in the top decile by turnover.'
  ),
  (
    'market_turnover',
    'market_turnover',
    'Total Market Turnover',
    true,
    '{"display_unit": "100M"}'::jsonb,
    'Aggregate turnover across the market snapshot.'
  ),
  (
    'active_themes',
    'active_themes',
    'Active Themes Volume',
    true,
    '{"top_n": 20, "threshold": 0, "window_days": 20, "expire_days": 5}'::jsonb,
    'Top active themes selected from AkShare concept boards by turnover.'
  )
on conflict (key) do update
set
  type = excluded.type,
  name = excluded.name,
  enabled = excluded.enabled,
  config = excluded.config,
  description = excluded.description,
  updated_at = timezone('utc', now());
