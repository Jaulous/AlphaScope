from __future__ import annotations

import sys
import unittest
from datetime import date
from types import ModuleType, SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd

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

    def lt(self, key, value):
        self._rows = [row for row in self._rows if row.get(key) < value]
        return self

    def eq(self, key, value):
        self._rows = [row for row in self._rows if row.get(key) == value]
        return self

    def in_(self, key, values):
        allowed = set(values)
        self._rows = [row for row in self._rows if row.get(key) in allowed]
        return self

    def order(self, key, desc=False):
        self._rows = sorted(
            self._rows,
            key=lambda row: row.get(key) or "",
            reverse=desc,
        )
        return self

    def limit(self, count):
        self._rows = self._rows[:count]
        return self

    def execute(self):
        return FakeResponse(self._rows)


class FakeClient:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return FakeQuery(self._tables.get(name, []))


class FakeWriteResponse:
    def __init__(self, data=None):
        self.data = data or []


class FakeWriteQuery:
    def __init__(self, table_name: str, sink: dict[str, list[dict]]):
        self._table_name = table_name
        self._sink = sink

    def upsert(self, payload, on_conflict=None):
        self._sink.setdefault(self._table_name, []).append(
            {"payload": payload, "on_conflict": on_conflict}
        )
        return self

    def insert(self, payload):
        self._sink.setdefault(self._table_name, []).append(
            {"payload": payload, "on_conflict": None}
        )
        return self

    def execute(self):
        return FakeWriteResponse()


class FakeWriteClient:
    def __init__(self):
        self.sink: dict[str, list[dict]] = {}

    def table(self, name):
        return FakeWriteQuery(name, self.sink)


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

    def test_upsert_raw_equity_daily_quotes_marks_limit_flags(self) -> None:
        store = SupabaseStore.__new__(SupabaseStore)
        store.client = FakeWriteClient()

        market_snapshot = pd.DataFrame(
            [
                {
                    "symbol": "000001",
                    "name": "Ping An",
                    "last_price": 11.0,
                    "pct_change": 10.02,
                    "change_amount": 1.0,
                    "volume": 1000.0,
                    "turnover": 12000.0,
                    "amplitude": 6.0,
                    "turnover_rate": 5.5,
                    "pe_dynamic": 9.2,
                },
                {
                    "symbol": "600001",
                    "name": "Test Down",
                    "last_price": 7.5,
                    "pct_change": -9.95,
                    "change_amount": -0.8,
                    "volume": 800.0,
                    "turnover": 9000.0,
                    "amplitude": 4.5,
                    "turnover_rate": 3.2,
                    "pe_dynamic": 12.0,
                },
            ]
        )
        limit_up_pool = pd.DataFrame([{"symbol": "000001"}])

        row_count = store.upsert_raw_equity_daily_quotes(
            date(2026, 4, 3),
            market_snapshot,
            limit_up_pool=limit_up_pool,
        )

        self.assertEqual(row_count, 2)
        writes = store.client.sink["raw_equity_daily_quotes"][0]
        payload = writes["payload"]
        self.assertEqual(writes["on_conflict"], "trade_date,symbol")
        self.assertEqual(payload[0]["exchange"], "SZSE")
        self.assertTrue(payload[0]["is_limit_up"])
        self.assertFalse(payload[0]["is_limit_down"])
        self.assertEqual(payload[1]["exchange"], "SSE")
        self.assertTrue(payload[1]["is_limit_down"])
        self.assertFalse(payload[1]["is_limit_up"])

    def test_upsert_raw_equity_daily_limit_events_writes_up_and_down_rows(self) -> None:
        store = SupabaseStore.__new__(SupabaseStore)
        store.client = FakeWriteClient()

        limit_up_pool = pd.DataFrame(
            [
                {
                    "symbol": "000001",
                    "name": "Ping An",
                    "board_count": 2,
                    "seal_funds": 8800000.0,
                    "turnover_rate": 5.2,
                    "first_limit_time": "093100",
                    "last_limit_time": "145600",
                }
            ]
        )
        market_snapshot = pd.DataFrame(
            [
                {"symbol": "600001", "name": "Down Test", "pct_change": -10.01, "turnover_rate": 2.8},
                {"symbol": "000001", "name": "Ping An", "pct_change": 10.01, "turnover_rate": 5.2},
            ]
        )

        row_count = store.upsert_raw_equity_daily_limit_events(
            date(2026, 4, 3),
            limit_up_pool=limit_up_pool,
            market_snapshot=market_snapshot,
        )

        self.assertEqual(row_count, 2)
        writes = store.client.sink["raw_equity_daily_limit_events"][0]
        payload = sorted(
            writes["payload"], key=lambda item: (item["event_side"], item["symbol"])
        )
        self.assertEqual(writes["on_conflict"], "trade_date,symbol,event_side")
        self.assertEqual(payload[0]["event_side"], "down")
        self.assertEqual(payload[0]["limit_type"], "threshold_proxy")
        self.assertEqual(payload[1]["event_side"], "up")
        self.assertEqual(payload[1]["board_count"], 2)


if __name__ == "__main__":
    unittest.main()
