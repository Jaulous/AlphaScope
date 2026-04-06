from __future__ import annotations

import sys
import unittest
from datetime import date, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.modules.setdefault(
    "supabase",
    SimpleNamespace(Client=object, create_client=lambda *_args, **_kwargs: None),
)
sys.modules.setdefault("akshare", SimpleNamespace())
try:
    import pytz  # noqa: F401
except ModuleNotFoundError:
    pytz_stub = ModuleType("pytz")
    pytz_stub.__version__ = "2024.2"
    pytz_stub.timezone = lambda name: ZoneInfo(name)
    pytz_stub.UTC = ZoneInfo("UTC")
    sys.modules["pytz"] = pytz_stub
if "apscheduler.schedulers.asyncio" not in sys.modules:
    apscheduler_module = ModuleType("apscheduler")
    schedulers_module = ModuleType("apscheduler.schedulers")
    asyncio_module = ModuleType("apscheduler.schedulers.asyncio")
    triggers_module = ModuleType("apscheduler.triggers")
    cron_module = ModuleType("apscheduler.triggers.cron")

    class AsyncIOScheduler:
        def __init__(self, *args, **kwargs):
            self.running = False

        def add_job(self, *args, **kwargs):
            return None

        def start(self):
            self.running = True

        def shutdown(self, wait=False):
            self.running = False

    class CronTrigger:
        def __init__(self, *args, **kwargs):
            return None

    asyncio_module.AsyncIOScheduler = AsyncIOScheduler
    cron_module.CronTrigger = CronTrigger
    sys.modules["apscheduler"] = apscheduler_module
    sys.modules["apscheduler.schedulers"] = schedulers_module
    sys.modules["apscheduler.schedulers.asyncio"] = asyncio_module
    sys.modules["apscheduler.triggers"] = triggers_module
    sys.modules["apscheduler.triggers.cron"] = cron_module
if "limitboard_server.config" not in sys.modules:
    config_module = ModuleType("limitboard_server.config")
    config_module.settings = SimpleNamespace(
        supabase_enabled=False,
        supabase_url=None,
        supabase_server_key=None,
        scheduler_timezone="Asia/Shanghai",
    )
    sys.modules["limitboard_server.config"] = config_module
sys.modules.setdefault("requests", SimpleNamespace())

from limitboard_server.scheduler import FetchScheduler


class FetchSchedulerBackfillTests(unittest.TestCase):
    def test_catch_up_missing_trading_days_backfills_gap_after_latest_snapshot(
        self,
    ) -> None:
        now = datetime(2026, 3, 18, 18, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        fake_settings = SimpleNamespace(
            supabase_enabled=True,
            supabase_url="https://example.supabase.co",
            supabase_server_key="service-key",
            scheduler_timezone="Asia/Shanghai",
        )
        fake_provider = SimpleNamespace(
            latest_market_date=lambda reference_date=None: reference_date,
            trade_dates=lambda: {
                date(2026, 3, 16),
                date(2026, 3, 17),
                date(2026, 3, 18),
            },
        )
        fake_store = SimpleNamespace(
            latest_snapshot_date=lambda: "2026-03-16",
            fetch_snapshot_dates=lambda start_date, end_date: {
                date(2026, 3, 16),
                date(2026, 3, 18),
            },
        )

        with (
            patch("limitboard_server.scheduler.settings", fake_settings),
            patch(
                "limitboard_server.scheduler.AkShareProvider",
                return_value=fake_provider,
            ),
            patch("limitboard_server.scheduler.SupabaseStore", return_value=fake_store),
            patch(
                "limitboard_server.scheduler.run_daily_fetch",
                side_effect=lambda **kwargs: {
                    "status": "success",
                    "as_of": kwargs["reference_date_override"].isoformat(),
                },
            ) as run_fetch,
        ):
            scheduler = FetchScheduler()
            results = scheduler.catch_up_missing_trading_days(now=now)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["as_of"], "2026-03-17")
        run_fetch.assert_called_once_with(
            trigger="startup_backfill",
            reference_date_override=date(2026, 3, 17),
        )

    def test_catch_up_before_close_only_requires_previous_trading_day(self) -> None:
        now = datetime(2026, 3, 18, 15, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        fake_settings = SimpleNamespace(
            supabase_enabled=True,
            supabase_url="https://example.supabase.co",
            supabase_server_key="service-key",
            scheduler_timezone="Asia/Shanghai",
        )
        fake_provider = SimpleNamespace(
            latest_market_date=lambda reference_date=None: (
                date(2026, 3, 17)
                if reference_date == date(2026, 3, 17)
                else reference_date
            ),
            trade_dates=lambda: {
                date(2026, 3, 17),
                date(2026, 3, 18),
            },
        )
        fake_store = SimpleNamespace(
            latest_snapshot_date=lambda: "2026-03-17",
            fetch_snapshot_dates=lambda start_date, end_date: {date(2026, 3, 17)},
        )

        with (
            patch("limitboard_server.scheduler.settings", fake_settings),
            patch(
                "limitboard_server.scheduler.AkShareProvider",
                return_value=fake_provider,
            ),
            patch("limitboard_server.scheduler.SupabaseStore", return_value=fake_store),
            patch("limitboard_server.scheduler.run_daily_fetch") as run_fetch,
        ):
            scheduler = FetchScheduler()
            results = scheduler.catch_up_missing_trading_days(now=now)

        self.assertEqual(results, [])
        run_fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
