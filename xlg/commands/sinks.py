"""Sink commands that consume pipelines."""
from collections.abc import Generator
from typing import Any


def cmd_print(upstream: Generator[Any, None, None]) -> list[Any]:
    """Print each item and return collected results."""
    results = []
    for item in upstream:
        print(item)
        results.append(item)
    return results
