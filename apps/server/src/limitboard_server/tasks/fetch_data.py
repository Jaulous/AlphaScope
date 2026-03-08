from __future__ import annotations

from datetime import datetime
from time import sleep
from typing import Any, Callable

import pandas as pd
import pytz
from quant_core import QuantEngine, TrackingConfig
from quant_core.types import IndicatorContext, IndicatorDefinition

from limitboard_server.config import settings
from limitboard_server.db.supabase_store import SupabaseStore
from limitboard_server.defaults import DEFAULT_INDICATOR_DEFINITIONS

SourceFetcher = Callable[[], pd.DataFrame]
RawReader = Callable[[], pd.DataFrame]

_FETCH_RETRY_DELAYS = (1.0, 3.0, 8.0)


def run_daily_fetch(
    *,
    trigger: str = "manual",
    force_non_trading: bool = False,
) -> dict[str, Any]:
    if not settings.supabase_enabled:
        raise RuntimeError(
            "Supabase persistence is required. Configure SUPABASE_URL and SUPABASE_SECRET_KEY."
        )

    store = SupabaseStore(
        supabase_url=settings.supabase_url,
        secret_key=settings.supabase_server_key,
        board_slug=settings.supabase_board_slug,
    )
    timezone = pytz.timezone(settings.scheduler_timezone)
    engine = QuantEngine(use_multiprocessing=settings.engine_parallelism)
    reference_date = datetime.now(timezone).date()
    is_trading_day = engine.provider.is_trading_day(reference_date)
    as_of = engine.provider.latest_market_date(reference_date)

    if not is_trading_day and trigger == "scheduler" and not force_non_trading:
        payload = {
            "status": "skipped_non_trading_day",
            "as_of": as_of.isoformat(),
            "indicator_count": 0,
            "theme_count": 0,
            "stock_kline_count": 0,
            "persisted": False,
            "warnings": ["Scheduler skipped because today is not a trading day."],
            "raw_market_snapshot_count": 0,
            "raw_limit_up_pool_count": 0,
            "raw_concept_board_count": 0,
            "raw_stock_kline_count": 0,
        }
        store.record_fetch_run(
            trigger=trigger,
            reference_date=reference_date,
            target_date=as_of,
            status=payload["status"],
            skipped_reason="non_trading_day",
            warnings=payload["warnings"],
        )
        return payload

    definitions = store.ensure_indicator_definitions() or [
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
    indicator_history = store.fetch_indicator_history(lookback_days=90)
    theme_history = store.fetch_theme_history(lookback_days=120)

    warnings: list[str] = []
    if not is_trading_day:
        warnings.append(
            f"Reference date {reference_date.isoformat()} is not a trading day. "
            f"Using latest trading day {as_of.isoformat()}."
        )

    source_statuses: dict[str, Any] = {}
    raw_counts: dict[str, int] = {
        "raw_market_snapshot_count": 0,
        "raw_limit_up_pool_count": 0,
        "raw_concept_board_count": 0,
        "raw_stock_kline_count": 0,
    }

    market_snapshot, market_fetched = _fetch_source_with_reuse(
        name="market_snapshot",
        fetcher=engine.provider.fetch_market_snapshot,
        read_existing=lambda: store.fetch_raw_market_snapshot(as_of),
        source_statuses=source_statuses,
        warnings=warnings,
    )
    if market_fetched:
        raw_counts["raw_market_snapshot_count"] = store.upsert_raw_market_snapshot(
            as_of, market_snapshot
        )
    raw_market_snapshot = store.fetch_raw_market_snapshot(as_of)

    limit_up_pool, limit_up_fetched = _fetch_source_with_reuse(
        name="limit_up_pool",
        fetcher=lambda: engine.provider.fetch_limit_up_pool(as_of),
        read_existing=lambda: store.fetch_raw_limit_up_pool(as_of),
        source_statuses=source_statuses,
        warnings=warnings,
    )
    if limit_up_fetched:
        raw_counts["raw_limit_up_pool_count"] = store.upsert_raw_limit_up_pool(
            as_of, limit_up_pool
        )
    raw_limit_up_pool = store.fetch_raw_limit_up_pool(as_of)

    concept_boards, concept_fetched = _fetch_source_with_reuse(
        name="concept_boards",
        fetcher=engine.provider.fetch_concept_board_snapshot,
        read_existing=lambda: store.fetch_raw_concept_boards(as_of),
        source_statuses=source_statuses,
        warnings=warnings,
    )
    if concept_fetched:
        raw_counts["raw_concept_board_count"] = store.upsert_raw_concept_boards(
            as_of, concept_boards
        )
    raw_concept_boards = store.fetch_raw_concept_boards(as_of)

    existing_serving = store.has_serving_snapshot(as_of)
    critical_missing = raw_market_snapshot.empty or raw_concept_boards.empty
    if critical_missing and existing_serving:
        warnings.append(
            "Critical raw sources are incomplete. Existing serving snapshot was preserved."
        )
        payload = {
            "status": "preserved_existing_snapshot",
            "as_of": as_of.isoformat(),
            "indicator_count": 0,
            "theme_count": 0,
            "stock_kline_count": 0,
            "persisted": False,
            "warnings": warnings,
            **raw_counts,
        }
        store.record_fetch_run(
            trigger=trigger,
            reference_date=reference_date,
            target_date=as_of,
            status=payload["status"],
            source_statuses=source_statuses,
            warnings=warnings,
            counts=raw_counts,
        )
        return payload
    if critical_missing and not existing_serving:
        store.record_fetch_run(
            trigger=trigger,
            reference_date=reference_date,
            target_date=as_of,
            status="failed",
            skipped_reason="critical_raw_missing",
            source_statuses=source_statuses,
            warnings=warnings,
            counts=raw_counts,
        )
        raise RuntimeError(
            "Critical raw sources are unavailable and there is no existing serving snapshot to preserve."
        )

    tracking_config = TrackingConfig(
        top_turnover_count=settings.tracking_top_turnover_count,
        limit_up_pool_count=settings.tracking_limit_up_pool_count,
        include_symbols=settings.tracking_symbols,
    )
    theme_definition = next(
        (item for item in definitions if item.enabled and item.key == "active_themes"),
        None,
    )
    pre_context = IndicatorContext(
        as_of=as_of,
        market_snapshot=raw_market_snapshot,
        limit_up_pool=raw_limit_up_pool,
        concept_boards=raw_concept_boards,
        historical_indicator_values=indicator_history,
        historical_theme_volume=theme_history,
    )
    active_themes = engine.active_theme_universe.select(
        pre_context, theme_definition.config if theme_definition else {}
    )
    tracked_symbols = engine.tracked_equities_universe.select(
        IndicatorContext(
            as_of=as_of,
            market_snapshot=raw_market_snapshot,
            limit_up_pool=raw_limit_up_pool,
            concept_boards=raw_concept_boards,
            historical_indicator_values=indicator_history,
            historical_theme_volume=theme_history,
            active_themes=active_themes,
        ),
        tracking_config,
    )

    raw_stock_kline_rows = engine.collect_stock_kline_rows(as_of, tracked_symbols)
    raw_counts["raw_stock_kline_count"] = store.upsert_raw_stock_kline_rows(
        raw_stock_kline_rows
    )
    raw_stock_kline = store.fetch_raw_stock_kline(as_of, tracked_symbols)
    preloaded_stock_kline_rows = [
        {
            "ts": row["ts"],
            "symbol": row["symbol"],
            "name": row.get("name"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "turnover": row.get("turnover"),
            "amplitude": row.get("amplitude"),
            "pct_change": row.get("pct_change"),
            "metadata": row.get("metadata") or {},
        }
        for _, row in raw_stock_kline.iterrows()
    ]

    result = engine.run_with_frames(
        definitions=definitions,
        as_of=as_of,
        market_snapshot=raw_market_snapshot,
        limit_up_pool=raw_limit_up_pool,
        concept_boards=raw_concept_boards,
        historical_indicator_values=indicator_history,
        historical_theme_volume=theme_history,
        tracking_config=tracking_config,
        preloaded_stock_kline_rows=preloaded_stock_kline_rows,
    )

    indicator_rows = [
        {
            "key": item.key,
            "title": item.name,
            "type": item.indicator_type,
            "value_numeric": item.value_numeric,
            "value_text": item.value_text,
            "delta": item.delta,
            "unit": item.unit,
            "raw_data": item.raw_data,
        }
        for item in result.indicators
    ]
    store.upsert_indicator_results(as_of, indicator_rows)
    store.upsert_theme_rows(result.theme_rows)
    store.upsert_stock_kline_rows(preloaded_stock_kline_rows)

    status = "success_with_warnings" if warnings else "success"
    serving_counts = {
        "indicator_count": len(indicator_rows),
        "theme_count": len(result.theme_rows),
        "stock_kline_count": len(preloaded_stock_kline_rows),
    }
    payload = {
        "status": status,
        "as_of": as_of.isoformat(),
        **serving_counts,
        "persisted": True,
        "warnings": warnings,
        **raw_counts,
    }
    store.record_fetch_run(
        trigger=trigger,
        reference_date=reference_date,
        target_date=as_of,
        status=status,
        source_statuses=source_statuses,
        warnings=warnings,
        counts={**raw_counts, **serving_counts},
    )
    return payload


def _fetch_source_with_reuse(
    *,
    name: str,
    fetcher: SourceFetcher,
    read_existing: RawReader,
    source_statuses: dict[str, Any],
    warnings: list[str],
) -> tuple[pd.DataFrame, bool]:
    errors: list[str] = []
    for attempt, delay in enumerate(_FETCH_RETRY_DELAYS, start=1):
        try:
            df = fetcher()
            source_statuses[name] = {
                "status": "fetched",
                "attempts": attempt,
                "row_count": int(len(df.index)),
            }
            return df, True
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc}")
            if attempt < len(_FETCH_RETRY_DELAYS):
                sleep(delay)

    existing = read_existing()
    if not existing.empty:
        warnings.append(
            f"{name} fetch failed after retries; reused stored raw data for the same trading day."
        )
        source_statuses[name] = {
            "status": "reused_existing_raw",
            "attempts": len(_FETCH_RETRY_DELAYS),
            "row_count": int(len(existing.index)),
            "errors": errors,
        }
        return existing, False

    warnings.append(
        f"{name} fetch failed after retries and no stored raw data was available."
    )
    source_statuses[name] = {
        "status": "failed_no_raw",
        "attempts": len(_FETCH_RETRY_DELAYS),
        "row_count": 0,
        "errors": errors,
    }
    return existing, False
