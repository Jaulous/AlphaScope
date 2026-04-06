from __future__ import annotations

import pandas as pd

from quant_core.datasets import get_equity_daily_limit_events, get_equity_daily_quotes
from quant_core.types import IndicatorContext, TrackingConfig


class TrackedEquitiesUniverse:
    def select(self, context: IndicatorContext, config: TrackingConfig) -> list[str]:
        symbols: list[str] = []

        snapshot = get_equity_daily_quotes(context)
        if not snapshot.empty:
            snapshot["turnover"] = pd.to_numeric(snapshot["turnover"], errors="coerce").fillna(0.0)
            symbols.extend(
                snapshot.sort_values("turnover", ascending=False)
                .head(config.top_turnover_count)["symbol"]
                .dropna()
                .astype(str)
                .tolist()
            )

        limit_events = get_equity_daily_limit_events(context)
        up_events = (
            limit_events[limit_events["event_side"] == "up"]
            if "event_side" in limit_events.columns
            else pd.DataFrame()
        )
        if not up_events.empty and "symbol" in up_events.columns:
            symbols.extend(
                up_events["symbol"]
                .dropna()
                .astype(str)
                .head(config.limit_up_pool_count)
                .tolist()
            )

        symbols.extend([symbol for symbol in config.include_symbols if symbol])

        seen: set[str] = set()
        ordered: list[str] = []
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                ordered.append(symbol)
        return ordered
