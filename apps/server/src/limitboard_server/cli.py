from __future__ import annotations

import argparse
import json
from typing import Any

from limitboard_server.tasks.fetch_data import run_daily_fetch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="limitboard-fetch",
        description="Run the AlphaScope daily fetch and indicator computation job.",
    )
    parser.add_argument(
        "--trigger",
        default="manual",
        choices=["manual", "scheduler", "on_demand"],
        help="Trigger label recorded in fetch_runs.",
    )
    parser.add_argument(
        "--force-non-trading",
        action="store_true",
        help="Run even when today is not a trading day.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result: dict[str, Any] = run_daily_fetch(
        trigger=args.trigger,
        force_non_trading=args.force_non_trading,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
