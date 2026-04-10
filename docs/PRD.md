# AlphaScope PRD

## 1. Executive Summary
AlphaScope is not a zero-to-one greenfield product. The next phase evolves the current `AkShare -> raw -> quant-core -> serving -> API -> dashboard` system into a research-engine market monitoring and decision interface for short-term trading analysis. The primary entry is a data dashboard that supports three recurring moments: pre-market planning, post-market review, and cross-day tracking. The product center is a strong data foundation plus strong indicator computation, while the upper presentation layer intentionally stays basic in this phase. Indicators are the first-class product object, and the core goal is to let operators and engineers rapidly define, compute, combine, validate, display, and iterate trading-related indicators on top of one synchronized market context.

### Direction Convergence
AlphaScope's next phase is not "hypothesis workbench first." It is a research-oriented data dashboard built on a strong data foundation and a strong indicator-computation engine, optimized for rapidly defining, computing, combining, presenting, and iterating market indicators.

## 2. Problem Statement
### Who has this problem?
- The project owner and future internal users who need one reliable surface for pre-market planning, post-market review, and cross-day tracking through custom indicators.
- Engineers maintaining a quant workflow who need one coherent place to add, test, combine, and operate new indicators without rebuilding the surrounding pipeline.

### What is the problem?
- Existing retail market dashboards surface scattered metrics, but they rarely provide a coherent, extensible indicator engine tailored to the exact signals the operator wants to define and iterate.
- Notebook and ad hoc script workflows make it easy to compute one metric once, but hard to maintain a durable research-and-monitoring system with shared context, history, composition, and operational safety.
- The current AlphaScope codebase already contains the right technical foundation, but without a sharper product definition future work could drift toward richer surface interaction instead of indicator research velocity.

### Why is it painful?
- Indicator logic drifts when data fetch, universe selection, composition, and metric computation are spread across unrelated scripts.
- Without persisted raw data and serving outputs, debugging stale or partial signals is slow and unreliable.
- Without one dashboard organized around the decision cycle, data display stays passive and does not reliably support pre-market planning, post-market review, or cross-day validation.
- Without a strong reusable data-and-compute layer, each new indicator idea risks turning into bespoke ingestion, storage, or UI work.

### Evidence
- The current repository already evolved away from an editable whiteboard into a backend-driven market dashboard backed by persisted raw and serving data.
- The existing codebase invests heavily in unified `quant-core` execution, Raw V2 storage, `fetch_runs`, and historical series rendering, which directly supports a research engine rather than a canvas or hypothesis-workbench product.
- The maintained docs and runtime already standardize the system around `ingestion + universe + indicators + engine`, making indicator computation the durable product center.

## 3. Target Users & Personas
### Primary Persona: Operator-Researcher
- Runs a repeated decision workflow across pre-market planning, post-market review, and cross-day tracking.
- Cares about signal quality, timeliness, historical continuity, and whether indicators are actually decision-useful.
- Needs to inspect current indicator values, supporting stocks, active themes, tracked equities, and recent changes in one place.

### Secondary Persona: Quant Engineer
- Extends ingestion, universes, and indicator plugins.
- Needs deterministic execution, simple extension points, and clear operational contracts.

### Jobs To Be Done
- “Before the market opens, help me review the latest valid trading-day snapshot so I can prepare a plan.”
- “After the market closes, help me compute and inspect fresh indicator changes from one consistent market context.”
- “Across trading days, help me track whether a signal is strengthening, decaying, confirming, or failing.”
- “When I invent a new signal, help me define, compute, combine, and validate it without rewriting unrelated ingestion or UI code.”
- “When data sources partially fail, help me preserve trusted historical outputs and explain what degraded.”

## 4. Strategic Context
### Product Direction Guardrails
- Product type: continue evolving the current AlphaScope system, not a zero-to-one restart.
- Direction mainline: monitoring and decision interface.
- Target moments: pre-market planning, post-market review, and cross-day tracking.
- Primary entry: data dashboard.
- Product center: strong data capability plus strong computation capability; richer presentation remains secondary in this phase.
- Product positioning: research-engine product.
- First-class citizen: indicator computation.

