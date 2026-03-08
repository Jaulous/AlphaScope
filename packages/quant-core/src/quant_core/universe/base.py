from __future__ import annotations

from abc import ABC, abstractmethod

from quant_core.types import IndicatorContext, ThemeSelection


class BaseUniverseSelection(ABC):
    @abstractmethod
    def select(self, context: IndicatorContext, config: dict) -> list[ThemeSelection]:
        raise NotImplementedError
