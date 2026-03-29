# AlphaScope PRD

## 1. Executive Summary
AlphaScope is a quant indicator observation platform built on a mainstream quant architecture of `ingestion + universe + indicators + engine`. It is designed for short-term market analysis, where the core value is not a generic dashboard shell but the repeatable computation, storage, comparison, and presentation of a growing library of market indicators. The platform should let operators and researchers define complex indicators, run them against a synchronized daily market context, persist results, and observe both current state and historical evolution through a stable API and UI.

## 2. Problem Statement
### Who has this problem?
- The project owner and future internal users who need a reliable way to observe short-term market structure through custom indicators.
- Engineers maintaining a quant workflow who need one coherent place to add, test, and operate new indicators.

### What is the problem?
- Existing retail market tools surface scattered metrics but rarely provide a coherent, extensible indicator computation stack tailored to the exact signals the operator wants to track.
- Ad hoc scripts make it easy to compute one metric once, but hard to maintain a durable indicator platform with shared context, history, and operational safety.

### Why is it painful?
- Indicator logic drifts when data fetch, universe selection, and metric computation are spread across unrelated scripts.
- Without persisted raw data and serving outputs, debugging stale or partial signals is slow and unreliable.
- Without a unified observation surface, it is difficult to compare indicator behavior across trading days and validate whether a signal is actually useful.

### Evidence
- The current repository already evolved away from an editable whiteboard into a backend-driven market surface, indicating that computed signal observation is the real product center.
- The existing codebase invests heavily in a unified `quant-core`, raw/serving storage, `fetch_runs`, and historical series rendering, which directly supports an indicator platform rather than a canvas product.

## 3. Target Users & Personas
### Primary Persona: Operator-Researcher
- Runs daily market observation workflows.
- Cares about signal quality, timeliness, and historical continuity.
- Needs to inspect current indicator values, component stocks, active themes, and tracked equities in one place.

### Secondary Persona: Quant Engineer
- Extends ingestion, universes, and indicator plugins.
- Needs deterministic execution, simple extension points, and clear operational contracts.

### Jobs To Be Done
- “When a new trading day closes, help me compute and inspect my key market indicators from one consistent market context.”
- “When I invent a new signal, help me add it without rewriting unrelated ingestion or UI code.”
- “When data sources partially fail, help me preserve trusted historical outputs and explain what degraded.”

## 4. Strategic Context
### Business Goals
- Make AlphaScope the canonical internal surface for daily signal observation.
- Reduce friction for adding new indicators from idea to productionized observation.
- Improve confidence in daily signal correctness through persistence, history, and run metadata.

### Market Opportunity
- The immediate opportunity is not broad retail distribution; it is building a strong internal quant foundation that can later support richer research, screening, ranking, and strategy workflows.

### Competitive Landscape
- Generic market dashboards optimize for breadth of coverage, not indicator extensibility.
- Notebook workflows optimize for flexibility, not operational consistency.
- AlphaScope should sit in between: research-friendly architecture with productized daily operation.

### Why Now?
- The repository already contains the right architectural primitives: raw data persistence, a unified quant engine, historical series storage, and a UI for observation.
- The main remaining risk is product ambiguity. Locking the PRD now prevents future regressions back into “dashboard shell” or “whiteboard” behavior.

## 5. Solution Overview
### High-Level Description
Build AlphaScope as a modular indicator observation platform where indicators are first-class products. The platform ingests daily market data, reconstructs one synchronized market context, computes enabled indicators plus related universes, persists both raw and serving layers, and exposes results through API and UI.

### User Flow
1. Operator configures indicator definitions and runtime environment.
2. Scheduler, manual CLI, or on-demand API triggers the daily fetch pipeline.
3. Raw market datasets are fetched and persisted.
4. `quant-core` builds an execution plan and computes indicators from a synchronized context.
5. Indicator results, active themes, tracked equities, and run metadata are persisted.
6. UI and API expose current values, histories, and supporting details for observation.

