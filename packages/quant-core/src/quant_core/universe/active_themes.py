from __future__ import annotations

from collections import defaultdict

import pandas as pd

from quant_core.datasets import get_concept_board_daily
from quant_core.types import IndicatorContext, ThemeSelection
from .base import BaseUniverseSelection


class ActiveThemesUniverse(BaseUniverseSelection):
    def select(self, context: IndicatorContext, config: dict) -> list[ThemeSelection]:
        top_n = int(config.get("top_n", 20))
        threshold = float(config.get("threshold", 0.0))
        window_days = int(config.get("window_days", 20))
        expire_days = int(config.get("expire_days", 5))

        today = get_concept_board_daily(context)
        if today.empty:
            return []

        today = today.sort_values("turnover", ascending=False).head(top_n).copy()
        today = today[pd.to_numeric(today["turnover"], errors="coerce").fillna(0.0) >= threshold]

        history_map: dict[str, list[dict]] = defaultdict(list)
        if context.historical_theme_volume is not None and not context.historical_theme_volume.empty:
            hist = context.historical_theme_volume.copy()
            hist["indicator_date"] = pd.to_datetime(hist["indicator_date"], errors="coerce")
            cutoff = pd.Timestamp(context.as_of) - pd.Timedelta(days=window_days)
            hist = hist[hist["indicator_date"] >= cutoff]
            for _, row in hist.sort_values("indicator_date").iterrows():
                history_map[str(row["theme_name"])] .append(
                    {
                        "date": row["indicator_date"].date().isoformat(),
                        "turnover": float(row["turnover"]),
                    }
                )

        selected: list[ThemeSelection] = []
        for _, row in today.iterrows():
            theme_name = str(row["theme_name"])
            history = history_map.get(theme_name, [])
            recently_seen = True
            if history:
                last_seen = pd.Timestamp(history[-1]["date"])
                recently_seen = (pd.Timestamp(context.as_of) - last_seen).days <= expire_days
            if not history or recently_seen:
                selected.append(
                    ThemeSelection(
                        name=theme_name,
                        turnover=float(row["turnover"]),
                        rank=int(row["rank"]),
                        history=history,
                        metadata={
                            "pct_change": float(row["pct_change"]) if pd.notna(row["pct_change"]) else None,
                            "leader": row.get("leader"),
                            "advancers": int(row["advancers"]) if pd.notna(row["advancers"]) else None,
                            "decliners": int(row["decliners"]) if pd.notna(row["decliners"]) else None,
                        },
                    )
                )

        return selected
