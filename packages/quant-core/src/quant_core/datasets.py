from __future__ import annotations

import pandas as pd

from quant_core.types import IndicatorContext


def get_equity_daily_quotes(context: IndicatorContext) -> pd.DataFrame:
    quotes = context.datasets.get("equity_daily_quotes")
    if quotes is not None and not quotes.empty:
        return quotes.copy()

    snapshot = context.market_snapshot.copy()
    if snapshot.empty:
        return pd.DataFrame(
            columns=[
                "trade_date",
                "symbol",
                "name",
                "close",
                "pct_change",
                "change_amount",
                "volume",
                "turnover",
                "amplitude",
                "turnover_rate",
                "pe_dynamic",
                "is_limit_up",
                "is_limit_down",
            ]
        )

    quotes = snapshot.rename(
        columns={
            "snapshot_date": "trade_date",
            "last_price": "close",
        }
    ).copy()
    quotes["pct_change"] = pd.to_numeric(quotes["pct_change"], errors="coerce")
    quotes["is_limit_up"] = quotes["pct_change"] >= 9.8
    quotes["is_limit_down"] = quotes["pct_change"] <= -9.8
    return quotes


def get_equity_daily_limit_events(context: IndicatorContext) -> pd.DataFrame:
    events = context.datasets.get("equity_daily_limit_events")
    if events is not None and not events.empty:
        return events.copy()

    payload: list[dict[str, object]] = []
    if not context.limit_up_pool.empty:
        for _, row in context.limit_up_pool.iterrows():
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            payload.append(
                {
                    "trade_date": context.as_of.isoformat(),
                    "symbol": symbol,
                    "event_side": "up",
                    "name": row.get("name"),
                    "board_count": row.get("board_count"),
                    "seal_amount": row.get("seal_funds"),
                    "turnover_rate": row.get("turnover_rate"),
                    "first_limit_time": row.get("first_limit_time"),
                    "last_limit_time": row.get("last_limit_time"),
                    "limit_type": "pool",
                }
            )

    if not context.market_snapshot.empty:
        snapshot = context.market_snapshot.copy()
        snapshot["pct_change"] = pd.to_numeric(snapshot["pct_change"], errors="coerce")
        for _, row in snapshot[snapshot["pct_change"] <= -9.8].iterrows():
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            payload.append(
                {
                    "trade_date": context.as_of.isoformat(),
                    "symbol": symbol,
                    "event_side": "down",
                    "name": row.get("name"),
                    "board_count": None,
                    "seal_amount": None,
                    "turnover_rate": row.get("turnover_rate"),
                    "first_limit_time": None,
                    "last_limit_time": None,
                    "limit_type": "threshold_proxy",
                }
            )

    columns = [
        "trade_date",
        "symbol",
        "event_side",
        "name",
        "board_count",
        "seal_amount",
        "turnover_rate",
        "first_limit_time",
        "last_limit_time",
        "limit_type",
    ]
    return pd.DataFrame(payload, columns=columns)


def get_concept_board_daily(context: IndicatorContext) -> pd.DataFrame:
    boards = context.datasets.get("concept_board_daily")
    if boards is not None and not boards.empty:
        renamed = boards.rename(
            columns={
                "trade_date": "snapshot_date",
                "board_name": "theme_name",
            }
        ).copy()
        return renamed

    return context.concept_boards.copy()
