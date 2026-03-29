from __future__ import annotations

import sys
import unittest
from datetime import date
from types import ModuleType, SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd

sys.modules.setdefault("akshare", SimpleNamespace())
if "pytz" not in sys.modules:
    pytz_stub = ModuleType("pytz")
    pytz_stub.__version__ = "2024.2"
    pytz_stub.timezone = lambda name: ZoneInfo(name)
    pytz_stub.UTC = ZoneInfo("UTC")
    sys.modules["pytz"] = pytz_stub
sys.modules.setdefault("requests", SimpleNamespace())

from quant_core import IndicatorDefinition, QuantEngine


class FakeProvider:
    def fetch_stock_kline_daily(
        self, symbol: str, start_date: date, end_date: date | None = None
    ) -> pd.DataFrame:
        if symbol == "BAD":
            raise RuntimeError("fetch failed")
        return pd.DataFrame(
            [
                {
                    "ts": pd.Timestamp("2026-03-06", tz="Asia/Shanghai"),
                    "symbol": symbol,
                    "name": "Demo",
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.5,
                    "close": 10.8,
                    "volume": 1000.0,
                    "turnover": 10000.0,
                    "amplitude": 5.0,
                    "pct_change": 8.0,
                }
            ]
        )


class QuantEngineExecutionPlanTests(unittest.TestCase):
    def test_build_execution_plan_aggregates_indicator_requirements(self) -> None:
        engine = QuantEngine(use_multiprocessing=False)
        definitions = [
            IndicatorDefinition(
                key="active_themes",
                type="active_themes",
                name="Active Themes",
                config={"window_days": 28},
            ),
            IndicatorDefinition(
                key="n_shape_limit_up_count",
                type="n_shape_limit_up_count",
                name="N Shape",
                config={"lookback_days": 45},
            ),
            IndicatorDefinition(
                key="up_limit_count",
                type="up_limit_count",
                name="Up Limit Count",
                enabled=False,
            ),
        ]

        plan = engine.build_execution_plan(definitions)

        self.assertEqual(plan.theme_history_days, 28)
        self.assertEqual(plan.limit_up_pool_history_days, 45)
        self.assertEqual(plan.limit_up_pool_stock_history_days, 45)
        self.assertTrue(plan.limit_up_pool_stock_history_required)
        self.assertEqual(plan.tracked_stock_history_days, 0)

    def test_collect_stock_kline_rows_reports_symbol_errors(self) -> None:
        engine = QuantEngine(provider=FakeProvider(), use_multiprocessing=False)

        rows, errors = engine.collect_stock_kline_rows(
            as_of=date(2026, 3, 6),
            symbols=["000001", "BAD"],
            return_errors=True,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "000001")
        self.assertEqual(len(errors), 1)
        self.assertIn("BAD", errors[0])


if __name__ == "__main__":
    unittest.main()
