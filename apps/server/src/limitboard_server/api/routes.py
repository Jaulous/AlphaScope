from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytz
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from quant_core.ingestion import AkShareProvider

from limitboard_server.config import settings
from limitboard_server.db.supabase_store import SupabaseStore
from limitboard_server.defaults import DEFAULT_INDICATOR_DEFINITIONS
from limitboard_server.tasks.fetch_data import run_daily_fetch

router = APIRouter()


class BoardPayload(BaseModel):
    snapshot: dict


def get_store() -> SupabaseStore | None:
    if not settings.supabase_enabled:
        return None
    return SupabaseStore(
        supabase_url=settings.supabase_url,
        secret_key=settings.supabase_server_key,
        board_slug=settings.supabase_board_slug,
    )


def require_store() -> SupabaseStore:
    store = get_store()
    if not store:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase persistence is required. Configure SUPABASE_URL and "
                "SUPABASE_SECRET_KEY before using the dashboard."
            ),
        )
    return store


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "supabase_enabled": settings.supabase_enabled,
        "storage_mode": "supabase",
        "scheduler_timezone": settings.scheduler_timezone,
    }


@router.get("/dashboard/latest")
def dashboard_latest(lookback_days: int = 60) -> dict:
    store = require_store()
    snapshot: dict | None = None
    warnings: list[str] = []
    provider = AkShareProvider(timezone=settings.scheduler_timezone)
    latest_market_date = provider.latest_market_date().isoformat()

    try:
        snapshot = store.fetch_dashboard_snapshot(lookback_days=lookback_days)
    except Exception:
        snapshot = None

    needs_refresh = (
        snapshot is None
        or snapshot.get("as_of") != latest_market_date
        or (
            not snapshot.get("indicators")
            and not snapshot.get("active_themes")
            and not snapshot.get("tracked_stocks")
        )
    )
    if needs_refresh:
        try:
            fetch_result = run_daily_fetch(trigger="on_demand")
            warnings.extend(fetch_result.get("warnings", []))
            snapshot = store.fetch_dashboard_snapshot(lookback_days=lookback_days)
        except Exception as exc:
            if snapshot and snapshot.get("as_of"):
                warnings.append(
                    f"Latest fetch failed, showing stored snapshot from {snapshot['as_of']}: {exc}"
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to produce a persisted dashboard snapshot: {exc}",
                ) from exc

    if not snapshot:
        raise HTTPException(
            status_code=404, detail="No persisted dashboard snapshot available"
        )

    snapshot["source"] = "stored"
    snapshot["storage_mode"] = "supabase"
    snapshot["generated_at"] = datetime.now(
        pytz.timezone(settings.scheduler_timezone)
    ).isoformat()
    snapshot["warnings"] = warnings
    snapshot["latest_run"] = store.fetch_latest_fetch_run()
    if "market_breadth" not in snapshot:
        snapshot["market_breadth"] = None
    return snapshot


@router.get("/definitions")
def indicator_definitions() -> list[dict]:
    store = require_store()
    return store.fetch_indicator_definitions() or DEFAULT_INDICATOR_DEFINITIONS


@router.get("/stocks/{symbol}/kline")
def stock_kline(symbol: str, lookback_days: int = 30) -> list[dict]:
    store = require_store()
    return store.fetch_stock_kline_history(symbol=symbol, lookback_days=lookback_days)


@router.post("/fetch/run")
def trigger_fetch(x_admin_key: str | None = Header(default=None)) -> dict:
    if settings.admin_api_key and x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="invalid admin key")
    try:
        return run_daily_fetch(trigger="manual")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/board/default")
def get_board() -> dict:
    return require_store().get_board_document()


@router.put("/board/default")
def put_board(payload: BoardPayload) -> dict:
    if payload.snapshot is None:
        raise HTTPException(status_code=400, detail="snapshot is required")
    return require_store().save_board_document(payload.snapshot)
