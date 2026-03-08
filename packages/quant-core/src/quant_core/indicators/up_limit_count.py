from __future__ import annotations

import pandas as pd

from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class UpLimitCountIndicator(BaseIndicator):
    indicator_key = "up_limit_count"
    display_name = "Up Limit Count"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        if not context.limit_up_pool.empty:
            pool = context.limit_up_pool.copy()
            pool["symbol"] = pool["symbol"].astype(str)
            stocks = [
                {
                    "symbol": str(row["symbol"]),
                    "name": row.get("name"),
                    "board_count": int(row.get("board_count") or 1),
                }
                for _, row in pool.iterrows()
            ]
            value = len(stocks)
            raw_data = {"stocks": stocks}
        else:
            threshold = float(definition.config.get("threshold", 9.8))
            snapshot = context.market_snapshot.copy()
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
