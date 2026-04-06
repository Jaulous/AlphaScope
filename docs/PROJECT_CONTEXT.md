# Project Context

## Purpose
Define why this project exists and what it should or should not do.

## When To Update
- Problem statement, target users, goals, or constraints change.

## Minimum Sections
- Problem Statement
- Goals
- Non-Goals
- Target Users
- Scope and Constraints

## Problem Statement
AlphaScope exists to provide a reliable quant indicator observation platform for short-term trading analysis without requiring users to manually gather raw market breadth, theme turnover, limit-up pool, tracked equity data, and custom signal calculations from multiple sources. The product replaces an earlier editable whiteboard shape with a backend-computed system where indicator computation is the core value and the UI is the observation surface.

## Goals
- Produce a deterministic daily indicator snapshot from a unified backend pipeline.
- Persist both raw inputs and serving outputs so the dashboard can serve stored data instead of recomputing ad hoc on every request.
- Redesign the raw layer so it preserves enough direct-source data to support a future library of roughly `100+` indicators without repeated schema churn.
- Keep theme selection, tracked equities, and indicator computation synchronized to the same trading day context.
- Support local development and operator-triggered fetches with the same core fetch pipeline used by scheduled and on-demand runs.
- Expose enough ingestion status to diagnose stale or partial market snapshots.
- Make new indicator onboarding cheap enough that the platform can grow into a durable signal library.

## Non-Goals
- AlphaScope is not an editable whiteboard or collaborative canvas product.
- The frontend is not the source of truth for indicator logic, market calculations, universe policies, or theme ranking.
- The system does not target full intraday trading execution or broker integration.
- The project does not currently support a non-Supabase persistence backend.

## Target Users
- Primary: the repo owner and internal operators maintaining a daily China-market indicator observation surface.
- Secondary: engineers or agents extending indicators, universe policies, API endpoints, or dashboard presentation.
- Readers of the UI consume backend-computed market state and signal history; they are not expected to edit the underlying data model from the UI.

## Scope and Constraints
- Market data source is primarily AkShare, so schema drift and source instability are ongoing external constraints.
- Supabase is required for persistence and serving. Missing `SUPABASE_URL` or `SUPABASE_SECRET_KEY` blocks dashboard data availability.
- Daily execution is keyed to the latest confirmed trading day; weekends and holidays intentionally backfill the most recent trading day.
- The raw layer should be treated as a durable research substrate, not a narrow cache of only the current dashboard's required inputs.
- The repository is a monorepo with a mixed Node.js and Python toolchain.
- Local Node work on this machine must use `nvm` with Node `v24.14.0` and `corepack`-managed `pnpm`.
- Python packages require Python `>=3.11`.
