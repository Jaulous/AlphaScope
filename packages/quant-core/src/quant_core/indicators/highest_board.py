from __future__ import annotations

import pandas as pd

from quant_core.datasets import get_current_up_limit_events
from quant_core.indicators.base import BaseIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class HighestBoardIndicator(BaseIndicator):
    indicator_key = "highest_board"
    display_name = "Highest Board"

    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        current_up_events = get_current_up_limit_events(context)
        if current_up_events.empty:
            return IndicatorResult(
                key=definition.key,
                name=definition.name,
                indicator_type=definition.type,
                value_numeric=0.0,
                value_text="0",
                unit="boards",
            )
        board_counts = pd.to_numeric(
            current_up_events.get("board_count"), errors="coerce"
        ).fillna(1)
        highest = int(board_counts.max()) if not board_counts.empty else 0
        leaders = (
            current_up_events.loc[board_counts == highest, "name"]
            .dropna()
            .astype(str)
            .tolist()[:8]
        )
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=float(highest),
            value_text=str(highest),
            unit="boards",
            raw_data={"leaders": leaders},
        )
