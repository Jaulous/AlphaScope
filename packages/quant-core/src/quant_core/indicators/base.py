from __future__ import annotations

from abc import ABC, abstractmethod

from quant_core.types import (
    IndicatorContext,
    IndicatorDefinition,
    IndicatorRequirements,
    IndicatorResult,
)


class BaseIndicator(ABC):
    indicator_key = ""
    display_name = ""

    def get_requirements(
        self, definition: IndicatorDefinition
    ) -> IndicatorRequirements:
        return IndicatorRequirements()

    @abstractmethod
    def compute(
        self, context: IndicatorContext, definition: IndicatorDefinition
    ) -> IndicatorResult:
        raise NotImplementedError