### Business Goals
- Make AlphaScope the canonical internal entry for daily market monitoring and decision support.
- Reduce friction for moving an indicator from idea to computed, comparable dashboard output.
- Improve confidence in daily signal correctness through persistence, history, and run metadata.
- Keep upper-layer presentation intentionally simple while the reusable data and compute base compounds.

### Market Opportunity
- The immediate opportunity is not broad retail distribution. It is to build a strong internal research engine that can later support richer screening, ranking, validation, and strategy workflows.

### Competitive Landscape
- Generic market dashboards optimize for breadth of coverage and polished presentation, not rapid custom-indicator iteration.
- Notebook workflows optimize for flexibility, not operational continuity, reuse, or daily decision cadence.
- Hypothesis or whiteboard tools optimize for idea capture, not synchronized market computation or stable daily monitoring.
- AlphaScope should sit in between: a research-engine architecture underneath and a productized decision dashboard on top.

### Why Now?
- The repository already contains the right architectural primitives: raw data persistence, a unified quant engine, historical series storage, and a dashboard entrypoint.
- The main remaining risk is product ambiguity. Locking the PRD now prevents future regressions toward generic dashboard-shell work or hypothesis-workbench behavior.

## 5. Solution Overview
### High-Level Description
Build AlphaScope as a research-oriented monitoring and decision dashboard where indicators are the first-class product object. The platform ingests and persists daily market data, reconstructs one synchronized market context, computes enabled indicators and related universes, supports rapid indicator combination and validation, persists both raw and serving layers, and exposes the latest usable state through a stable API and a basic but reliable dashboard.

### Product Principles
- Data and compute first, presentation second.
- One synchronized market context per trading day.
- New indicators should fit the standard engine, not force bespoke infrastructure.
- The dashboard should help decisions quickly, not become a heavy editing surface.

### User Flow
1. Operator or engineer configures indicator definitions, combinations, and runtime environment.
2. Scheduler, manual CLI, or on-demand API triggers the daily fetch pipeline.
3. Raw market datasets are fetched and persisted.
4. `quant-core` builds an execution plan and computes indicators from a synchronized context.
5. Indicator results, active themes, tracked equities, historical context, and run metadata are persisted.
6. The dashboard supports the three target moments:
   - pre-market planning from the latest valid trading-day snapshot
   - post-market review from the fresh close-of-day snapshot
   - cross-day tracking from recent historical comparisons

### Key Features
- Unified indicator plugin system with clear extension points.
- Deterministic daily execution plan based on indicator requirements.
- Rapid path to define, combine, and validate new indicators within the standard pipeline.
- Persisted raw and serving data model for replayability and fallback.
- Historical series for indicators, themes, and tracked stocks.
- Operational status visibility through `fetch_runs` and warnings.
- Dashboard entrypoint focused on monitoring and decision support, not manual editing.

## 6. Success Metrics
### Primary Metric
- Time and friction required to move a trading-relevant indicator from idea to computed, comparable dashboard output.

### Secondary Metrics
- Number of production-useful indicators and indicator combinations supported through the standard pipeline without bespoke infrastructure work.
- Daily snapshot freshness for the latest valid trading day.
- Successful fetch run rate.
- Share of indicator calculations completed without missing required datasets.
- Time to validate a new indicator against recent history in the normal workflow.

### Initial Targets
- Support at least 10 stable daily indicators through the unified engine.
- Maintain latest snapshot freshness to the most recent valid trading day for each pre-market and post-market cycle.
- Expose run status and warnings for 100% of fetch attempts.
- Keep new indicator onboarding to one plugin file plus one definition row in the normal case.
- Keep recent history available in the standard dashboard workflow so cross-day validation does not require a separate notebook by default.

## 7. User Stories & Requirements
### Epic Hypothesis
If AlphaScope treats indicator computation as the first-class product and uses the dashboard as a monitoring-and-decision interface, then operators will be able to plan, review, and track market structure more reliably while engineers expand the signal library with much lower coordination cost.

### User Stories
#### Story 1: Add Indicator
As a quant engineer, I want to add a new indicator by implementing one plugin contract so that new signals can be shipped without changing unrelated parts of the pipeline.

