from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from quant_core.types import IndicatorDefinition
from supabase import Client, create_client

from limitboard_server.defaults import DEFAULT_INDICATOR_DEFINITIONS


class SupabaseStore:
    def __init__(self, supabase_url: str, secret_key: str) -> None:
        self.client: Client = create_client(supabase_url, secret_key)

    def ensure_indicator_definitions(self) -> list[IndicatorDefinition]:
        response = self.client.table("indicator_definitions").select("*").execute()
        rows = response.data or []
        existing_keys = {row["key"] for row in rows}
        missing_defaults = [
            item
            for item in DEFAULT_INDICATOR_DEFINITIONS
            if item["key"] not in existing_keys
        ]
        if missing_defaults:
            self.client.table("indicator_definitions").upsert(
                missing_defaults, on_conflict="key"
            ).execute()
            rows.extend(missing_defaults)
        elif not rows:
            self.client.table("indicator_definitions").upsert(
                DEFAULT_INDICATOR_DEFINITIONS, on_conflict="key"
            ).execute()
            rows = list(DEFAULT_INDICATOR_DEFINITIONS)
        return [
            IndicatorDefinition(
                key=row["key"],
                type=row["type"],
                name=row["name"],
                enabled=row.get("enabled", True),
                config=row.get("config", {}),
                description=row.get("description"),
            )
            for row in rows
            if row.get("enabled", True)
        ]

    def fetch_indicator_history(self, lookback_days: int = 60) -> pd.DataFrame:
        since = (date.today() - timedelta(days=lookback_days)).isoformat()
        response = (
            self.client.table("daily_indicators")
            .select("key,indicator_date,value_numeric")
            .gte("indicator_date", since)
            .order("indicator_date", desc=False)
            .execute()
        )
        return pd.DataFrame(response.data or [])

    def fetch_raw_market_snapshot(self, snapshot_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_market_snapshot_daily")
            .select(
                "snapshot_date,symbol,name,last_price,pct_change,change_amount,volume,turnover,amplitude,turnover_rate,pe_dynamic,metadata"
            )
            .eq("snapshot_date", snapshot_date.isoformat())
            .order("symbol", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
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
                "metadata",
            ],
        )

    def fetch_raw_limit_up_pool(self, snapshot_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_limit_up_pool_daily")
            .select(
                "snapshot_date,symbol,name,board_count,seal_funds,turnover_rate,first_limit_time,last_limit_time,metadata"
            )
            .eq("snapshot_date", snapshot_date.isoformat())
            .order("symbol", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
                "symbol",
                "name",
                "board_count",
                "seal_funds",
                "turnover_rate",
                "first_limit_time",
                "last_limit_time",
                "metadata",
            ],
        )

    def fetch_raw_limit_up_pool_history(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        response = (
            self.client.table("raw_limit_up_pool_daily")
            .select(
                "snapshot_date,symbol,name,board_count,seal_funds,turnover_rate,first_limit_time,last_limit_time,metadata"
            )
            .gte("snapshot_date", start_date.isoformat())
            .lte("snapshot_date", end_date.isoformat())
            .order("snapshot_date", desc=False)
            .order("symbol", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
                "symbol",
                "name",
                "board_count",
                "seal_funds",
                "turnover_rate",
                "first_limit_time",
                "last_limit_time",
                "metadata",
            ],
        )

    def fetch_raw_concept_boards(self, snapshot_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_concept_boards_daily")
            .select(
                "snapshot_date,theme_name,turnover,pct_change,market_cap,advancers,decliners,leader,rank,metadata"
            )
            .eq("snapshot_date", snapshot_date.isoformat())
            .order("rank", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
                "theme_name",
                "turnover",
                "pct_change",
                "market_cap",
                "advancers",
                "decliners",
                "leader",
                "rank",
                "metadata",
            ],
        )

    def fetch_raw_equity_daily_quotes_v2(self, trade_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_equity_daily_quotes")
            .select(
                "trade_date,symbol,market,exchange,name,open,high,low,close,pre_close,change_amount,pct_change,volume,turnover,turnover_rate,amplitude,volume_ratio,pe_dynamic,pb,total_market_cap,float_market_cap,limit_up_price,limit_down_price,is_limit_up,is_limit_down,is_suspended,source_name,source_payload,metadata"
            )
            .eq("trade_date", trade_date.isoformat())
            .order("symbol", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "trade_date",
                "symbol",
                "market",
                "exchange",
                "name",
                "open",
                "high",
                "low",
                "close",
                "pre_close",
                "change_amount",
                "pct_change",
                "volume",
                "turnover",
                "turnover_rate",
                "amplitude",
                "volume_ratio",
                "pe_dynamic",
                "pb",
                "total_market_cap",
                "float_market_cap",
                "limit_up_price",
                "limit_down_price",
                "is_limit_up",
                "is_limit_down",
                "is_suspended",
                "source_name",
                "source_payload",
                "metadata",
            ],
        )

    def fetch_raw_equity_daily_limit_events_v2(self, trade_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_equity_daily_limit_events")
            .select(
                "trade_date,symbol,event_side,market,name,board_count,seal_amount,seal_volume,turnover_rate,open_times,first_limit_time,last_limit_time,limit_reason,limit_type,source_name,source_payload,metadata"
            )
            .eq("trade_date", trade_date.isoformat())
            .order("event_side", desc=False)
            .order("symbol", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "trade_date",
                "symbol",
                "event_side",
                "market",
                "name",
                "board_count",
                "seal_amount",
                "seal_volume",
                "turnover_rate",
                "open_times",
                "first_limit_time",
                "last_limit_time",
                "limit_reason",
                "limit_type",
                "source_name",
                "source_payload",
                "metadata",
            ],
        )

    def fetch_raw_equity_daily_limit_events_history_v2(
        self,
        start_date: date,
        end_date: date,
        *,
        event_side: str | None = None,
    ) -> pd.DataFrame:
        query = (
            self.client.table("raw_equity_daily_limit_events")
            .select(
                "trade_date,symbol,event_side,market,name,board_count,seal_amount,seal_volume,turnover_rate,open_times,first_limit_time,last_limit_time,limit_reason,limit_type,source_name,source_payload,metadata"
            )
            .gte("trade_date", start_date.isoformat())
            .lte("trade_date", end_date.isoformat())
            .order("trade_date", desc=False)
            .order("symbol", desc=False)
        )
        if event_side:
            query = query.eq("event_side", event_side)
        response = query.execute()
        return pd.DataFrame(
            response.data or [],
            columns=[
                "trade_date",
                "symbol",
                "event_side",
                "market",
                "name",
                "board_count",
                "seal_amount",
                "seal_volume",
                "turnover_rate",
                "open_times",
                "first_limit_time",
                "last_limit_time",
                "limit_reason",
                "limit_type",
                "source_name",
                "source_payload",
                "metadata",
            ],
        )

    def fetch_raw_concept_board_daily_v2(self, trade_date: date) -> pd.DataFrame:
        response = (
            self.client.table("raw_concept_board_daily")
            .select(
                "trade_date,board_type,board_name,board_code,turnover,pct_change,market_cap,advancers,decliners,leader,member_count,rank,source_name,source_payload,metadata"
            )
            .eq("trade_date", trade_date.isoformat())
            .order("rank", desc=False)
            .execute()
        )
        return pd.DataFrame(
            response.data or [],
            columns=[
                "trade_date",
                "board_type",
                "board_name",
                "board_code",
                "turnover",
                "pct_change",
                "market_cap",
                "advancers",
                "decliners",
                "leader",
                "member_count",
                "rank",
                "source_name",
                "source_payload",
                "metadata",
            ],
        )

    def fetch_raw_stock_kline(
        self, snapshot_date: date, symbols: list[str] | None = None
    ) -> pd.DataFrame:
        query = (
            self.client.table("raw_stock_kline_daily")
            .select(
                "snapshot_date,ts,symbol,name,open,high,low,close,volume,turnover,amplitude,pct_change,metadata"
            )
            .eq("snapshot_date", snapshot_date.isoformat())
            .order("ts", desc=False)
        )
        if symbols:
            query = query.in_("symbol", symbols)
        response = query.execute()
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
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
                "metadata",
            ],
        )

    def fetch_raw_stock_kline_history(
        self,
        start_date: date,
        end_date: date,
        symbols: list[str] | None = None,
    ) -> pd.DataFrame:
        query = (
            self.client.table("raw_stock_kline_daily")
            .select(
                "snapshot_date,ts,symbol,name,open,high,low,close,volume,turnover,amplitude,pct_change,metadata"
            )
            .gte("snapshot_date", start_date.isoformat())
            .lte("snapshot_date", end_date.isoformat())
            .order("ts", desc=False)
        )
        if symbols:
            query = query.in_("symbol", symbols)
        response = query.execute()
        return pd.DataFrame(
            response.data or [],
            columns=[
                "snapshot_date",
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
                "metadata",
            ],
        )

    def fetch_theme_history(self, lookback_days: int = 60) -> pd.DataFrame:
        since = (date.today() - timedelta(days=lookback_days)).isoformat()
        response = (
            self.client.table("daily_themes_volume")
            .select("indicator_date,theme_name,turnover,rank,metadata")
            .gte("indicator_date", since)
            .order("indicator_date", desc=False)
            .execute()
        )
        return pd.DataFrame(response.data or [])

    def fetch_indicator_definitions(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("indicator_definitions")
            .select("key,type,name,enabled,config,description")
            .order("key", desc=False)
            .execute()
        )
        return response.data or []

    def latest_snapshot_date(self) -> str | None:
        response = (
            self.client.table("daily_indicators")
            .select("indicator_date")
            .order("indicator_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return rows[0].get("indicator_date")

    def fetch_snapshot_dates(self, start_date: date, end_date: date) -> set[date]:
        response = (
            self.client.table("daily_indicators")
            .select("indicator_date")
            .gte("indicator_date", start_date.isoformat())
            .lte("indicator_date", end_date.isoformat())
            .order("indicator_date", desc=False)
            .execute()
        )
        rows = response.data or []
        snapshot_dates: set[date] = set()
        for row in rows:
            raw_value = row.get("indicator_date")
            if not raw_value:
                continue
            snapshot_dates.add(date.fromisoformat(str(raw_value)))
        return snapshot_dates

    def has_serving_snapshot(self, as_of: date) -> bool:
        response = (
            self.client.table("daily_indicators")
            .select("key", count="exact")
            .eq("indicator_date", as_of.isoformat())
            .limit(1)
            .execute()
        )
        return bool(response.count)

    def record_fetch_run(
        self,
        *,
        trigger: str,
        reference_date: date,
        target_date: date,
        status: str,
        skipped_reason: str | None = None,
        source_statuses: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        counts: dict[str, Any] | None = None,
    ) -> None:
        self.client.table("fetch_runs").insert(
            self._sanitize_row(
                {
                    "trigger": trigger,
                    "reference_date": reference_date.isoformat(),
                    "target_date": target_date.isoformat(),
                    "status": status,
                    "skipped_reason": skipped_reason,
                    "source_statuses": source_statuses or {},
                    "warnings": warnings or [],
                    "counts": counts or {},
                }
            )
        ).execute()

    def create_raw_ingestion_run(
        self,
        *,
        trigger: str,
        dataset_key: str,
        source_name: str,
        status: str,
        market: str = "CN_A",
        as_of_date: date | None = None,
        request_params: dict[str, Any] | None = None,
        row_count: int | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int | None:
        payload = self._sanitize_row(
            {
                "trigger": trigger,
                "dataset_key": dataset_key,
                "source_name": source_name,
                "market": market,
                "as_of_date": as_of_date.isoformat() if as_of_date else None,
                "request_params": request_params or {},
                "status": status,
                "row_count": row_count,
                "error_message": error_message,
                "started_at": started_at.isoformat() if started_at else None,
                "finished_at": finished_at.isoformat() if finished_at else None,
                "metadata": metadata or {},
            }
        )
        response = self.client.table("raw_ingestion_runs").insert(payload).execute()
        rows = response.data or []
        if not rows:
            return None
        raw_id = rows[0].get("id")
        return int(raw_id) if raw_id is not None else None

    def create_raw_dataset_batch(
        self,
        *,
        run_id: int | None,
        dataset_key: str,
        source_name: str,
        source_endpoint: str | None = None,
        market: str = "CN_A",
        as_of_date: date | None = None,
        snapshot_time: datetime | None = None,
        fetch_params: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int | None:
        sanitized_rows = self._sanitize_rows(rows or [])
        payload_hash = hashlib.sha256(
            json.dumps(
                sanitized_rows,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        payload = self._sanitize_row(
            {
                "run_id": run_id,
                "dataset_key": dataset_key,
                "source_name": source_name,
                "source_endpoint": source_endpoint,
                "market": market,
                "as_of_date": as_of_date.isoformat() if as_of_date else None,
                "snapshot_time": snapshot_time.isoformat() if snapshot_time else None,
                "fetch_params": fetch_params or {},
                "column_names": sorted(
                    {
                        key
                        for row in sanitized_rows
                        for key in row.keys()
                    }
                ),
                "record_count": len(sanitized_rows),
                "payload_sha256": payload_hash,
                "metadata": metadata or {},
            }
        )
        response = self.client.table("raw_dataset_batches").insert(payload).execute()
        rows = response.data or []
        if not rows:
            return None
        raw_id = rows[0].get("id")
        return int(raw_id) if raw_id is not None else None

    def insert_raw_source_payload_rows(
        self, batch_id: int | None, rows: list[dict[str, Any]]
    ) -> int:
        if batch_id is None or not rows:
            return 0
        payload = []
        sanitized_rows = self._sanitize_rows(rows)
        for index, row in enumerate(sanitized_rows, start=1):
            natural_key = self._build_payload_natural_key(row)
            payload.append(
                {
                    "batch_id": batch_id,
                    "row_no": index,
                    "natural_key": natural_key,
                    "payload": row,
                }
            )
        self.client.table("raw_source_payload_rows").insert(payload).execute()
        return len(payload)

    def fetch_latest_fetch_run(self) -> dict[str, Any] | None:
        response = (
            self.client.table("fetch_runs")
            .select(
                "id,trigger,reference_date,target_date,status,skipped_reason,source_statuses,warnings,counts,created_at"
            )
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return rows[0]

    def upsert_indicator_results(self, as_of: date, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        payload = []
        for row in rows:
            payload.append(
                {
                    "key": row["key"],
                    "indicator_date": as_of.isoformat(),
                    "title": row["title"],
                    "type": row["type"],
                    "value_numeric": row.get("value_numeric"),
                    "value_text": row.get("value_text"),
                    "delta": row.get("delta"),
                    "unit": row.get("unit"),
                    "raw_data": row.get("raw_data", {}),
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["key", "indicator_date"])
        )
        self.client.table("daily_indicators").upsert(
            payload, on_conflict="key,indicator_date"
        ).execute()

    def upsert_raw_market_snapshot(self, as_of: date, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        payload = []
        for _, row in df.iterrows():
            payload.append(
                {
                    "snapshot_date": as_of.isoformat(),
                    "symbol": str(row.get("symbol")),
                    "name": row.get("name"),
                    "last_price": row.get("last_price"),
                    "pct_change": row.get("pct_change"),
                    "change_amount": row.get("change_amount"),
                    "volume": row.get("volume"),
                    "turnover": row.get("turnover"),
                    "amplitude": row.get("amplitude"),
                    "turnover_rate": row.get("turnover_rate"),
                    "pe_dynamic": row.get("pe_dynamic"),
                    "metadata": {},
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["snapshot_date", "symbol"])
        )
        self.client.table("raw_market_snapshot_daily").upsert(
            payload, on_conflict="snapshot_date,symbol"
        ).execute()
        return len(payload)

    def upsert_raw_limit_up_pool(self, as_of: date, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        payload = []
        for _, row in df.iterrows():
            payload.append(
                {
                    "snapshot_date": as_of.isoformat(),
                    "symbol": str(row.get("symbol")),
                    "name": row.get("name"),
                    "board_count": row.get("board_count"),
                    "seal_funds": row.get("seal_funds"),
                    "turnover_rate": row.get("turnover_rate"),
                    "first_limit_time": row.get("first_limit_time"),
                    "last_limit_time": row.get("last_limit_time"),
                    "metadata": {},
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["snapshot_date", "symbol"])
        )
        self.client.table("raw_limit_up_pool_daily").upsert(
            payload, on_conflict="snapshot_date,symbol"
        ).execute()
        return len(payload)

    def upsert_raw_concept_boards(self, as_of: date, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        payload = []
        for _, row in df.iterrows():
            payload.append(
                {
                    "snapshot_date": as_of.isoformat(),
                    "theme_name": row.get("theme_name"),
                    "turnover": row.get("turnover"),
                    "pct_change": row.get("pct_change"),
                    "market_cap": row.get("market_cap"),
                    "advancers": row.get("advancers"),
                    "decliners": row.get("decliners"),
                    "leader": row.get("leader"),
                    "rank": row.get("rank"),
                    "metadata": {},
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["snapshot_date", "theme_name"])
        )
        self.client.table("raw_concept_boards_daily").upsert(
            payload, on_conflict="snapshot_date,theme_name"
        ).execute()
        return len(payload)

    def upsert_raw_stock_kline_rows(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        payload = []
        for row in rows:
            snapshot_date = str(row["ts"])[:10]
            payload.append(
                {
                    "snapshot_date": snapshot_date,
                    "ts": row["ts"],
                    "symbol": row["symbol"],
                    "name": row.get("name"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume"),
                    "turnover": row.get("turnover"),
                    "amplitude": row.get("amplitude"),
                    "pct_change": row.get("pct_change"),
                    "metadata": row.get("metadata", {}),
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["ts", "symbol"])
        )
        self.client.table("raw_stock_kline_daily").upsert(
            payload, on_conflict="ts,symbol"
        ).execute()
        return len(payload)

    def upsert_raw_trade_calendar(
        self,
        trade_dates: set[date],
        *,
        market: str = "CN_A",
        source_name: str = "akshare",
    ) -> int:
        if not trade_dates:
            return 0
        payload = [
            {
                "market": market,
                "trade_date": trade_date.isoformat(),
                "is_trading_day": True,
                "source_name": source_name,
                "source_payload": {},
                "metadata": {},
            }
            for trade_date in sorted(trade_dates)
        ]
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["market", "trade_date"])
        )
        self.client.table("raw_trade_calendar").upsert(
            payload, on_conflict="market,trade_date"
        ).execute()
        return len(payload)

    def upsert_raw_security_master(
        self,
        market_snapshot: pd.DataFrame,
        *,
        market: str = "CN_A",
        source_name: str = "akshare",
    ) -> int:
        if market_snapshot.empty:
            return 0
        payload = []
        for _, row in market_snapshot.iterrows():
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            payload.append(
                {
                    "market": market,
                    "symbol": symbol,
                    "exchange": self._infer_exchange(symbol),
                    "security_type": "equity",
                    "name": row.get("name"),
                    "board": self._infer_board(symbol),
                    "industry": None,
                    "list_date": None,
                    "delist_date": None,
                    "status": "active",
                    "source_name": source_name,
                    "source_payload": {},
                    "metadata": {},
                    "updated_at": datetime.now(tz=ZoneInfo("UTC")).isoformat(),
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["market", "symbol"])
        )
        self.client.table("raw_security_master").upsert(
            payload, on_conflict="market,symbol"
        ).execute()
        return len(payload)

    def upsert_raw_equity_daily_quotes(
        self,
        as_of: date,
        market_snapshot: pd.DataFrame,
        *,
        limit_up_pool: pd.DataFrame | None = None,
        market: str = "CN_A",
        source_name: str = "akshare",
    ) -> int:
        if market_snapshot.empty:
            return 0
        limit_up_symbols = set()
        if limit_up_pool is not None and not limit_up_pool.empty:
            limit_up_symbols = set(
                limit_up_pool["symbol"].dropna().astype(str).tolist()
            )

        payload = []
        for _, row in market_snapshot.iterrows():
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            pct_change = row.get("pct_change")
            payload.append(
                {
                    "trade_date": as_of.isoformat(),
                    "symbol": symbol,
                    "market": market,
                    "exchange": self._infer_exchange(symbol),
                    "name": row.get("name"),
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": row.get("last_price"),
                    "pre_close": None,
                    "change_amount": row.get("change_amount"),
                    "pct_change": pct_change,
                    "volume": row.get("volume"),
                    "turnover": row.get("turnover"),
                    "turnover_rate": row.get("turnover_rate"),
                    "amplitude": row.get("amplitude"),
                    "volume_ratio": None,
                    "pe_dynamic": row.get("pe_dynamic"),
                    "pb": None,
                    "total_market_cap": None,
                    "float_market_cap": None,
                    "limit_up_price": None,
                    "limit_down_price": None,
                    "is_limit_up": symbol in limit_up_symbols
                    or self._is_limit_threshold_hit(pct_change, threshold=9.8),
                    "is_limit_down": self._is_limit_threshold_hit(
                        pct_change, threshold=-9.8
                    ),
                    "is_suspended": False,
                    "source_name": source_name,
                    "source_payload": {},
                    "metadata": {},
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["trade_date", "symbol"])
        )
        self.client.table("raw_equity_daily_quotes").upsert(
            payload, on_conflict="trade_date,symbol"
        ).execute()
        return len(payload)

    def upsert_raw_equity_daily_limit_events(
        self,
        as_of: date,
        *,
        limit_up_pool: pd.DataFrame,
        market_snapshot: pd.DataFrame | None = None,
        market: str = "CN_A",
        source_name: str = "akshare",
    ) -> int:
        payload: list[dict[str, Any]] = []
        if limit_up_pool is not None and not limit_up_pool.empty:
            for _, row in limit_up_pool.iterrows():
                symbol = str(row.get("symbol") or "").strip()
                if not symbol:
                    continue
                payload.append(
                    {
                        "trade_date": as_of.isoformat(),
                        "symbol": symbol,
                        "event_side": "up",
                        "market": market,
                        "name": row.get("name"),
                        "board_count": row.get("board_count"),
                        "seal_amount": row.get("seal_funds"),
                        "seal_volume": None,
                        "turnover_rate": row.get("turnover_rate"),
                        "open_times": None,
                        "first_limit_time": row.get("first_limit_time"),
                        "last_limit_time": row.get("last_limit_time"),
                        "limit_reason": None,
                        "limit_type": "pool",
                        "source_name": source_name,
                        "source_payload": {},
                        "metadata": {},
                    }
                )

        if market_snapshot is not None and not market_snapshot.empty:
            for _, row in market_snapshot.iterrows():
                symbol = str(row.get("symbol") or "").strip()
                if not symbol:
                    continue
                if not self._is_limit_threshold_hit(row.get("pct_change"), -9.8):
                    continue
                payload.append(
                    {
                        "trade_date": as_of.isoformat(),
                        "symbol": symbol,
                        "event_side": "down",
                        "market": market,
                        "name": row.get("name"),
                        "board_count": None,
                        "seal_amount": None,
                        "seal_volume": None,
                        "turnover_rate": row.get("turnover_rate"),
                        "open_times": None,
                        "first_limit_time": None,
                        "last_limit_time": None,
                        "limit_reason": None,
                        "limit_type": "threshold_proxy",
                        "source_name": source_name,
                        "source_payload": {},
                        "metadata": {
                            "pct_change": self._sanitize_value(row.get("pct_change")),
                        },
                    }
                )

        if not payload:
            return 0

        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["trade_date", "symbol", "event_side"])
        )
        self.client.table("raw_equity_daily_limit_events").upsert(
            payload, on_conflict="trade_date,symbol,event_side"
        ).execute()
        return len(payload)

    def upsert_raw_concept_board_daily(
        self,
        as_of: date,
        concept_boards: pd.DataFrame,
        *,
        board_type: str = "concept",
        source_name: str = "akshare",
    ) -> int:
        if concept_boards.empty:
            return 0
        payload = []
        for _, row in concept_boards.iterrows():
            board_name = str(row.get("theme_name") or "").strip()
            if not board_name:
                continue
            advancers = self._safe_int(row.get("advancers"))
            decliners = self._safe_int(row.get("decliners"))
            member_count = None
            if advancers is not None or decliners is not None:
                member_count = (advancers or 0) + (decliners or 0)
            payload.append(
                {
                    "trade_date": as_of.isoformat(),
                    "board_type": board_type,
                    "board_name": board_name,
                    "board_code": None,
                    "turnover": row.get("turnover"),
                    "pct_change": row.get("pct_change"),
                    "market_cap": row.get("market_cap"),
                    "advancers": advancers,
                    "decliners": decliners,
                    "leader": row.get("leader"),
                    "member_count": member_count,
                    "rank": row.get("rank"),
                    "source_name": source_name,
                    "source_payload": {},
                    "metadata": {},
                }
            )
        payload = self._sanitize_rows(
            self._dedupe_payload(payload, keys=["trade_date", "board_type", "board_name"])
        )
        self.client.table("raw_concept_board_daily").upsert(
            payload, on_conflict="trade_date,board_type,board_name"
        ).execute()
        return len(payload)

    def upsert_theme_rows(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        rows = self._sanitize_rows(
            self._dedupe_payload(rows, keys=["indicator_date", "theme_name"])
        )
        self.client.table("daily_themes_volume").upsert(
            rows, on_conflict="indicator_date,theme_name"
        ).execute()

    def upsert_stock_kline_rows(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        rows = self._sanitize_rows(self._dedupe_payload(rows, keys=["ts", "symbol"]))
        self.client.table("stock_kline_daily").upsert(
            rows, on_conflict="ts,symbol"
        ).execute()

    def upsert_dashboard_payload(self, payload: dict[str, Any]) -> dict[str, int]:
        as_of_raw = payload.get("as_of")
        if not as_of_raw:
            raise ValueError("dashboard payload missing as_of")
        as_of = date.fromisoformat(str(as_of_raw))

        indicator_rows = [
            {
                "key": item["key"],
                "title": item["title"],
                "type": item["type"],
                "value_numeric": item.get("value_numeric"),
                "value_text": item.get("value_text"),
                "delta": item.get("delta"),
                "unit": item.get("unit"),
                "raw_data": item.get("raw_data") or {},
            }
            for item in payload.get("indicators", [])
        ]
        theme_rows = [
            {
                "indicator_date": as_of.isoformat(),
                "theme_name": item["theme_name"],
                "turnover": item["latest_turnover"],
                "rank": item["rank"],
                "metadata": item.get("metadata") or {},
            }
            for item in payload.get("active_themes", [])
        ]
        stock_rows: list[dict[str, Any]] = []
        for stock in payload.get("tracked_stocks", []):
            for point in stock.get("history", []) or []:
                stock_rows.append(
                    {
                        "ts": point["ts"],
                        "symbol": stock["symbol"],
                        "name": stock.get("name"),
                        "open": point.get("open"),
                        "high": point.get("high"),
                        "low": point.get("low"),
                        "close": point.get("close"),
                        "volume": point.get("volume"),
                        "turnover": point.get("turnover"),
                        "amplitude": point.get("amplitude"),
                        "pct_change": point.get("pct_change"),
                        "metadata": {},
                    }
                )

        self.upsert_indicator_results(as_of, indicator_rows)
        self.upsert_theme_rows(theme_rows)
        self.upsert_stock_kline_rows(stock_rows)
        return {
            "indicator_count": len(indicator_rows),
            "theme_count": len(theme_rows),
            "stock_kline_count": len(stock_rows),
        }

    def fetch_stock_kline_history(
        self, symbol: str, lookback_days: int = 30
    ) -> list[dict[str, Any]]:
        since = (date.today() - timedelta(days=lookback_days)).isoformat()
        response = (
            self.client.table("stock_kline_daily")
            .select(
                "ts,symbol,name,open,high,low,close,volume,turnover,amplitude,pct_change,metadata"
            )
            .eq("symbol", symbol)
            .gte("ts", since)
            .order("ts", desc=False)
            .execute()
        )
        return response.data or []

    def fetch_dashboard_snapshot(self, lookback_days: int = 60) -> dict[str, Any]:
        as_of_raw = self.latest_snapshot_date()
        if not as_of_raw:
            return {
                "as_of": None,
                "market_breadth": None,
                "indicators": [],
                "active_themes": [],
                "tracked_stocks": [],
            }

        as_of = date.fromisoformat(as_of_raw)
        since = (as_of - timedelta(days=lookback_days)).isoformat()
        stock_since = self._market_day_start(as_of - timedelta(days=lookback_days))
        stock_day_start = self._market_day_start(as_of)
        stock_next_day_start = self._market_day_start(as_of + timedelta(days=1))

        latest_indicator_rows = (
            self.client.table("daily_indicators")
            .select(
                "key,indicator_date,title,type,value_numeric,value_text,delta,unit,raw_data"
            )
            .eq("indicator_date", as_of.isoformat())
            .order("key", desc=False)
            .execute()
            .data
            or []
        )
        indicator_keys = [row["key"] for row in latest_indicator_rows]
        indicator_rows = []
        if indicator_keys:
            indicator_rows = (
                self.client.table("daily_indicators")
                .select(
                    "key,indicator_date,title,type,value_numeric,value_text,delta,unit,raw_data"
                )
                .in_("key", indicator_keys)
                .gte("indicator_date", since)
                .order("indicator_date", desc=False)
                .execute()
                .data
                or []
            )

        latest_theme_rows = (
            self.client.table("daily_themes_volume")
            .select("indicator_date,theme_name,turnover,rank,metadata")
            .eq("indicator_date", as_of.isoformat())
            .order("rank", desc=False)
            .execute()
            .data
            or []
        )
        theme_names = [row["theme_name"] for row in latest_theme_rows]
        theme_rows = []
        if theme_names:
            theme_rows = (
                self.client.table("daily_themes_volume")
                .select("indicator_date,theme_name,turnover,rank,metadata")
                .in_("theme_name", theme_names)
                .gte("indicator_date", since)
                .order("indicator_date", desc=False)
                .execute()
                .data
                or []
            )

        latest_stock_rows = (
            self.client.table("stock_kline_daily")
            .select(
                "ts,symbol,name,open,high,low,close,volume,turnover,amplitude,pct_change"
            )
            .gte("ts", stock_day_start)
            .lt("ts", stock_next_day_start)
            .order("turnover", desc=True)
            .execute()
            .data
            or []
        )
        stock_symbols = [row["symbol"] for row in latest_stock_rows]
        stock_rows = []
        if stock_symbols:
            stock_rows = (
                self.client.table("stock_kline_daily")
                .select(
                    "ts,symbol,name,open,high,low,close,volume,turnover,amplitude,pct_change"
                )
                .in_("symbol", stock_symbols)
                .gte("ts", stock_since)
                .order("ts", desc=False)
                .execute()
                .data
                or []
            )

        latest_by_key: dict[str, dict[str, Any]] = {}
        history_by_key: dict[str, list[dict[str, Any]]] = {}
        for row in indicator_rows:
            history_by_key.setdefault(row["key"], []).append(
                {"date": row["indicator_date"], "value": row.get("value_numeric")}
            )
            latest_by_key[row["key"]] = row

        theme_history: dict[str, list[dict[str, Any]]] = {}
        latest_theme_meta: dict[str, dict[str, Any]] = {}
        for row in theme_rows:
            theme = row["theme_name"]
            theme_history.setdefault(theme, []).append(
                {"date": row["indicator_date"], "turnover": float(row["turnover"])}
            )
            latest_theme_meta[theme] = row

        indicators = []
        for key, row in latest_by_key.items():
            indicators.append(
                {
                    **row,
                    "history": history_by_key.get(key, []),
                }
            )

        active_themes = [
            {
                "theme_name": theme,
                "rank": int(meta["rank"]),
                "latest_turnover": float(meta["turnover"]),
                "history": theme_history.get(theme, []),
                "metadata": meta.get("metadata") or {},
            }
            for theme, meta in sorted(
                latest_theme_meta.items(), key=lambda item: item[1]["rank"]
            )
        ]

        stock_history: dict[str, list[dict[str, Any]]] = {}
        stock_meta: dict[str, dict[str, Any]] = {}
        for row in stock_rows:
            symbol = row["symbol"]
            stock_history.setdefault(symbol, []).append(
                {
                    "ts": row["ts"],
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume"),
                    "turnover": row.get("turnover"),
                    "amplitude": row.get("amplitude"),
                    "pct_change": row.get("pct_change"),
                }
            )
            stock_meta[symbol] = row

        tracked_stocks = [
            {
                "symbol": symbol,
                "name": meta.get("name"),
                "latest_close": meta.get("close"),
                "latest_pct_change": meta.get("pct_change"),
                "latest_turnover": meta.get("turnover"),
                "history": stock_history.get(symbol, []),
            }
            for symbol, meta in sorted(
                stock_meta.items(),
                key=lambda item: float(item[1].get("turnover") or 0),
                reverse=True,
            )
        ]

        market_breadth = None
        if as_of_raw:
            raw_market_rows = (
                self.client.table("raw_market_snapshot_daily")
                .select("pct_change")
                .eq("snapshot_date", as_of_raw)
                .execute()
                .data
                or []
            )
            if raw_market_rows:
                raw_market_df = pd.DataFrame(raw_market_rows)
                raw_market_df["pct_change"] = pd.to_numeric(
                    raw_market_df["pct_change"], errors="coerce"
                )
                market_breadth = {
                    "advancers": int((raw_market_df["pct_change"] > 0).sum()),
                    "decliners": int((raw_market_df["pct_change"] < 0).sum()),
                    "unchanged": int((raw_market_df["pct_change"] == 0).sum()),
                }

        return {
            "as_of": as_of_raw,
            "market_breadth": market_breadth,
            "indicators": indicators,
            "active_themes": active_themes,
            "tracked_stocks": tracked_stocks,
        }

    @staticmethod
    def _dedupe_payload(
        rows: list[dict[str, Any]], keys: list[str]
    ) -> list[dict[str, Any]]:
        deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in rows:
            deduped[tuple(row.get(key) for key in keys)] = row
        return list(deduped.values())

    @classmethod
    def _sanitize_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls._sanitize_row(row) for row in rows]

    @classmethod
    def _sanitize_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {key: cls._sanitize_value(value) for key, value in row.items()}

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._sanitize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._sanitize_value(item) for item in value]
        if value is None:
            return None
        if pd.isna(value):
            return None
        if hasattr(value, "item") and not isinstance(value, (str, bytes, bytearray)):
            try:
                return value.item()
            except Exception:
                return value
        return value

    @classmethod
    def _build_payload_natural_key(cls, row: dict[str, Any]) -> str | None:
        preferred_keys = [
            "symbol",
            "代码",
            "theme_name",
            "板块名称",
            "name",
            "名称",
            "date",
            "日期",
            "ts",
            "trade_date",
        ]
        parts: list[str] = []
        for key in preferred_keys:
            value = row.get(key)
            if value is None:
                continue
            parts.append(f"{key}={value}")
        if not parts:
            return None
        return "|".join(parts)

    @staticmethod
    def _infer_exchange(symbol: str) -> str | None:
        raw = str(symbol).strip()
        if raw.startswith(("600", "601", "603", "605", "688", "689", "510", "511", "512", "513", "515", "518")):
            return "SSE"
        if raw.startswith(("000", "001", "002", "003", "300", "301", "159")):
            return "SZSE"
        if raw.startswith(("430", "800", "830", "831", "832", "833", "835", "836", "837", "838", "839")):
            return "BSE"
        return None

    @classmethod
    def _infer_board(cls, symbol: str) -> str | None:
        raw = str(symbol).strip()
        if raw.startswith(("688", "689")):
            return "STAR"
        if raw.startswith(("300", "301")):
            return "ChiNext"
        if raw.startswith(("430", "800", "830", "831", "832", "833", "835", "836", "837", "838", "839")):
            return "Beijing"
        if cls._infer_exchange(raw) == "SSE":
            return "Main"
        if cls._infer_exchange(raw) == "SZSE":
            return "Main"
        return None

    @classmethod
    def _is_limit_threshold_hit(cls, value: Any, threshold: float) -> bool:
        if value is None or pd.isna(value):
            return False
        numeric = float(value)
        if threshold >= 0:
            return numeric >= threshold
        return numeric <= threshold

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None
        return int(value)

    @staticmethod
    def _market_day_start(value: date) -> str:
        market_tz = ZoneInfo("Asia/Shanghai")
        return datetime.combine(value, time.min, tzinfo=market_tz).isoformat()
