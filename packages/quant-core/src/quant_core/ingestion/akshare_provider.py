from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Any

import akshare as ak
import pandas as pd
import pytz
import requests


class AkShareProvider:
    def __init__(self, timezone: str = "Asia/Shanghai") -> None:
        self.timezone = pytz.timezone(timezone)
        self.sina_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": "https://vip.stock.finance.sina.com.cn/mkt/",
        }
        self._trade_dates_cache: set[date] | None = None

    def fetch_market_snapshot(self) -> pd.DataFrame:
        errors: list[str] = []
        try:
            df = self._fetch_market_snapshot_sina_https()
            if not df.empty:
                return self._normalize_market_snapshot(df)
        except Exception as exc:
            errors.append(f"sina_https: {exc}")

        for fetcher in (ak.stock_zh_a_spot_em, ak.stock_zh_a_spot):
            try:
                df = fetcher()
                if not df.empty:
                    return self._normalize_market_snapshot(df)
            except Exception as exc:
                errors.append(f"{fetcher.__name__}: {exc}")
        raise RuntimeError("; ".join(errors) or "failed to fetch market snapshot")

    def fetch_limit_up_pool(self, as_of: date) -> pd.DataFrame:
        try:
            df = ak.stock_zt_pool_em(date=as_of.strftime("%Y%m%d"))
        except Exception:
            return pd.DataFrame()
        return self._normalize_limit_up_pool(df)

    def fetch_concept_board_snapshot(self) -> pd.DataFrame:
        errors: list[str] = []
        try:
            df = ak.stock_board_concept_name_em()
            if not df.empty:
                return self._normalize_concept_boards(df)
        except Exception as exc:
            errors.append(f"stock_board_concept_name_em: {exc}")

        try:
            df = ak.stock_board_change_em()
            if not df.empty:
                return self._normalize_board_changes(df)
        except Exception as exc:
            errors.append(f"stock_board_change_em: {exc}")

        raise RuntimeError("; ".join(errors) or "failed to fetch concept boards")

    def fetch_stock_kline_daily(
        self, symbol: str, start_date: date, end_date: date | None = None
    ) -> pd.DataFrame:
        end = end_date or start_date
        errors: list[str] = []
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if not df.empty:
                rename_map = {
                    "日期": "ts",
                    "股票代码": "symbol",
                    "股票简称": "name",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "振幅": "amplitude",
                    "涨跌幅": "pct_change",
                }
                df = df.rename(columns=rename_map)
                return self._finalize_stock_kline_frame(df, symbol=symbol)
        except Exception as exc:
            errors.append(f"stock_zh_a_hist: {exc}")

        try:
            df = ak.stock_zh_a_hist_tx(
                symbol=self._symbol_with_exchange_prefix(symbol),
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if not df.empty:
                df = df.rename(
                    columns={
                        "date": "ts",
                        "open": "open",
                        "close": "close",
                        "high": "high",
                        "low": "low",
                        "amount": "turnover",
                    }
                )
                df["symbol"] = symbol
                return self._finalize_stock_kline_frame(df, symbol=symbol)
        except Exception as exc:
            errors.append(f"stock_zh_a_hist_tx: {exc}")

        if errors:
            raise RuntimeError("; ".join(errors))
        return pd.DataFrame()

    def _normalize_market_snapshot(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "代码": "symbol",
            "symbol": "symbol",
            "名称": "name",
            "name": "name",
            "最新价": "last_price",
            "trade": "last_price",
            "涨跌幅": "pct_change",
            "changepercent": "pct_change",
            "涨跌额": "change_amount",
            "pricechange": "change_amount",
            "成交量": "volume",
            "volume": "volume",
            "成交额": "turnover",
            "amount": "turnover",
            "振幅": "amplitude",
            "换手率": "turnover_rate",
            "turnoverratio": "turnover_rate",
            "市盈率-动态": "pe_dynamic",
            "per": "pe_dynamic",
        }
        normalized = df.rename(columns=rename_map)
        expected = [
            "symbol",
            "name",
            "last_price",
            "pct_change",
            "change_amount",
            "volume",
            "turnover",
            "amplitude",
            "turnover_rate",
            "pe_dynamic",
        ]
        for column in expected:
            if column not in normalized.columns:
                normalized[column] = None
        return normalized[expected].copy()

    def _normalize_limit_up_pool(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "代码": "symbol",
            "名称": "name",
            "连板数": "board_count",
            "封单资金": "seal_funds",
            "换手率": "turnover_rate",
            "首次封板时间": "first_limit_time",
            "最后封板时间": "last_limit_time",
        }
        normalized = df.rename(columns=rename_map)
        if "board_count" not in normalized.columns:
            normalized["board_count"] = 1
        return normalized

    def _normalize_concept_boards(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "板块名称": "theme_name",
            "名称": "theme_name",
            "成交额": "turnover",
            "涨跌幅": "pct_change",
            "总市值": "market_cap",
            "上涨家数": "advancers",
            "下跌家数": "decliners",
            "领涨股票": "leader",
        }
        normalized = df.rename(columns=rename_map)
        for column in [
            "theme_name",
            "turnover",
            "pct_change",
            "market_cap",
            "advancers",
            "decliners",
            "leader",
        ]:
            if column not in normalized.columns:
                normalized[column] = None
        normalized = normalized.dropna(subset=["theme_name"]).copy()
        normalized["turnover"] = pd.to_numeric(
            normalized["turnover"], errors="coerce"
        ).fillna(0.0)
        normalized = normalized.sort_values("turnover", ascending=False).reset_index(
            drop=True
        )
        normalized["rank"] = normalized.index + 1
        return normalized

    def _normalize_board_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "板块名称": "theme_name",
            "涨跌幅": "pct_change",
            "主力净流入": "turnover",
            "板块异动最频繁个股及所属类型-股票名称": "leader",
        }
        normalized = df.rename(columns=rename_map).copy()
        normalized["theme_name"] = normalized.get("theme_name")
        normalized["turnover"] = pd.to_numeric(
            normalized.get("turnover"), errors="coerce"
        ).fillna(0.0)
        normalized["pct_change"] = pd.to_numeric(
            normalized.get("pct_change"), errors="coerce"
        )
        normalized["leader"] = normalized.get("leader")
        normalized["advancers"] = None
        normalized["decliners"] = None
        normalized = normalized.dropna(subset=["theme_name"]).copy()
        normalized = normalized.sort_values("turnover", ascending=False).reset_index(
            drop=True
        )
        normalized["rank"] = normalized.index + 1
        return normalized[
            [
                "theme_name",
                "turnover",
                "pct_change",
                "leader",
                "advancers",
                "decliners",
                "rank",
            ]
        ]

    def recent_market_days(self, lookback_days: int = 30) -> tuple[date, date]:
        end = self.latest_market_date()
        return end - timedelta(days=lookback_days), end

    def latest_market_date(self, reference_date: date | None = None) -> date:
        current = reference_date or datetime.now(self.timezone).date()
        trade_dates = self.trade_dates()
        while current not in trade_dates:
            current -= timedelta(days=1)
        return current

    def is_trading_day(self, target_date: date | None = None) -> bool:
        current = target_date or datetime.now(self.timezone).date()
        return current in self.trade_dates()

    def trade_dates(self) -> set[date]:
        if self._trade_dates_cache is None:
            df = ak.tool_trade_date_hist_sina()
            self._trade_dates_cache = {
                item if isinstance(item, date) else pd.Timestamp(item).date()
                for item in df["trade_date"].tolist()
            }
        return self._trade_dates_cache

    def _finalize_stock_kline_frame(
        self, df: pd.DataFrame, symbol: str
    ) -> pd.DataFrame:
        normalized = df.copy()
        if "symbol" not in normalized.columns:
            normalized["symbol"] = symbol
        if "name" not in normalized.columns:
            normalized["name"] = None
        if "volume" not in normalized.columns:
            normalized["volume"] = None
        if "turnover" not in normalized.columns:
            normalized["turnover"] = None
        normalized["ts"] = pd.to_datetime(
            normalized["ts"], errors="coerce"
        ).dt.tz_localize(self.timezone, nonexistent="shift_forward", ambiguous="NaT")
        close_series = pd.to_numeric(normalized.get("close"), errors="coerce")
        if "pct_change" not in normalized.columns:
            normalized["pct_change"] = close_series.pct_change() * 100
        if "amplitude" not in normalized.columns:
            high_series = pd.to_numeric(normalized.get("high"), errors="coerce")
            low_series = pd.to_numeric(normalized.get("low"), errors="coerce")
            base_series = close_series.shift(1).where(close_series.shift(1) != 0)
            normalized["amplitude"] = ((high_series - low_series) / base_series) * 100
        return normalized[
            [
                c
                for c in [
                    "ts",
                    "symbol",
                    "name",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "turnover",
                    "amplitude",
                    "pct_change",
                ]
                if c in normalized.columns
            ]
        ].copy()

    def _symbol_with_exchange_prefix(self, symbol: str) -> str:
        raw = str(symbol).strip()
        if raw.startswith(("sh", "sz", "bj")):
            return raw
        if raw.startswith(("600", "601", "603", "605", "688", "689")):
            return f"sh{raw}"
        if raw.startswith(
            (
                "430",
                "800",
                "830",
                "831",
                "832",
                "833",
                "835",
                "836",
                "837",
                "838",
                "839",
            )
        ):
            return f"bj{raw}"
        return f"sz{raw}"

    def _fetch_market_snapshot_sina_https(self) -> pd.DataFrame:
        count_url = (
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "Market_Center.getHQNodeStockCount?node=hs_a"
        )
        data_url = (
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "Market_Center.getHQNodeData"
        )
        count_response = requests.get(count_url, headers=self.sina_headers, timeout=20)
        count_response.raise_for_status()
        total_count = int((count_response.text or "0").strip().strip('"'))
        if total_count <= 0:
            return pd.DataFrame()

        page_size = 80
        page_count = (total_count + page_size - 1) // page_size

        def fetch_page(page: int) -> list[dict[str, Any]]:
            params = {
                "page": str(page),
                "num": str(page_size),
                "sort": "symbol",
                "asc": "1",
                "node": "hs_a",
                "symbol": "",
                "_s_r_a": "page",
            }
            response = requests.get(
                data_url, params=params, headers=self.sina_headers, timeout=20
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError(f"unexpected page payload for page {page}")
            return payload

        rows: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(fetch_page, page): page
                for page in range(1, page_count + 1)
            }
            for future in as_completed(futures):
                rows.extend(future.result())

        return pd.DataFrame(rows)
