from __future__ import annotations

from datetime import date
from multiprocessing import cpu_count, get_context
from typing import Sequence

import pandas as pd

from .ingestion import AkShareProvider
from .registry import IndicatorRegistry
from .types import (
    EngineExecutionPlan,
    EngineResult,
    IndicatorContext,
    IndicatorDefinition,
    IndicatorResult,
    TrackingConfig,
)
from .universe import ActiveThemesUniverse, TrackedEquitiesUniverse


def _compute_indicator_task(
    args: tuple[type, IndicatorContext, IndicatorDefinition],
) -> IndicatorResult:
    indicator_cls, context, definition = args
    indicator = indicator_cls()
    return indicator.compute(context, definition)


class QuantEngine:
    def __init__(
        self,
        provider: AkShareProvider | None = None,
        registry: IndicatorRegistry | None = None,
        use_multiprocessing: bool = True,
    ) -> None:
        self.provider = provider or AkShareProvider()
        self.registry = registry or IndicatorRegistry()
        self.registry.discover()
        self.use_multiprocessing = use_multiprocessing
        self.active_theme_universe = ActiveThemesUniverse()
        self.tracked_equities_universe = TrackedEquitiesUniverse()

    def build_execution_plan(
        self, definitions: Sequence[IndicatorDefinition]
    ) -> EngineExecutionPlan:
        plan = EngineExecutionPlan()
        enabled_definitions = [
            definition for definition in definitions if definition.enabled
        ]
        for definition in enabled_definitions:
            indicator = self.registry.get(definition.type)()
            plan.include_indicator_requirements(indicator.get_requirements(definition))
        return plan

    def run(
        self,
        definitions: Sequence[IndicatorDefinition],
        as_of: date,
        historical_indicator_values: pd.DataFrame | None = None,
        historical_theme_volume: pd.DataFrame | None = None,
        historical_limit_up_pool: pd.DataFrame | None = None,
        stock_kline_history: pd.DataFrame | None = None,
        tracking_config: TrackingConfig | None = None,
    ) -> EngineResult:
        market_snapshot = self.provider.fetch_market_snapshot()
        limit_up_pool = self.provider.fetch_limit_up_pool(as_of)
        concept_boards = self.provider.fetch_concept_board_snapshot()
        return self.run_with_frames(
            definitions=definitions,
            as_of=as_of,
            market_snapshot=market_snapshot,
            limit_up_pool=limit_up_pool,
            concept_boards=concept_boards,
            historical_indicator_values=historical_indicator_values,
            historical_theme_volume=historical_theme_volume,
            historical_limit_up_pool=historical_limit_up_pool,
            stock_kline_history=stock_kline_history,
            tracking_config=tracking_config,
        )

    def run_with_frames(
        self,
        definitions: Sequence[IndicatorDefinition],
        as_of: date,
        market_snapshot: pd.DataFrame,
        limit_up_pool: pd.DataFrame,
        concept_boards: pd.DataFrame,
        historical_indicator_values: pd.DataFrame | None = None,
        historical_theme_volume: pd.DataFrame | None = None,
        historical_limit_up_pool: pd.DataFrame | None = None,
        stock_kline_history: pd.DataFrame | None = None,
        tracking_config: TrackingConfig | None = None,
        preloaded_stock_kline_rows: list[dict] | None = None,
    ) -> EngineResult:
        enabled_definitions = [
            definition for definition in definitions if definition.enabled
        ]
        tracking = tracking_config or TrackingConfig()

        theme_definition = next(
            (item for item in enabled_definitions if item.key == "active_themes"), None
        )
        datasets = {
            "market_snapshot": market_snapshot,
            "limit_up_pool": limit_up_pool,
            "concept_boards": concept_boards,
        }
        if historical_indicator_values is not None:
            datasets["historical_indicator_values"] = historical_indicator_values
        if historical_theme_volume is not None:
            datasets["historical_theme_volume"] = historical_theme_volume
        if historical_limit_up_pool is not None:
            datasets["historical_limit_up_pool"] = historical_limit_up_pool
        if stock_kline_history is not None:
            datasets["stock_kline_history"] = stock_kline_history
        context = IndicatorContext(
            as_of=as_of,
            market_snapshot=market_snapshot,
            limit_up_pool=limit_up_pool,
            concept_boards=concept_boards,
            historical_indicator_values=historical_indicator_values,
            historical_theme_volume=historical_theme_volume,
            historical_limit_up_pool=historical_limit_up_pool,
            stock_kline_history=stock_kline_history,
            active_themes=self.active_theme_universe.select(
                IndicatorContext(
                    as_of=as_of,
                    market_snapshot=market_snapshot,
                    limit_up_pool=limit_up_pool,
                    concept_boards=concept_boards,
                    historical_indicator_values=historical_indicator_values,
                    historical_theme_volume=historical_theme_volume,
                    historical_limit_up_pool=historical_limit_up_pool,
                    stock_kline_history=stock_kline_history,
                    datasets=datasets,
                ),
                theme_definition.config if theme_definition else {},
            ),
            datasets=datasets,
        )

        tasks = [
            (self.registry.get(definition.type), context, definition)
            for definition in enabled_definitions
        ]
        if self.use_multiprocessing and len(tasks) >= 4:
            with get_context("spawn").Pool(
                processes=min(cpu_count(), len(tasks))
            ) as pool:
                results = pool.map(_compute_indicator_task, tasks)
        else:
            results = [_compute_indicator_task(task) for task in tasks]

        theme_rows = [
            {
                "indicator_date": as_of.isoformat(),
                "theme_name": theme.name,
                "turnover": theme.turnover,
                "rank": theme.rank,
                "metadata": theme.metadata,
            }
            for theme in context.active_themes
        ]
        tracked_symbols = self.tracked_equities_universe.select(context, tracking)
        stock_kline_rows = preloaded_stock_kline_rows or self.collect_stock_kline_rows(
            as_of=as_of, symbols=tracked_symbols
        )
        return EngineResult(
            as_of=as_of,
            indicators=results,
            theme_rows=theme_rows,
            stock_kline_rows=stock_kline_rows,
        )

    def collect_stock_kline_rows(
        self,
        as_of: date,
        symbols: Sequence[str],
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        return_errors: bool = False,
    ) -> list[dict] | tuple[list[dict], list[str]]:
        rows: list[dict] = []
        errors: list[str] = []
        start = start_date or as_of
        end = end_date or as_of
        for symbol in symbols:
            try:
                df = self.provider.fetch_stock_kline_daily(
                    symbol=symbol,
                    start_date=start,
                    end_date=end,
                )
            except Exception as exc:
                errors.append(f"{symbol}: {exc}")
                continue
            if df.empty:
                continue
            for _, row in df.iterrows():
                ts = row.get("ts")
                if pd.isna(ts):
                    continue
                rows.append(
                    {
                        "ts": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                        "symbol": row.get("symbol") or symbol,
                        "name": row.get("name"),
                        "open": _safe_float(row.get("open")),
                        "high": _safe_float(row.get("high")),
                        "low": _safe_float(row.get("low")),
                        "close": _safe_float(row.get("close")),
                        "volume": _safe_float(row.get("volume")),
                        "turnover": _safe_float(row.get("turnover")),
                        "amplitude": _safe_float(row.get("amplitude")),
                        "pct_change": _safe_float(row.get("pct_change")),
                        "metadata": {},
                    }
                )
        if return_errors:
            return rows, errors
        return rows


def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