Acceptance criteria:
- A new indicator can declare its own data requirements.
- The engine aggregates those requirements into a single execution plan.
- The indicator can be enabled through `indicator_definitions`.
- The indicator can appear in the standard dashboard output without bespoke API or page wiring in the normal case.

#### Story 2: Combine Indicators Into A Reusable View
As an operator-researcher, I want to combine related indicators into one reusable dashboard view so that I can inspect one market regime from multiple angles without building a custom page each time.

Acceptance criteria:
- Related indicators can be grouped or sequenced through standard configuration in the normal case.
- The standard dashboard payload can surface multiple indicator families from one synchronized snapshot.
- Adding one more indicator to the view does not require rewriting the fetch pipeline.

#### Story 3: Pre-Market Planning
As an operator-researcher, I want to open one dashboard before the market opens and review the latest valid trading-day indicators, active themes, tracked stocks, and recent deltas so that I can form a plan for the coming session.

Acceptance criteria:
- The latest snapshot remains available on non-trading days and before the next open by mapping to the latest valid trading day.
- The latest snapshot includes indicators, active themes, tracked stocks, warnings, and latest run metadata.
- The dashboard exposes enough recent context to support plan-making instead of only point-in-time display.

#### Story 4: Post-Market Review
As an operator-researcher, I want to review the fresh close-of-day snapshot and see how key indicators changed so that I can understand what happened and update tomorrow's focus.

Acceptance criteria:
- After the daily fetch completes, the latest snapshot includes current values plus recent history for supported indicators.
- Indicators with supporting stock lists can expose those constituents in the dashboard payload.
- Run metadata makes degraded or fallback data conditions visible.

#### Story 5: Cross-Day Tracking And Validation
As an operator-researcher, I want to compare indicator behavior across recent trading days so that I can judge whether a signal is strengthening, decaying, confirming, or failing.

Acceptance criteria:
- Dashboard payloads include historical series for indicators, themes, and tracked stocks when available.
- Historical comparisons are aligned on valid trading days.
- The UI renders these comparisons through basic but reliable components instead of requiring a separate analysis surface by default.

#### Story 6: Survive Partial Data Failure
As an operator, I want the platform to preserve trusted historical outputs when a critical source degrades so that one bad upstream day does not destroy the decision surface.

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
- Rich surface interaction must not outrun the maturity of the data and compute layer.

## 8. Out of Scope
- Starting over with a new greenfield product instead of evolving the current system.
- Manual canvas editing or whiteboard composition.
- Hypothesis-workbench-first product behavior.
- Heavy collaboration, annotation, or note-taking features as the primary entry surface.
- Intraday execution, broker routing, or order management.
- Full research notebook replacement.
- Multi-tenant permissions and collaboration workflows.
- Arbitrary persistence backends beyond Supabase in the current phase.
- Rich presentation experiments that require bespoke infrastructure before the core indicator engine is ready.

## 9. Dependencies & Risks
### Technical Dependencies
- AkShare data availability and schema stability.
- Supabase schema correctness and write access.
- Python `quant-core` execution and Next.js/FastAPI integration.

### External Dependencies
- China-market trading calendar behavior.
- Third-party market data latency and outages.

### Risks And Mitigations
- Risk: product ambiguity regresses the repo into a generic dashboard or hypothesis-workbench direction.
  - Mitigation: document the next-phase PRD around the three target moments, the dashboard entrypoint, and the data/compute-first priority.
- Risk: upstream schema drift breaks indicators.
  - Mitigation: keep normalization concentrated in ingestion and validate source statuses in `fetch_runs`.
- Risk: indicator growth creates fragmented logic.
  - Mitigation: enforce the unified plugin contract and shared execution plan.
- Risk: UI work grows faster than reusable indicator/data capability.
  - Mitigation: require new feature work to improve indicator definition, computation, combination, validation, or decision-cycle usability.

## 10. Open Questions
- Which indicator families should form the first decision-oriented core pack for pre-market, post-market, and cross-day workflows?
- Should indicator definitions and indicator grouping stay database-configured only, or also gain a versioned file-based registry for reviewability?
- What is the minimum dashboard primitive set needed in this phase: cards, ranked lists, time-series, delta views, and constituent drilldowns?
- How much of the current `limitboard_*` naming should be retired versus tolerated as transitional internal naming?
