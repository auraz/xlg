"""Pipeline execution engine."""

from collections.abc import Callable, Generator
from typing import Any

Source = Callable[[], Generator[Any, None, None]]
Transform = Callable[[Generator[Any, None, None]], Generator[Any, None, None]]
Stage = Source | Transform


def run_pipeline(stages: list[Stage]) -> Generator[Any, None, None]:
    """Chain and execute pipeline stages."""
    if not stages:
        return
    stream = stages[0]()
    for stage in stages[1:]:
        stream = stage(stream)
    yield from stream
