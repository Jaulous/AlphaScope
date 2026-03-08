from __future__ import annotations

import pandas as pd

from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class MarketTurnoverIndicator(BaseIndicator):
    indicator_key = "market_turnover"
    display_name = "Market Turnover"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        snapshot = context.market_snapshot.copy()
        snapshot["turnover"] = pd.to_numeric(snapshot["turnover"], errors="coerce").fillna(0.0)
        total_turnover = float(snapshot["turnover"].sum())
        unit = definition.config.get("display_unit", "CNY")
        display_value = total_turnover / 100000000 if unit == "100M" else total_turnover
        display_text = f"{display_value:,.2f}{'B' if unit == '100M' else ''}"
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=total_turnover,
            value_text=display_text,
            unit=unit,
        )
