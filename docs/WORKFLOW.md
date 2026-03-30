# Workflow

## Purpose
Define the repeatable engineering workflow for this project.

## When To Update
- Commands, CI checks, release flow, or environments change.

## Minimum Sections
- Local Development
- Quality Gates
- Release Process
- Incident/Hotfix Path

## Local Development
```bash
nvm use
corepack enable
corepack prepare pnpm@10.6.2 --activate
pnpm install
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/quant-core -e apps/server
cp .env.example .env
pnpm start:project
```

Backend-only development:

```bash
source .venv/bin/activate
pnpm --filter @limitboard/server dev
```

Frontend-only development:

```bash
pnpm --filter @limitboard/web dev
```

Open the frontend page:

```bash
pnpm open:frontend
```

Manual fetch through the packaged Python entrypoint:

```bash
PYTHONPATH=apps/server/src:packages/quant-core/src .venv/bin/python3 -m limitboard_server --trigger manual
```

Startup behavior:

- When the backend process starts, it immediately serves requests, starts the scheduler, and runs missed trading-day backfill in the background.
- Before the final scheduled run of the day, startup catch-up only requires snapshots through the previous trading day.
- Embedded scheduler is intended for long-running deployments. On Vercel, disable embedded scheduling and use the backend project's Vercel Cron Job instead.

## Deployment
- Vercel monorepo setup should use two projects from the same repository:
  - frontend project deployment path: repository root `.`, with project root directory `apps/web`
  - backend project deployment path: repository root `.`
- The frontend Vercel deployment should use project root directory `apps/web` and local config [`apps/web/vercel.json`](../apps/web/vercel.json).
- The backend Vercel deployment uses repository-root [`api/index.py`](../api/index.py), [`requirements.txt`](../requirements.txt), and [`vercel.json`](../vercel.json) so it can import both `apps/server/src` and `packages/quant-core/src`.
- Repository-root [`vercel.json`](../vercel.json) must keep the `/api` and `/api/(.*)` rewrites pointing at `api/index.py`; without those rewrites the FastAPI deployment only exposes the function entrypoint and nested API paths return Vercel `NOT_FOUND`.
- The backend Vercel deployment pins Python via [`../.python-version`](../.python-version) to avoid unsupported wheel builds in Vercel's Python runtime.
- The backend Vercel project must have `CRON_SECRET`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SERVER_CORS_ORIGINS`, and any tracking env vars configured.
- The frontend Vercel project must have `NEXT_PUBLIC_SERVER_URL`, `NEXT_PUBLIC_SUPABASE_URL`, and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` configured.
- Backend cron is declared in [`vercel.json`](../vercel.json) and runs once per day at `09:00 UTC`, which is `17:00 Asia/Shanghai`.

## Git Rules
- Never push directly to `main`.
- Create a feature branch for every change set.
- Run the relevant verification commands before push: at minimum `pnpm test`, `pnpm typecheck`, and `pnpm build` for major changes.
- Push every major completed change set to the remote branch immediately after verification.
- Merge to `main` only through a reviewed pull request.

## Quality Gates
- Run `pnpm lint`.
- Run `pnpm typecheck`.
- Run `pnpm test`.
- Run `pnpm build` before shipping cross-package changes.
- When changing ingestion, universes, indicators, or persistence, validate `GET /api/health` and `GET /api/dashboard/latest` against a configured Supabase environment.
- Update `docs/*.md` in the same change when workflow, runtime contracts, or architecture changes.

## Release Process
- There is no formal packaged release workflow documented in-repo yet.
- Treat `main` as the deployment source of truth until a separate release document exists.
- Before deploy, confirm the latest migration set in `supabase/migrations/` matches the target Supabase project.
- After deploy, validate the dashboard API, latest snapshot date, and latest `fetch_runs` status.

## Incident/Hotfix Path
- Use [`../TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) as the first-response guide.
- Check `GET /api/health` to confirm process health and Supabase mode.
- Check `GET /api/dashboard/latest` and inspect the `warnings` and `latest_run` fields.
- If data is stale, trigger `POST /api/fetch/run` or run the manual fetch CLI.
- If the service was down across one or more trading days, restart the backend first so startup backfill can fill the missing dates before deeper debugging.
- For AkShare schema drift, patch normalization in ingestion/provider code instead of rewriting indicator logic unless the metric definition changed.
