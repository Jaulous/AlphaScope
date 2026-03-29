from __future__ import annotations

from datetime import date, datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from quant_core.ingestion import AkShareProvider

from limitboard_server.config import settings
from limitboard_server.db.supabase_store import SupabaseStore
from limitboard_server.tasks.fetch_data import run_daily_fetch

_DAILY_FETCH_HOUR = 16
_DAILY_FETCH_MINUTES = (0, 15, 30)


class FetchScheduler:
    def __init__(self) -> None:
        self.timezone = pytz.timezone(settings.scheduler_timezone)
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        self.last_success_date: str | None = None

    def _run_guarded(self) -> None:
        if not settings.supabase_enabled:
            return
        today = datetime.now(self.timezone).date().isoformat()
        if self.last_success_date == today:
            return
        result = run_daily_fetch(trigger="scheduler")
        if result.get("status") in {"success", "success_with_warnings"}:
            self.last_success_date = today

    def catch_up_missing_trading_days(
        self, now: datetime | None = None
    ) -> list[dict[str, object]]:
        if not settings.supabase_enabled:
            return []

        current_time = now or datetime.now(self.timezone)
        provider = AkShareProvider(timezone=settings.scheduler_timezone)
        expected_through = self._latest_expected_market_date(
            provider, current_time=current_time
        )
        store = SupabaseStore(
            supabase_url=settings.supabase_url,
            secret_key=settings.supabase_server_key,
        )
        latest_snapshot_raw = store.latest_snapshot_date()
        if not latest_snapshot_raw:
            result = run_daily_fetch(
                trigger="startup_backfill",
                reference_date_override=expected_through,
            )
            self._record_startup_success(
                current_time=current_time,
                as_of=expected_through,
                status=str(result.get("status", "")),
            )
            return [result]

        latest_snapshot = date.fromisoformat(latest_snapshot_raw)
        if latest_snapshot >= expected_through:
            return []

        existing_dates = store.fetch_snapshot_dates(
            start_date=latest_snapshot,
            end_date=expected_through,
        )
        missing_dates = [
            trading_date
            for trading_date in sorted(provider.trade_dates())
            if latest_snapshot < trading_date <= expected_through
            and trading_date not in existing_dates
        ]

        results: list[dict[str, object]] = []
        for missing_date in missing_dates:
            result = run_daily_fetch(
                trigger="startup_backfill",
                reference_date_override=missing_date,
            )
            results.append(result)
            self._record_startup_success(
                current_time=current_time,
                as_of=missing_date,
                status=str(result.get("status", "")),
            )
        return results

    def _latest_expected_market_date(
        self, provider: AkShareProvider, *, current_time: datetime
    ) -> date:
        cutoff_date = current_time.date()
        if (current_time.hour, current_time.minute) < (
            _DAILY_FETCH_HOUR,
            max(_DAILY_FETCH_MINUTES),
        ):
            cutoff_date -= timedelta(days=1)
        return provider.latest_market_date(cutoff_date)

    def _record_startup_success(
        self, *, current_time: datetime, as_of: date, status: str
    ) -> None:
        if status not in {"success", "success_with_warnings"}:
            return
        if as_of.isoformat() == current_time.date().isoformat() and (
            current_time.hour,
            current_time.minute,
        ) >= (_DAILY_FETCH_HOUR, max(_DAILY_FETCH_MINUTES)):
            self.last_success_date = current_time.date().isoformat()

    def start(self) -> None:
        if not settings.supabase_enabled:
            return
        for minute in _DAILY_FETCH_MINUTES:
            self.scheduler.add_job(
                self._run_guarded,
                CronTrigger(
                    hour=_DAILY_FETCH_HOUR, minute=minute, timezone=self.timezone
                ),
                id=f"daily-fetch-{minute}",
                replace_existing=True,
            )
        self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
