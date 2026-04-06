from __future__ import annotations

import pandas as pd

from quant_core.datasets import get_equity_daily_limit_events, get_equity_daily_quotes
from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class DownLimitCountIndicator(BaseIndicator):
    indicator_key = "down_limit_count"
    display_name = "Down Limit Count"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        limit_events = get_equity_daily_limit_events(context)
        down_events = (
            limit_events[limit_events["event_side"] == "down"]
            if "event_side" in limit_events.columns
            else pd.DataFrame()
        )
        if not down_events.empty:
            value = int(len(down_events.index))
        else:
            threshold = float(definition.config.get("threshold", -9.8))
            snapshot = get_equity_daily_quotes(context)
            snapshot["pct_change"] = pd.to_numeric(snapshot["pct_change"], errors="coerce")
            value = int((snapshot["pct_change"] <= threshold).sum())
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=float(value),
            value_text=str(value),
            unit="stocks",
        )
