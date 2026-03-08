from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

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
