from __future__ import annotations

from datetime import timedelta

import pandas as pd

from quant_core.indicators.base import BaseIndicator
from quant_core.types import (
    IndicatorContext,
    IndicatorDefinition,
    IndicatorRequirements,
    IndicatorResult,
    StockKlineRequirement,
)


class NShapeLimitUpCountIndicator(BaseIndicator):
    indicator_key = "n_shape_limit_up_count"
    display_name = "N-Shape Limit-Up Count"

    def get_requirements(
        self, definition: IndicatorDefinition
    ) -> IndicatorRequirements:
        lookback_days = int(definition.config.get("lookback_days", 30))
        return IndicatorRequirements(
            historical_limit_up_pool_days=lookback_days,
            stock_kline_requirements=[
                StockKlineRequirement(
                    scope="limit_up_pool",
                    lookback_days=lookback_days,
                    required=True,
                )
            ],
        )

    def compute(
        self, context: IndicatorContext, definition: IndicatorDefinition
    ) -> IndicatorResult:
        if (
            context.limit_up_pool.empty
            or context.historical_limit_up_pool is None
            or context.historical_limit_up_pool.empty
            or context.stock_kline_history is None
            or context.stock_kline_history.empty
        ):
            return IndicatorResult(
                key=definition.key,
                name=definition.name,
                indicator_type=definition.type,
                value_numeric=0.0,
                value_text="0",
                unit="stocks",
                raw_data={"stocks": []},
            )

        lookback_days = int(definition.config.get("lookback_days", 30))
        min_pullback_pct = float(definition.config.get("min_pullback_pct", 5.0))
        min_gap_days = int(definition.config.get("min_gap_days", 2))
        breakout_tolerance_pct = float(
            definition.config.get("breakout_tolerance_pct", 0.0)
        )

        today = context.limit_up_pool.copy()
        today["symbol"] = today["symbol"].astype(str)

        history_pool = context.historical_limit_up_pool.copy()
        history_pool["snapshot_date"] = pd.to_datetime(
            history_pool["snapshot_date"], errors="coerce"
        )
        history_pool["symbol"] = history_pool["symbol"].astype(str)
        history_pool = history_pool.dropna(subset=["snapshot_date"])

        kline_history = context.stock_kline_history.copy()
        kline_history["ts"] = pd.to_datetime(kline_history["ts"], errors="coerce")
        kline_history["symbol"] = kline_history["symbol"].astype(str)
        for column in ("open", "high", "low", "close", "pct_change"):
            kline_history[column] = pd.to_numeric(
                kline_history[column], errors="coerce"
            )
        kline_history = kline_history.dropna(subset=["ts"])

        as_of_ts = pd.Timestamp(context.as_of)
        cutoff = as_of_ts - timedelta(days=lookback_days)
        matched_stocks: list[dict[str, object]] = []

        sorted_today = today.sort_values(
            ["board_count", "symbol"], ascending=[False, True]
        )
        for _, stock in sorted_today.iterrows():
            symbol = str(stock["symbol"])
            symbol_history = (
                kline_history[kline_history["symbol"] == symbol]
                .sort_values("ts")
                .reset_index(drop=True)
            )
            if symbol_history.empty:
                continue

            today_row = symbol_history[symbol_history["ts"].dt.date == context.as_of]
            if today_row.empty:
                continue
            today_row = today_row.iloc[-1]

            prior_limits = history_pool[
                (history_pool["symbol"] == symbol)
                & (history_pool["snapshot_date"] < as_of_ts)
                & (history_pool["snapshot_date"] >= cutoff)
            ].sort_values("snapshot_date", ascending=False)
            if prior_limits.empty:
                continue

            for _, prior_limit in prior_limits.iterrows():
                prior_date = prior_limit["snapshot_date"]
                if pd.isna(prior_date):
                    continue
                if int((as_of_ts - prior_date).days) < min_gap_days:
                    continue

                prior_row = symbol_history[
                    symbol_history["ts"].dt.date == prior_date.date()
                ]
                if prior_row.empty:
                    continue
                prior_row = prior_row.iloc[-1]
                if pd.isna(prior_row["close"]) or float(prior_row["close"]) <= 0:
                    continue
                prior_close = float(prior_row["close"])

                between = symbol_history[
                    (symbol_history["ts"] > prior_date)
                    & (symbol_history["ts"] < as_of_ts)
                ].copy()
                if between.empty:
                    continue

                pullback_candidates = between[pd.notna(between["close"])]
                if pullback_candidates.empty:
                    continue
                trough_row = pullback_candidates.loc[
                    pullback_candidates["close"].idxmin()
                ]
                trough_close = float(trough_row["close"])
                pullback_pct = ((prior_close - trough_close) / prior_close) * 100
                if pullback_pct < min_pullback_pct:
                    continue

                breakout_level = prior_close * (1 - breakout_tolerance_pct / 100)
                if (
                    pd.isna(today_row["close"])
                    or float(today_row["close"]) < breakout_level
                ):
                    continue

                matched_stocks.append(
                    {
                        "symbol": symbol,
                        "name": stock.get("name") or today_row.get("name"),
                        "prior_limit_date": prior_date.date().isoformat(),
                        "pullback_low_date": pd.Timestamp(trough_row["ts"])
                        .date()
                        .isoformat(),
                        "pullback_pct": round(pullback_pct, 2),
                        "today_board_count": int(stock.get("board_count") or 1),
                    }
                )
                break

        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=float(len(matched_stocks)),
            value_text=str(len(matched_stocks)),
            unit="stocks",
            raw_data={"stocks": matched_stocks},
        )
