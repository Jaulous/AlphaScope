from __future__ import annotations

import pandas as pd

from quant_core.datasets import get_equity_daily_limit_events, get_equity_daily_quotes
from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class UpLimitCountIndicator(BaseIndicator):
    indicator_key = "up_limit_count"
    display_name = "Up Limit Count"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        limit_events = get_equity_daily_limit_events(context)
        up_events = (
            limit_events[limit_events["event_side"] == "up"].copy()
            if "event_side" in limit_events.columns
            else pd.DataFrame()
        )
        if not up_events.empty:
            up_events["symbol"] = up_events["symbol"].astype(str)
            stocks = [
                {
                    "symbol": str(row["symbol"]),
                    "name": row.get("name"),
                    "board_count": int(row.get("board_count") or 1),
                }
                for _, row in up_events.iterrows()
            ]
            value = len(stocks)
            raw_data = {"stocks": stocks}
        else:
            threshold = float(definition.config.get("threshold", 9.8))
            snapshot = get_equity_daily_quotes(context)
            snapshot["pct_change"] = pd.to_numeric(snapshot["pct_change"], errors="coerce")
            value = int((snapshot["pct_change"] >= threshold).sum())
            raw_data = {"stocks": []}

        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=float(value),
            value_text=str(value),
            unit="stocks",
            raw_data=raw_data,
        )