### Key Features
- Unified indicator plugin system with clear extension points.
- Deterministic daily execution plan based on indicator requirements.
- Persisted raw and serving data model for replayability and fallback.
- Historical series for indicators, themes, and tracked stocks.
- Operational status visibility through `fetch_runs` and warnings.
- Read-only UI focused on signal observation, not manual editing.

## 6. Success Metrics
### Primary Metric
- Number of production-useful indicators that can be added and observed through the standard pipeline without bespoke infrastructure work.

### Secondary Metrics
- Daily snapshot freshness for the latest valid trading day.
- Successful fetch run rate.
- Share of indicator calculations completed without missing required datasets.
- Time to add a new indicator from definition to visible output.

### Initial Targets
- Support at least 10 stable daily indicators through the unified engine.
- Maintain latest snapshot freshness to the most recent trading day on each fetch cycle.
- Expose run status and warnings for 100% of fetch attempts.
- Keep new indicator onboarding to one plugin file plus one definition row in the normal case.

## 7. User Stories & Requirements
### Epic Hypothesis
If AlphaScope standardizes around a unified quant indicator architecture, then operators will be able to observe complex signals more reliably and engineers will be able to expand the signal library with much lower coordination cost.

### User Stories
#### Story 1: Add Indicator
As a quant engineer, I want to add a new indicator by implementing one plugin contract so that new signals can be shipped without changing unrelated parts of the pipeline.

Acceptance criteria:
- A new indicator can declare its own data requirements.
- The engine aggregates those requirements into a single execution plan.
- The indicator can be enabled through `indicator_definitions`.

#### Story 2: Observe Current Signal State
As an operator, I want to see the latest indicator values and supporting stock/theme context so that I can quickly judge current market structure.

Acceptance criteria:
- The latest snapshot includes indicators, active themes, tracked stocks, warnings, and latest run metadata.
- Indicators with supporting stock lists can expose those constituents in the UI payload.

#### Story 3: Observe Historical Evolution
As an operator, I want to compare current indicator values against recent history so that I can see acceleration, decay, and regime changes.

Acceptance criteria:
- Dashboard payloads include historical series for indicators, themes, and tracked stocks when available.
- UI renders these historical series clearly.

#### Story 4: Survive Partial Data Failure
As an operator, I want the platform to preserve trusted historical outputs when a critical source degrades so that one bad upstream day does not destroy the observation surface.

Acceptance criteria:
- Fetch pipeline retries sources.
- Existing raw data can be reused for the same trading day when appropriate.
- Existing serving snapshots are preserved when critical raw sources are incomplete.
- Run metadata records warnings and source-level statuses.

### Edge Cases And Constraints
- Non-trading days must map to the latest valid trading day.
- AkShare schema drift must be handled in ingestion/provider normalization, not indicator logic.
- Indicators that require stock history must declare it explicitly.
- Supabase remains the required persistence layer for current operation.

## 8. Out of Scope
- Manual canvas editing or whiteboard composition.
- Intraday execution, broker routing, or order management.
- Full research notebook replacement.
- Multi-tenant permissions and collaboration workflows.
- Arbitrary persistence backends beyond Supabase in the current phase.

## 9. Dependencies & Risks
### Technical Dependencies
- AkShare data availability and schema stability.
- Supabase schema correctness and write access.
- Python `quant-core` execution and Next.js/FastAPI integration.

### External Dependencies
- China-market trading calendar behavior.
- Third-party market data latency and outages.

### Risks And Mitigations
- Risk: product ambiguity regresses the repo into a generic dashboard.
  - Mitigation: document PRD and remove old whiteboard runtime paths.
- Risk: upstream schema drift breaks indicators.
  - Mitigation: keep normalization concentrated in ingestion and validate source statuses in `fetch_runs`.
- Risk: indicator growth creates fragmented logic.
  - Mitigation: enforce the unified plugin contract and shared execution plan.

## 10. Open Questions
- Should indicator definitions stay database-configured only, or also gain a versioned file-based registry for reviewability?
- Which indicators are considered tier-1 “core market structure” signals vs experimental signals?
- Does the next phase prioritize more indicator breadth, richer historical analytics, or a dedicated research comparison view?
- How much of the current `limitboard_*` naming should be retired versus tolerated as transitional internal naming?
