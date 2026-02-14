"""Transform commands for pipelines."""
import csv
import json
from collections.abc import Generator
from io import StringIO
from typing import Any


def cmd_parse(upstream: Generator[Any, None, None], format: str) -> Generator[Any, None, None]:
    """Parse input data according to format."""
    for item in upstream:
        if format == "json":
            yield json.loads(item)
        elif format == "csv":
            reader = csv.DictReader(StringIO(item))
            yield from reader


def cmd_get(upstream: Generator[Any, None, None], path: str) -> Generator[Any, None, None]:
    """Extract nested field by dot-path."""
    for item in upstream:
        value = item
        for key in path.split('.'):
            value = value[key]
        yield value


def cmd_filter(upstream: Generator[Any, None, None], field: str, value: str) -> Generator[Any, None, None]:
    """Filter items where field equals value."""
    for item in upstream:
        if str(item.get(field)) == str(value):
            yield item


def cmd_take(upstream: Generator[Any, None, None], n: int) -> Generator[Any, None, None]:
    """Take first n items."""
    count = 0
    for item in upstream:
        if count >= n:
            break
        yield item
        count += 1
