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
if "pytz" not in sys.modules:
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
if "fastapi" not in sys.modules:
    fastapi_module = ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class APIRouter:
        def get(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def post(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

    fastapi_module.APIRouter = APIRouter
    fastapi_module.Header = lambda default=None: default
    fastapi_module.HTTPException = HTTPException
    sys.modules["fastapi"] = fastapi_module
if "limitboard_server.config" not in sys.modules:
    config_module = ModuleType("limitboard_server.config")
    config_module.settings = SimpleNamespace(
        supabase_enabled=True,
        supabase_url="https://example.supabase.co",
        supabase_server_key="service-key",
        scheduler_timezone="Asia/Shanghai",
        cron_secret="test-secret",
        admin_api_key="",
        scheduler_enabled=False,
        is_vercel=True,
    )
    sys.modules["limitboard_server.config"] = config_module
sys.modules.setdefault("requests", SimpleNamespace())

from limitboard_server.api import routes


class VercelCronBehaviorTests(unittest.TestCase):
    def test_cron_fetch_requires_secret(self) -> None:
        fake_settings = SimpleNamespace(
            supabase_enabled=True,
            supabase_url="https://example.supabase.co",
            supabase_server_key="service-key",
            scheduler_timezone="Asia/Shanghai",
            cron_secret="expected-secret",
            admin_api_key="",
            scheduler_enabled=False,
            is_vercel=True,
        )

        with patch("limitboard_server.api.routes.settings", fake_settings):
            with self.assertRaises(routes.HTTPException) as context:
                routes.cron_fetch(authorization="Bearer wrong-secret")

        self.assertEqual(context.exception.status_code, 401)

    def test_cron_fetch_runs_startup_backfill_path(self) -> None:
        fake_settings = SimpleNamespace(
            supabase_enabled=True,
            supabase_url="https://example.supabase.co",
            supabase_server_key="service-key",
            scheduler_timezone="Asia/Shanghai",
            cron_secret="expected-secret",
            admin_api_key="",
            scheduler_enabled=False,
            is_vercel=True,
        )
        fake_provider = SimpleNamespace(
            latest_market_date=lambda reference_date=None: date(2026, 3, 27)
        )
        fake_scheduler = SimpleNamespace(
            catch_up_missing_trading_days=lambda now=None: [
                {"status": "success", "as_of": "2026-03-27"}
            ]
        )

        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                current = cls(2026, 3, 29, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
                return current if tz is None else current.astimezone(tz)

        with (
            patch("limitboard_server.api.routes.settings", fake_settings),
            patch("limitboard_server.api.routes.cron_scheduler", fake_scheduler),
            patch(
                "limitboard_server.api.routes.AkShareProvider",
                return_value=fake_provider,
            ),
            patch("limitboard_server.api.routes.datetime", FrozenDateTime),
        ):
            payload = routes.cron_fetch(authorization="Bearer expected-secret")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["expected_through"], "2026-03-27")
        self.assertEqual(payload["latest_backfilled_as_of"], "2026-03-27")


if __name__ == "__main__":
    unittest.main()
