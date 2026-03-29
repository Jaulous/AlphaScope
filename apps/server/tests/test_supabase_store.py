from __future__ import annotations

import sys
import unittest
from types import ModuleType, SimpleNamespace
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
sys.modules.setdefault("requests", SimpleNamespace())

from limitboard_server.db.supabase_store import SupabaseStore


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self._rows = list(rows)

    def select(self, *_args, **_kwargs):
        return self

    def gte(self, key, value):
        self._rows = [row for row in self._rows if row.get(key) >= value]
        return self

    def eq(self, key, value):
        self._rows = [row for row in self._rows if row.get(key) == value]
        return self

    def order(self, key, desc=False):
        self._rows = sorted(
            self._rows,
            key=lambda row: row.get(key) or "",
            reverse=desc,
        )
        return self

    def execute(self):
        return FakeResponse(self._rows)


class FakeClient:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return FakeQuery(self._tables.get(name, []))


class SupabaseStoreSnapshotTests(unittest.TestCase):
    def test_fetch_dashboard_snapshot_includes_history_series(self) -> None:
        store = SupabaseStore.__new__(SupabaseStore)
        store.client = FakeClient(
            {
                "daily_indicators": [
                    {
                        "key": "up_limit_count",
                        "indicator_date": "2026-03-05",
                        "title": "Up Limit Count",
                        "type": "up_limit_count",
                        "value_numeric": 91.0,
                        "value_text": "91",
                        "delta": None,
                        "unit": "stocks",
                        "raw_data": {},
                    },
                    {
                        "key": "up_limit_count",
                        "indicator_date": "2026-03-06",
                        "title": "Up Limit Count",
                        "type": "up_limit_count",
                        "value_numeric": 103.0,
                        "value_text": "103",
                        "delta": None,
                        "unit": "stocks",
                        "raw_data": {},
                    },
                ],
                "daily_themes_volume": [
                    {
                        "indicator_date": "2026-03-05",
                        "theme_name": "AI",
                        "turnover": 100000000.0,
                        "rank": 2,
                        "metadata": {"leader": "A"},
                    },
                    {
                        "indicator_date": "2026-03-06",
                        "theme_name": "AI",
                        "turnover": 150000000.0,
                        "rank": 1,
                        "metadata": {"leader": "B"},
                    },
                ],
                "stock_kline_daily": [
                    {
                        "ts": "2026-03-05T00:00:00+08:00",
                        "symbol": "000001",
                        "name": "Ping An",
                        "open": 10.0,
                        "high": 10.8,
                        "low": 9.8,
                        "close": 10.5,
                        "volume": 1000.0,
                        "turnover": 10000.0,
                        "amplitude": 5.0,
                        "pct_change": 2.0,
                    },
                    {
                        "ts": "2026-03-06T00:00:00+08:00",
                        "symbol": "000001",
                        "name": "Ping An",
                        "open": 10.5,
                        "high": 11.2,
                        "low": 10.2,
                        "close": 11.0,
                        "volume": 1200.0,
                        "turnover": 12000.0,
                        "amplitude": 6.0,
                        "pct_change": 4.5,
                    },
                ],
                "raw_market_snapshot_daily": [
                    {"snapshot_date": "2026-03-06", "pct_change": 1.2},
                    {"snapshot_date": "2026-03-06", "pct_change": -0.4},
                    {"snapshot_date": "2026-03-06", "pct_change": 0.0},
                ],
            }
        )
        snapshot = store.fetch_dashboard_snapshot(lookback_days=60)

        self.assertEqual(snapshot["as_of"], "2026-03-06")
        self.assertEqual(len(snapshot["indicators"]), 1)
        self.assertEqual(len(snapshot["indicators"][0]["history"]), 2)
        self.assertEqual(snapshot["active_themes"][0]["rank"], 1)
        self.assertEqual(len(snapshot["active_themes"][0]["history"]), 2)
        self.assertEqual(snapshot["tracked_stocks"][0]["symbol"], "000001")
        self.assertEqual(len(snapshot["tracked_stocks"][0]["history"]), 2)
        self.assertEqual(
            snapshot["market_breadth"],
            {"advancers": 1, "decliners": 1, "unchanged": 1},
        )


if __name__ == "__main__":
    unittest.main()
