from __future__ import annotations

import pandas as pd

from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class ActiveCapitalRatioIndicator(BaseIndicator):
    indicator_key = "active_capital_ratio"
    display_name = "Active Capital Ratio"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        snapshot = context.market_snapshot.copy()
        snapshot["turnover"] = pd.to_numeric(snapshot["turnover"], errors="coerce").fillna(0.0)
        top_percent = float(definition.config.get("top_percent", 0.1))
        total_turnover = float(snapshot["turnover"].sum())
        if total_turnover <= 0:
            ratio = 0.0
        else:
            top_count = max(1, int(len(snapshot) * top_percent))
            active_turnover = float(snapshot.nlargest(top_count, "turnover")["turnover"].sum())
            ratio = active_turnover / total_turnover
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=ratio,
            value_text=f"{ratio:.2%}",
            unit="ratio",
        )
