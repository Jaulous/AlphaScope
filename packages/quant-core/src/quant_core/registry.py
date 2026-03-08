from __future__ import annotations

import importlib
import pkgutil
from typing import Type

from .indicators import base as indicator_base


class IndicatorRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Type[indicator_base.BaseIndicator]] = {}

    def register(self, indicator_cls: Type[indicator_base.BaseIndicator]) -> None:
        key = indicator_cls.indicator_key
        if not key:
            raise ValueError(f"Indicator {indicator_cls.__name__} is missing indicator_key")
        self._plugins[key] = indicator_cls

    def discover(self) -> None:
        package = importlib.import_module("quant_core.indicators")
        for module_info in pkgutil.iter_modules(package.__path__):
            if module_info.name.startswith("_") or module_info.name == "base":
                continue
            importlib.import_module(f"quant_core.indicators.{module_info.name}")

        for indicator_cls in indicator_base.BaseIndicator.__subclasses__():
            if indicator_cls.indicator_key:
                self.register(indicator_cls)

    def get(self, key: str) -> Type[indicator_base.BaseIndicator]:
        if key not in self._plugins:
            raise KeyError(f"Indicator plugin '{key}' not found")
        return self._plugins[key]

    def keys(self) -> list[str]:
        return sorted(self._plugins.keys())
