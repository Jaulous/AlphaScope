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

from unittest.mock import patch

from quant_core.ingestion.akshare_provider import AkShareProvider


class _FakeRecvConn:
    def __init__(self) -> None:
        self.payload = None
        self.closed = False

    def poll(self) -> bool:
        return self.payload is not None

    def recv(self) -> dict:
        return self.payload

    def close(self) -> None:
        self.closed = True


class _FakeSendConn:
    def __init__(self, recv_conn: _FakeRecvConn) -> None:
        self.recv_conn = recv_conn

    def close(self) -> None:
        return None


class _FakeProcess:
    def __init__(self, board_name: str, send_conn: _FakeSendConn, behaviors: dict[str, str]) -> None:
        self.board_name = board_name
        self.send_conn = send_conn
        self.behaviors = behaviors
        self.exitcode: int | None = None
        self._alive = False

    def start(self) -> None:
        behavior = self.behaviors[self.board_name]
        if behavior == "success":
            self.send_conn.recv_conn.payload = {
                "ok": True,
                "rows": [
                    {
                        "代码": "000001",
                        "名称": "Ping An",
                        "成交额": 123.0,
                        "涨跌幅": 2.5,
                    }
                ],
            }
            self.exitcode = 0
            self._alive = False
            return

        self.exitcode = None
        self._alive = True

    def join(self, timeout: float | None = None) -> None:
        return None

    def is_alive(self) -> bool:
        return self._alive

    def terminate(self) -> None:
        self._alive = False
        self.exitcode = -15

    def kill(self) -> None:
        self._alive = False
        self.exitcode = -9


class _FakeContext:
    def __init__(self, behaviors: dict[str, str]) -> None:
        self.behaviors = behaviors

    def Pipe(self, duplex: bool = False) -> tuple[_FakeRecvConn, _FakeSendConn]:
        recv_conn = _FakeRecvConn()
        send_conn = _FakeSendConn(recv_conn)
        return recv_conn, send_conn

    def Process(self, target=None, args=None, daemon=None) -> _FakeProcess:
        board_name, send_conn = args
        return _FakeProcess(board_name=board_name, send_conn=send_conn, behaviors=self.behaviors)


class ConceptBoardConstituentTimeoutTests(unittest.TestCase):
    def test_partial_rows_are_preserved_when_global_budget_expires(self) -> None:
        provider = AkShareProvider()
        fake_context = _FakeContext(
            behaviors={
                "AI": "success",
                "Robotics": "hang",
                "Chip": "hang",
            }
        )

        with (
            patch(
                "quant_core.ingestion.akshare_provider.get_context",
                return_value=fake_context,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_MAX_WORKERS",
                2,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_TOTAL_TIMEOUT_SECONDS",
                0.01,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_POLL_INTERVAL_SECONDS",
                0.0,
            ),
            patch(
                "quant_core.ingestion.akshare_provider.sleep",
                side_effect=lambda _: __import__("time").sleep(0.02),
            ),
        ):
            artifact = provider.fetch_concept_board_constituents_artifact(
                ["AI", "Robotics", "Chip"]
            )

        self.assertEqual(artifact.metadata["requested_board_count"], 3)
        self.assertEqual(artifact.metadata["succeeded_board_count"], 1)
        self.assertEqual(len(artifact.data.index), 1)
        self.assertEqual(artifact.data.iloc[0]["board_name"], "AI")
        self.assertIn("global timeout", " ".join(artifact.metadata["errors"]))

    def test_global_budget_failure_raises_when_no_board_succeeds(self) -> None:
        provider = AkShareProvider()
        fake_context = _FakeContext(
            behaviors={
                "AI": "hang",
                "Robotics": "hang",
            }
        )

        with (
            patch(
                "quant_core.ingestion.akshare_provider.get_context",
                return_value=fake_context,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_MAX_WORKERS",
                2,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_TOTAL_TIMEOUT_SECONDS",
                0.01,
            ),
            patch(
                "quant_core.ingestion.akshare_provider._CONCEPT_BOARD_CONSTITUENT_POLL_INTERVAL_SECONDS",
                0.0,
            ),
            patch(
                "quant_core.ingestion.akshare_provider.sleep",
                side_effect=lambda _: __import__("time").sleep(0.02),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "global timeout"):
                provider.fetch_concept_board_constituents_artifact(["AI", "Robotics"])
