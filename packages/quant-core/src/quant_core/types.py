from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

import pandas as pd


@dataclass(slots=True)
class IndicatorDefinition:
    key: str
    type: str
    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    description: str | None = None


@dataclass(slots=True)
class ThemeSelection:
    name: str
    turnover: float
    rank: int
    history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StockKlineRequirement:
    scope: Literal["tracked", "limit_up_pool"] = "tracked"
    lookback_days: int = 0
    required: bool = True


@dataclass(slots=True)
class IndicatorRequirements:
    historical_indicator_days: int = 0
    historical_theme_days: int = 0
    historical_limit_up_pool_days: int = 0
    stock_kline_requirements: list[StockKlineRequirement] = field(default_factory=list)


@dataclass(slots=True)
class EngineExecutionPlan:
    indicator_history_days: int = 0
    theme_history_days: int = 0
    limit_up_pool_history_days: int = 0
    tracked_stock_history_days: int = 0
    tracked_stock_history_required: bool = False
    limit_up_pool_stock_history_days: int = 0
    limit_up_pool_stock_history_required: bool = False

    def include_indicator_requirements(
        self, requirements: IndicatorRequirements
    ) -> None:
        self.indicator_history_days = max(
            self.indicator_history_days, requirements.historical_indicator_days
        )
        self.theme_history_days = max(
            self.theme_history_days, requirements.historical_theme_days
        )
        self.limit_up_pool_history_days = max(
            self.limit_up_pool_history_days,
            requirements.historical_limit_up_pool_days,
        )
        for requirement in requirements.stock_kline_requirements:
            if requirement.scope == "tracked":
                self.tracked_stock_history_days = max(
                    self.tracked_stock_history_days, requirement.lookback_days
                )
                self.tracked_stock_history_required = (
                    self.tracked_stock_history_required or requirement.required
                )
                continue
            if requirement.scope == "limit_up_pool":
                self.limit_up_pool_stock_history_days = max(
                    self.limit_up_pool_stock_history_days,
                    requirement.lookback_days,
                )
                self.limit_up_pool_stock_history_required = (
                    self.limit_up_pool_stock_history_required or requirement.required
                )
                continue
            raise ValueError(f"Unsupported stock kline scope: {requirement.scope}")


@dataclass(slots=True)
class IndicatorContext:
    as_of: date
    market_snapshot: pd.DataFrame
    limit_up_pool: pd.DataFrame
    concept_boards: pd.DataFrame
    historical_indicator_values: pd.DataFrame | None = None
    historical_theme_volume: pd.DataFrame | None = None
    historical_limit_up_pool: pd.DataFrame | None = None
    stock_kline_history: pd.DataFrame | None = None
    active_themes: list[ThemeSelection] = field(default_factory=list)
    datasets: dict[str, pd.DataFrame] = field(default_factory=dict)


@dataclass(slots=True)
class IndicatorResult:
    key: str
    name: str
    indicator_type: str
    value_numeric: float | None = None
    value_text: str | None = None
    delta: float | None = None
    unit: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EngineResult:
    as_of: date
    indicators: list[IndicatorResult]
    theme_rows: list[dict[str, Any]] = field(default_factory=list)
    stock_kline_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TrackingConfig:
    top_turnover_count: int = 20
    limit_up_pool_count: int = 20
    include_symbols: list[str] = field(default_factory=list)
