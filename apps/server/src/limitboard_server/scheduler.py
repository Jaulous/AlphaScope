from __future__ import annotations

from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from limitboard_server.config import settings
from limitboard_server.tasks.fetch_data import run_daily_fetch


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

    def start(self) -> None:
        if not settings.supabase_enabled:
            return
        for minute in (0, 15, 30):
            self.scheduler.add_job(
                self._run_guarded,
                CronTrigger(hour=16, minute=minute, timezone=self.timezone),
                id=f"daily-fetch-{minute}",
                replace_existing=True,
            )
        self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
