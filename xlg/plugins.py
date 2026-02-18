"""Plugin system for XLG custom commands."""

import importlib.util
from collections.abc import Generator
from pathlib import Path
from typing import Any, Callable


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


def load_plugins(registry: Registry, plugin_dir: Path) -> None:
    """Load all plugins from directory."""
    if not plugin_dir.exists():
        return
    for plugin_path in plugin_dir.glob("*.py"):
        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(registry)
