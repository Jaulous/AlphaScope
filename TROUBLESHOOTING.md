# Troubleshooting

## The frontend opens but shows no data

Check the backend first:

```bash
curl http://localhost:8000/api/health
```

Then check the dashboard endpoint:

```bash
curl http://localhost:8000/api/dashboard/latest
```

If `health` works but `dashboard/latest` fails, the usual causes are:

- AkShare request failure
- market data schema drift
- invalid Supabase config
- no persisted snapshot exists yet and the on-demand fetch failed

If `dashboard/latest` returns warnings, inspect `latest_run` in the response. Typical expected cases are:

- weekend requests target the latest trading day instead of the current calendar day
- one raw source was reused from stored data for the same trading day
- the latest fetch failed but the previous correct serving snapshot was preserved
- a recent restart is still backfilling missed trading days before normal scheduling resumes

## Supabase is not configured

That is no longer allowed for dashboard serving.

Expected behavior:

- the server still starts
- `/api/dashboard/latest` returns `503`
- `/api/fetch/run` returns `502` with a persistence configuration error
- board and market data APIs are unavailable until Supabase is configured

## AkShare schema drift

AkShare occasionally changes column names.

If the fetch job fails:

1. inspect the raw dataframe columns in `packages/quant-core/src/quant_core/ingestion/akshare_provider.py`
2. verify the corresponding `raw_*` table wrote the expected rows
3. update the normalization map
4. keep indicator business logic unchanged unless the metric definition itself changed

If one source is blocked but others still work, prefer extending the provider fallback chain instead of changing indicator logic.

## `POST /api/fetch/run` works but nothing is stored

That should not happen anymore.

If it does, verify:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- the target project has the schema from `supabase/migrations`
- the new `raw_*` tables are present and writable

## The backend missed one or more trading days

Restarting the backend now triggers startup backfill before normal scheduling begins.

Check:

1. restart the backend process
2. inspect the latest `fetch_runs` rows for `startup_backfill`
3. confirm `daily_indicators` now contains the missing trading dates

## Local ports

- `3000`: Next.js frontend
- `8000`: FastAPI backend
