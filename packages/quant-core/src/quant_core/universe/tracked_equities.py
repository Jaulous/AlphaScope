from __future__ import annotations

import pandas as pd

from quant_core.types import IndicatorContext, TrackingConfig


class TrackedEquitiesUniverse:
    def select(self, context: IndicatorContext, config: TrackingConfig) -> list[str]:
        symbols: list[str] = []

        if not context.market_snapshot.empty:
            snapshot = context.market_snapshot.copy()
            snapshot["turnover"] = pd.to_numeric(
                snapshot["turnover"], errors="coerce"
            ).fillna(0.0)
            symbols.extend(
                snapshot.sort_values("turnover", ascending=False)
                .head(config.top_turnover_count)["symbol"]
                .dropna()
                .astype(str)
                .tolist()
            )

        if (
            not context.limit_up_pool.empty
            and "symbol" in context.limit_up_pool.columns
        ):
            symbols.extend(
                context.limit_up_pool["symbol"]
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
