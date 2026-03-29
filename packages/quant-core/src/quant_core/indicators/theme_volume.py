from __future__ import annotations

from quant_core.indicators.base import BaseIndicator
from quant_core.types import (
    IndicatorContext,
    IndicatorDefinition,
    IndicatorRequirements,
    IndicatorResult,
)


class ThemeVolumeIndicator(BaseIndicator):
    indicator_key = "active_themes"
    display_name = "Active Themes"

    def get_requirements(
        self, definition: IndicatorDefinition
    ) -> IndicatorRequirements:
        window_days = int(definition.config.get("window_days", 20))
        return IndicatorRequirements(historical_theme_days=window_days)

    def compute(
        self, context: IndicatorContext, definition: IndicatorDefinition
    ) -> IndicatorResult:
        themes = []
        total_turnover = 0.0
        for theme in context.active_themes:
            total_turnover += theme.turnover
            history = list(theme.history)
            history.append(
                {"date": context.as_of.isoformat(), "turnover": theme.turnover}
            )
            themes.append(
                {
                    "theme_name": theme.name,
                    "turnover": theme.turnover,
                    "rank": theme.rank,
                    "history": history,
                    "metadata": theme.metadata,
                }
            )
        return IndicatorResult(
            key=definition.key,
            name=definition.name,
            indicator_type=definition.type,
            value_numeric=total_turnover,
            value_text=str(len(themes)),
            unit="themes",
            raw_data={"themes": themes},
        )
