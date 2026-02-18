"""Plugin system for XLG custom commands."""

from typing import Any, Callable
from collections.abc import Generator


class Registry:
    """Registry for plugin commands."""

    def __init__(self) -> None:
        self.sources: dict[str, Callable] = {}
        self.transforms: dict[str, Callable] = {}
        self.sinks: dict[str, Callable] = {}

    def add_source(self, name: str, fn: Callable[..., Generator[Any, None, None]]) -> None:
        """Register a source command."""
        self.sources[name] = fn

    def add_transform(self, name: str, fn: Callable[..., Generator[Any, None, None]]) -> None:
        """Register a transform command."""
        self.transforms[name] = fn

    def add_sink(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a sink command."""
        self.sinks[name] = fn
