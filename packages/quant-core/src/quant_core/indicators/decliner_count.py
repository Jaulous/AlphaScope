from __future__ import annotations

import pandas as pd

from quant_core.datasets import get_equity_daily_quotes
from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class DeclinerCountIndicator(BaseIndicator):
    indicator_key = "decliner_count"
    display_name = "Decliner Count"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        quotes = get_equity_daily_quotes(context)
        quotes["pct_change"] = pd.to_numeric(quotes["pct_change"], errors="coerce")
        value = int((quotes["pct_change"] < 0).sum())
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=float(value),
            value_text=str(value),
            unit="stocks",
        )
