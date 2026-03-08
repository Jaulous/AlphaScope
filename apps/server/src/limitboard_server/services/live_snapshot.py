from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytz
from quant_core import TrackingConfig
from quant_core.ingestion import AkShareProvider
from quant_core.registry import IndicatorRegistry
from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult
from quant_core.universe import ActiveThemesUniverse, TrackedEquitiesUniverse

from limitboard_server.config import settings
from limitboard_server.defaults import DEFAULT_INDICATOR_DEFINITIONS


def build_empty_dashboard_snapshot(warnings: list[str] | None = None) -> dict[str, Any]:
    timezone = pytz.timezone(settings.scheduler_timezone)
    return {
        "as_of": None,
        "generated_at": datetime.now(timezone).isoformat(),
        "source": "live",
        "storage_mode": "supabase",
        "warnings": warnings or [],
        "market_breadth": {"advancers": 0, "decliners": 0, "unchanged": 0},
        "indicators": [],
        "active_themes": [],
        "tracked_stocks": [],
    }


def build_live_dashboard_snapshot(
    definitions: list[IndicatorDefinition] | None = None,
    historical_indicator_values: pd.DataFrame | None = None,
    historical_theme_volume: pd.DataFrame | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    timezone = pytz.timezone(settings.scheduler_timezone)
    now = datetime.now(timezone)

    resolved_definitions = definitions or [
        IndicatorDefinition(
            key=item["key"],
            type=item["type"],
            name=item["name"],
            enabled=item.get("enabled", True),
            config=item.get("config", {}),
            description=item.get("description"),
        )
        for item in DEFAULT_INDICATOR_DEFINITIONS
    ]
    provider = AkShareProvider(timezone=settings.scheduler_timezone)
    as_of = provider.latest_market_date()
    runtime_warnings = list(warnings or [])

    try:
        market_snapshot = provider.fetch_market_snapshot()
    except Exception as exc:
        market_snapshot = pd.DataFrame()
        runtime_warnings.append(
            f"Market-wide live snapshot unavailable: {exc}. "
            "Breadth and turnover-wide metrics are omitted."
        )

    try:
        limit_up_pool = provider.fetch_limit_up_pool(as_of)
    except Exception as exc:
        limit_up_pool = pd.DataFrame()
        runtime_warnings.append(f"Limit-up pool fetch failed: {exc}")

    try:
        concept_boards = provider.fetch_concept_board_snapshot()
    except Exception as exc:
        concept_boards = pd.DataFrame()
        runtime_warnings.append(f"Concept board snapshot failed: {exc}")

    active_themes = ActiveThemesUniverse().select(
        IndicatorContext(
            as_of=as_of,
            market_snapshot=market_snapshot,
            limit_up_pool=limit_up_pool,
            concept_boards=concept_boards,
            historical_indicator_values=historical_indicator_values,
            historical_theme_volume=historical_theme_volume,
        ),
        (
            next(
                (
                    item.config
                    for item in resolved_definitions
                    if item.enabled and item.key == "active_themes"
                ),
                {},
            )
            or {}
        ),
    )
    context = IndicatorContext(
        as_of=as_of,
        market_snapshot=market_snapshot,
        limit_up_pool=limit_up_pool,
        concept_boards=concept_boards,
        historical_indicator_values=historical_indicator_values,
        historical_theme_volume=historical_theme_volume,
        active_themes=active_themes,
    )

    registry = IndicatorRegistry()
    registry.discover()
    indicators: list[IndicatorResult] = []
    skipped_market_metrics = False
    for definition in resolved_definitions:
        if not definition.enabled:
            continue
        if definition.key == "up_limit_count" and market_snapshot.empty:
            indicators.append(
                IndicatorResult(
                    key=definition.key,
                    name=definition.name,
                    indicator_type=definition.type,
                    value_numeric=float(len(limit_up_pool.index)),
                    value_text=str(len(limit_up_pool.index)),
                    unit="stocks",
                    raw_data={"source": "limit_up_pool"},
                )
            )
            continue
        if market_snapshot.empty and definition.key in {
            "down_limit_count",
            "decliner_count",
            "active_capital_ratio",
            "market_turnover",
        }:
            skipped_market_metrics = True
            continue
        indicator_cls = registry.get(definition.type)
        indicators.append(indicator_cls().compute(context, definition))

    if skipped_market_metrics:
        runtime_warnings.append(
            "Some market-wide indicators were skipped because the full A-share snapshot "
            "could not be fetched in this environment."
        )

    indicator_payload = [
        {
            "key": item.key,
            "title": item.name,
            "type": item.indicator_type,
            "value_numeric": item.value_numeric,
            "value_text": item.value_text,
            "delta": item.delta,
            "unit": item.unit,
            "raw_data": item.raw_data,
            "history": [],
            "indicator_date": as_of.isoformat(),
        }
        for item in indicators
    ]

    theme_indicator = next(
        (item for item in indicators if item.key == "active_themes"), None
    )
    theme_rows = (
        theme_indicator.raw_data.get("themes", []) if theme_indicator else []
    ) or []
    active_themes = [
        {
            "theme_name": row["theme_name"],
            "rank": int(row["rank"]),
            "latest_turnover": float(row["turnover"]),
            "history": row.get("history", []),
            "metadata": row.get("metadata", {}),
        }
        for row in theme_rows
    ]

    stock_history: dict[str, list[dict[str, Any]]] = {}
    stock_meta: dict[str, dict[str, Any]] = {}
    tracking_config = TrackingConfig(
        top_turnover_count=settings.tracking_top_turnover_count,
        limit_up_pool_count=settings.tracking_limit_up_pool_count,
        include_symbols=settings.tracking_symbols,
    )
    tracked_symbols = TrackedEquitiesUniverse().select(context, tracking_config)
    name_map: dict[str, Any] = {}
    for source_df in (market_snapshot, limit_up_pool):
        if source_df.empty or "symbol" not in source_df.columns:
            continue
        subset = source_df.copy()
        subset["symbol"] = subset["symbol"].astype(str)
        if "name" in subset.columns:
            for _, row in (
                subset[["symbol", "name"]].dropna(subset=["symbol"]).iterrows()
            ):
                if row["symbol"] and row["symbol"] not in name_map:
                    name_map[row["symbol"]] = row.get("name")
    stock_kline_rows: list[dict[str, Any]] = []
    for symbol in tracked_symbols:
        try:
            df = provider.fetch_stock_kline_daily(
                symbol=symbol,
                start_date=as_of,
                end_date=as_of,
            )
        except Exception:
            continue
        if df.empty:
            continue
        for _, row in df.iterrows():
            ts = row.get("ts")
            if pd.isna(ts):
                continue
            stock_kline_rows.append(
                {
                    "ts": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                    "symbol": row.get("symbol") or symbol,
                    "name": row.get("name") or name_map.get(symbol),
                    "open": _safe_float(row.get("open")),
                    "high": _safe_float(row.get("high")),
                    "low": _safe_float(row.get("low")),
                    "close": _safe_float(row.get("close")),
                    "volume": _safe_float(row.get("volume")),
                    "turnover": _safe_float(row.get("turnover")),
                    "amplitude": _safe_float(row.get("amplitude")),
                    "pct_change": _safe_float(row.get("pct_change")),
                }
            )

    for row in stock_kline_rows:
        symbol = str(row["symbol"])
        stock_history.setdefault(symbol, []).append(
            {
                "ts": row["ts"],
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "turnover": row.get("turnover"),
                "amplitude": row.get("amplitude"),
                "pct_change": row.get("pct_change"),
            }
        )
        stock_meta[symbol] = row

    tracked_stocks = [
        {
            "symbol": symbol,
            "name": meta.get("name"),
            "latest_close": meta.get("close"),
            "latest_pct_change": meta.get("pct_change"),
            "latest_turnover": meta.get("turnover"),
            "history": stock_history.get(symbol, []),
        }
        for symbol, meta in sorted(
            stock_meta.items(),
            key=lambda item: float(item[1].get("turnover") or 0),
            reverse=True,
        )
    ]
    market_breadth: dict[str, int] | None = None
    if not market_snapshot.empty:
        market_snapshot = market_snapshot.copy()
        market_snapshot["pct_change"] = pd.to_numeric(
            market_snapshot.get("pct_change"), errors="coerce"
        )
        market_breadth = {
            "advancers": int((market_snapshot["pct_change"] > 0).sum()),
            "decliners": int((market_snapshot["pct_change"] < 0).sum()),
            "unchanged": int((market_snapshot["pct_change"] == 0).sum()),
        }

    payload = {
        "as_of": as_of.isoformat(),
        "generated_at": now.isoformat(),
        "source": "live",
        "storage_mode": "supabase",
        "warnings": runtime_warnings,
        "market_breadth": market_breadth,
        "indicators": indicator_payload,
        "active_themes": active_themes,
        "tracked_stocks": tracked_stocks,
    }
    return payload


def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
