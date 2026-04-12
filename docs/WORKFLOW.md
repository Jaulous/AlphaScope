# Workflow

## Purpose
Capture the preferred engineering workflow for this project, with extra emphasis on recurring pitfalls, operator habits, and agent guidance that help work go smoothly.

## When To Update
- Commands, CI checks, release flow, or environments change.
- A recurring mistake, debugging pattern, or operational lesson should be written down for future agents.

## Minimum Sections
- Local Development
- Working Heuristics
- Quality Gates
- Release Process
- Incident/Hotfix Path

## How To Read This Doc
- Treat this document as the project's maintained working guidance, not as a claim that every safeguard is enforced automatically by tooling.
- Prefer the documented workflow unless there is a deliberate reason to diverge.
- When you hit a pitfall that costs real time, add the lesson here if it is likely to recur.

## Local Development
```bash
pnpm install
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/quant-core -e apps/server
cp .env.example .env
./scripts/start-project.sh
```

One-click local startup wrappers:

```bash
./scripts/start-project.sh
./scripts/start-web.sh
./scripts/start-server.sh
```

- `./scripts/start-project.sh` loads `nvm`, enables `corepack`, activates `.venv`, and starts the full project.
- `./scripts/start-web.sh` loads `nvm`, enables `corepack`, and starts only the frontend.
- `./scripts/start-server.sh` loads `nvm`, enables `corepack`, activates `.venv`, and starts only the backend.
- Matching `pnpm` aliases are also available: `pnpm start:project`, `pnpm open:web`, and `pnpm dev`.
- If both frontend and backend listeners are already up, `./scripts/start-project.sh` exits cleanly and prints the reuse URLs instead of failing deep inside Turborepo with a raw port-bind error.
- If only one required listener port is already occupied, the startup wrappers fail fast with the occupied port, the current listener, and the reuse URL so the operator can distinguish "AlphaScope is already running" from "some other process is blocking startup".

Backend-only development:

```bash
./scripts/start-server.sh
```

Frontend-only development:

```bash
./scripts/start-web.sh
```

Open the frontend page:

```bash
pnpm open:frontend
```

Supabase inspection and validation:

```bash
# If the repo is linked to the target Supabase project
supabase migration list --linked
supabase db query --linked "select now() as ts;"
supabase inspect db table-stats --linked
```

- Prefer the local `supabase` CLI for migration state, SQL probes, and table/runtime inspection instead of ad hoc one-off scripts.
- If this repo is not linked to the target project yet, run `supabase link --project-ref <ref>` first or use the same commands with `--db-url`.

Manual fetch through the packaged Python entrypoint:

```bash
PYTHONPATH=apps/server/src:packages/quant-core/src .venv/bin/python3 -m limitboard_server --trigger manual
```

Startup behavior:

- When the backend process starts, it immediately serves requests, starts the scheduler, and runs missed trading-day backfill in the background.
- Before the final scheduled run of the day, startup catch-up only requires snapshots through the previous trading day.
- Embedded scheduler is intended for long-running deployments. On Vercel, disable embedded scheduling and use the backend project's Vercel Cron Job instead.

## Working Heuristics
- Read `docs/PRD.md` before changing product shape, user-facing behavior, or feature scope.
- Read `docs/RAW_DATA_MODEL.md` before changing raw tables, storage grain, or ingestion-to-raw mappings.
- Do not treat the frontend as the source of truth for market logic, indicator logic, universe policy, or fetch orchestration.
- For AkShare schema drift, patch normalization in ingestion/provider code before touching indicator business logic.
- When a fetch or dashboard bug looks data-related, inspect persisted raw and serving data before rewriting computation code.
- Keep changes traceable: if a code change alters architecture, workflow, or storage contracts, update the matching docs in the same change.
- Use `STATUS.md` for the latest verified runtime facts and `TROUBLESHOOTING.md` for step-by-step incident response instead of recreating those notes ad hoc.

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
- Treat a change as an important milestone when it changes any of these repo facts:
  - database schema, table grain, or migration state
  - indicator logic, universe policy, or any computation output
  - fetch/scheduler/backfill/retry/degrade behavior
  - deployment shape, environment contract, or runtime entrypoint
  - production data state through migration, backfill, cutover, or manual repair
  - completion of a separately verifiable feature slice or refactor stage
- Run the relevant verification commands before push: at minimum `pnpm test`, `pnpm typecheck`, and `pnpm build` for major changes.
- Every important milestone must end with `verify -> commit -> push -> update CHANGELOG`; if the milestone changes current runtime state, also update [`../STATUS.md`](../STATUS.md).
- Use the same important-milestone definition for both Git maintenance and `CHANGELOG.md`; do not create a second looser or stricter threshold for changelog entries.
- `git diff --check` is only a patch-hygiene check. It does not replace functional verification, `commit`, or `push`.
- Push every major completed change set to the remote branch immediately after verification.
- If multiple milestones are sitting together in the local worktree, split them into separate commits before push instead of shipping one mixed batch.
- After each important milestone, make sure the local branch, local commits, and remote tracking branch are in sync before stopping work.
- Merge to `main` only through a reviewed pull request.

## Quality Gates
- Prefer these checks as the default pre-push verification path; some are conventions and operator expectations, not necessarily fully enforced CI gates.
- Run `pnpm lint`.
- Run `pnpm typecheck`.
- Run `pnpm test`.
- Run `pnpm build` before shipping cross-package changes.
- When changing ingestion, universes, indicators, or persistence, validate `GET /api/health` and `GET /api/dashboard/latest` against a configured Supabase environment.
- When changing dashboard loading or API proxy behavior, verify both the happy path and a slow-upstream path so the UI does not show empty-state content while requests are still pending.
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
