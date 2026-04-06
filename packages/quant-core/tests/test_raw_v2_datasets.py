from __future__ import annotations

import sys
import unittest
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

from quant_core.indicators.active_capital_ratio import ActiveCapitalRatioIndicator
from quant_core.indicators.decliner_count import DeclinerCountIndicator
from quant_core.indicators.down_limit_count import DownLimitCountIndicator
from quant_core.indicators.highest_board import HighestBoardIndicator
from quant_core.indicators.market_turnover import MarketTurnoverIndicator
from quant_core.indicators.n_shape_limit_up_count import NShapeLimitUpCountIndicator
from quant_core.indicators.up_limit_count import UpLimitCountIndicator
from quant_core.types import IndicatorContext, IndicatorDefinition, TrackingConfig
from quant_core.universe.active_themes import ActiveThemesUniverse
from quant_core.universe.tracked_equities import TrackedEquitiesUniverse


class RawV2DatasetPreferenceTests(unittest.TestCase):
    def _context(self, *, datasets: dict[str, pd.DataFrame]) -> IndicatorContext:
        return IndicatorContext(
            as_of=pd.Timestamp("2026-04-03").date(),
            market_snapshot=pd.DataFrame(),
            limit_up_pool=pd.DataFrame(),
            concept_boards=pd.DataFrame(),
            datasets=datasets,
        )

    def test_market_turnover_decliner_and_active_capital_ratio_use_equity_daily_quotes(self) -> None:
        quotes = pd.DataFrame(
            [
                {"symbol": "000001", "turnover": 100.0, "pct_change": 5.0},
                {"symbol": "000002", "turnover": 60.0, "pct_change": -1.2},
                {"symbol": "000003", "turnover": 40.0, "pct_change": -3.4},
            ]
        )
        context = self._context(datasets={"equity_daily_quotes": quotes})

        market_turnover = MarketTurnoverIndicator().compute(
            context,
            IndicatorDefinition(
                key="market_turnover",
                type="market_turnover",
                name="Market Turnover",
                config={"display_unit": "CNY"},
            ),
        )
        decliner_count = DeclinerCountIndicator().compute(
            context,
            IndicatorDefinition(
                key="decliner_count",
                type="decliner_count",
                name="Decliner Count",
            ),
        )
        active_capital_ratio = ActiveCapitalRatioIndicator().compute(
            context,
            IndicatorDefinition(
                key="active_capital_ratio",
                type="active_capital_ratio",
                name="Active Capital Ratio",
                config={"top_percent": 0.34},
            ),
        )

        self.assertEqual(market_turnover.value_numeric, 200.0)
        self.assertEqual(decliner_count.value_numeric, 2.0)
        self.assertAlmostEqual(active_capital_ratio.value_numeric or 0.0, 0.5)

    def test_up_and_down_limit_indicators_use_limit_event_dataset(self) -> None:
        limit_events = pd.DataFrame(
            [
                {"symbol": "000001", "event_side": "up", "name": "Ping An", "board_count": 2},
                {"symbol": "000002", "event_side": "up", "name": "Vanke", "board_count": 1},
                {"symbol": "600001", "event_side": "down", "name": "Down Test"},
            ]
        )
        context = self._context(datasets={"equity_daily_limit_events": limit_events})

        up_limit = UpLimitCountIndicator().compute(
            context,
            IndicatorDefinition(
                key="up_limit_count",
                type="up_limit_count",
                name="Up Limit Count",
            ),
        )
        down_limit = DownLimitCountIndicator().compute(
            context,
            IndicatorDefinition(
                key="down_limit_count",
                type="down_limit_count",
                name="Down Limit Count",
            ),
        )

        self.assertEqual(up_limit.value_numeric, 2.0)
        self.assertEqual(len(up_limit.raw_data["stocks"]), 2)
        self.assertEqual(up_limit.raw_data["stocks"][0]["board_count"], 2)
        self.assertEqual(down_limit.value_numeric, 1.0)

    def test_universe_layers_prefer_raw_v2_datasets(self) -> None:
        context = self._context(
            datasets={
                "equity_daily_quotes": pd.DataFrame(
                    [
                        {"symbol": "000003", "turnover": 300.0},
                        {"symbol": "000001", "turnover": 100.0},
                        {"symbol": "000002", "turnover": 200.0},
                    ]
                ),
                "equity_daily_limit_events": pd.DataFrame(
                    [
                        {"symbol": "000001", "event_side": "up"},
                        {"symbol": "000002", "event_side": "up"},
                    ]
                ),
                "concept_board_daily": pd.DataFrame(
                    [
                        {
                            "trade_date": "2026-04-03",
                            "board_name": "AI",
                            "turnover": 200.0,
                            "pct_change": 3.1,
                            "market_cap": 1000.0,
                            "advancers": 8,
                            "decliners": 2,
                            "leader": "000001",
                            "rank": 1,
                        },
                        {
                            "trade_date": "2026-04-03",
                            "board_name": "Robotics",
                            "turnover": 150.0,
                            "pct_change": 2.0,
                            "market_cap": 900.0,
                            "advancers": 6,
                            "decliners": 4,
                            "leader": "000002",
                            "rank": 2,
                        },
                    ]
                ),
            }
        )

        themes = ActiveThemesUniverse().select(context, {"top_n": 1})
        tracked = TrackedEquitiesUniverse().select(
            context,
            TrackingConfig(top_turnover_count=2, limit_up_pool_count=1),
        )

        self.assertEqual(len(themes), 1)
        self.assertEqual(themes[0].name, "AI")
        self.assertEqual(tracked, ["000003", "000002", "000001"])

    def test_highest_board_uses_current_limit_event_dataset(self) -> None:
        context = self._context(
            datasets={
                "equity_daily_limit_events": pd.DataFrame(
                    [
                        {
                            "symbol": "000001",
                            "event_side": "up",
                            "name": "Ping An",
                            "board_count": 2,
                        },
                        {
                            "symbol": "000002",
                            "event_side": "up",
                            "name": "Vanke",
                            "board_count": 4,
                        },
                        {
                            "symbol": "000003",
                            "event_side": "down",
                            "name": "Down Test",
                        },
                    ]
                )
            }
        )

        result = HighestBoardIndicator().compute(
            context,
            IndicatorDefinition(
                key="highest_board",
                type="highest_board",
                name="Highest Board",
            ),
        )

        self.assertEqual(result.value_numeric, 4.0)
        self.assertEqual(result.raw_data["leaders"], ["Vanke"])

    def test_n_shape_limit_up_count_uses_historical_limit_event_dataset(self) -> None:
        context = IndicatorContext(
            as_of=pd.Timestamp("2026-04-03").date(),
            market_snapshot=pd.DataFrame(),
            limit_up_pool=pd.DataFrame(),
            concept_boards=pd.DataFrame(),
            stock_kline_history=pd.DataFrame(
                [
                    {
                        "ts": "2026-03-24T00:00:00+08:00",
                        "symbol": "000001",
                        "name": "Ping An",
                        "close": 10.0,
                    },
                    {
                        "ts": "2026-03-28T00:00:00+08:00",
                        "symbol": "000001",
                        "name": "Ping An",
                        "close": 9.0,
                    },
                    {
                        "ts": "2026-04-03T00:00:00+08:00",
                        "symbol": "000001",
                        "name": "Ping An",
                        "close": 10.2,
                    },
                ]
            ),
            datasets={
                "equity_daily_limit_events": pd.DataFrame(
                    [
                        {
                            "trade_date": "2026-04-03",
                            "symbol": "000001",
                            "event_side": "up",
                            "name": "Ping An",
                            "board_count": 1,
                        }
                    ]
                ),
                "historical_equity_daily_limit_events": pd.DataFrame(
                    [
                        {
                            "trade_date": "2026-03-24",
                            "symbol": "000001",
                            "event_side": "up",
                            "name": "Ping An",
                            "board_count": 1,
                        }
                    ]
                ),
            },
        )

        result = NShapeLimitUpCountIndicator().compute(
            context,
            IndicatorDefinition(
                key="n_shape_limit_up_count",
                type="n_shape_limit_up_count",
                name="N Shape Limit Up Count",
                config={"lookback_days": 30, "min_pullback_pct": 5.0, "min_gap_days": 2},
            ),
        )

        self.assertEqual(result.value_numeric, 1.0)
        self.assertEqual(result.raw_data["stocks"][0]["symbol"], "000001")


if __name__ == "__main__":
    unittest.main()
