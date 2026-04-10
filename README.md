# AlphaScope

AlphaScope is a Turborepo monorepo for a research-engine market monitoring and decision dashboard. It ingests market data from AkShare, persists raw data in Supabase, computes indicators and related universes through a unified `quant-core` engine, and serves a dashboard entrypoint for pre-market planning, post-market review, and cross-day tracking through FastAPI and Next.js.

## Start Here
- Read [`SOUL.md`](./SOUL.md) for repo-wide response and execution rules.
- Read [`AGENTS.md`](./AGENTS.md) for the agent execution contract and required doc-loading order.
- Read [`docs/DOCS_INDEX.md`](./docs/DOCS_INDEX.md) for the maintained documentation map.
- Read [`docs/PRD.md`](./docs/PRD.md) for the current product definition.
- Read [`docs/RAW_DATA_MODEL.md`](./docs/RAW_DATA_MODEL.md) for the maintained raw-layer structure and storage contract.
- Use [`STATUS.md`](./STATUS.md) for the last verified runtime snapshot.
- Use [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) for operational debugging.

## System Summary
- Product shape: backend-driven research-engine market monitoring and decision dashboard
- Core flow: `AkShare -> raw tables -> quant-core -> serving tables -> API -> UI`
- Frontend: Next.js 15
- Backend: FastAPI
- Quant engine: `packages/quant-core`
- Persistence: Supabase Postgres

## Deployment Shape
- Self-hosted backend: embedded startup backfill plus embedded scheduler.
- Vercel frontend: deploy `apps/web` as one Vercel project.
- Vercel frontend: deploy from repository root with project root directory `apps/web`, using [`apps/web/vercel.json`](apps/web/vercel.json).
- Vercel backend: deploy repository root `.` as a separate Python Vercel project, using [`api/index.py`](api/index.py), [`requirements.txt`](requirements.txt), [`vercel.json`](vercel.json), and [`.python-version`](.python-version), with Vercel Cron Jobs hitting `/api/cron/fetch`.
- `NEXT_PUBLIC_SERVER_URL` in the frontend must point to the deployed backend URL.

## Quick Start
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

Open the frontend page:

```bash
pnpm open:frontend
```

## Manual Fetch
```bash
PYTHONPATH=apps/server/src:packages/quant-core/src .venv/bin/python3 -m limitboard_server --trigger manual
```

## Documentation Map
- [`AGENTS.md`](./AGENTS.md)
- [`docs/PRD.md`](./docs/PRD.md)
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
- [`docs/RAW_DATA_MODEL.md`](./docs/RAW_DATA_MODEL.md)
- [`docs/WORKFLOW.md`](./docs/WORKFLOW.md)
- [`docs/DECISIONS.md`](./docs/DECISIONS.md)
- [`docs/REFERENCE.md`](./docs/REFERENCE.md)
