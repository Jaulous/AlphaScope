from __future__ import annotations

from datetime import date
from multiprocessing import cpu_count, get_context
from typing import Sequence

import pandas as pd

from .ingestion import AkShareProvider
from .registry import IndicatorRegistry
from .types import (
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

    def run(
        self,
        definitions: Sequence[IndicatorDefinition],
        as_of: date,
        historical_indicator_values: pd.DataFrame | None = None,
        historical_theme_volume: pd.DataFrame | None = None,
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
        context = IndicatorContext(
            as_of=as_of,
            market_snapshot=market_snapshot,
            limit_up_pool=limit_up_pool,
            concept_boards=concept_boards,
            historical_indicator_values=historical_indicator_values,
            historical_theme_volume=historical_theme_volume,
            active_themes=self.active_theme_universe.select(
                IndicatorContext(
                    as_of=as_of,
                    market_snapshot=market_snapshot,
                    limit_up_pool=limit_up_pool,
                    concept_boards=concept_boards,
                    historical_indicator_values=historical_indicator_values,
                    historical_theme_volume=historical_theme_volume,
                ),
                theme_definition.config if theme_definition else {},
            ),
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
        self, as_of: date, symbols: Sequence[str]
    ) -> list[dict]:
        rows: list[dict] = []
        for symbol in symbols:
            try:
                df = self.provider.fetch_stock_kline_daily(
                    symbol=symbol, start_date=as_of, end_date=as_of
                )
            except Exception:
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
        return rows


def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
