from __future__ import annotations

from abc import ABC, abstractmethod

from quant_core.types import IndicatorContext, IndicatorDefinition, IndicatorResult


class BaseIndicator(ABC):
    indicator_key = ""
    display_name = ""

    @abstractmethod
    def compute(self, context: IndicatorContext, definition: IndicatorDefinition) -> IndicatorResult:
        raise NotImplementedError
